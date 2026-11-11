"""Data ingestion service.

Turns an uploaded business file into structured data the platform can reason
over. Two stages:

1. **Parse** (on upload): detect the file kind, extract a tabular preview
   (CSV/Excel, or the first table inside a PDF/Word doc) or plain text, and
   auto-suggest a column mapping. Nothing touches business entities yet.
2. **Commit** (explicit): the user confirms/edits the mapping, and each row is
   turned into KPIs, customers, or products — after which the recommendation
   engine refreshes so the new data immediately drives insights.

Parsing is deterministic and fully offline (no LLM). Heavy format libraries are
imported lazily so a missing dependency degrades to a clear per-file error
instead of breaking app startup.
"""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import KPI
from app.models.customers import Customer, CustomerHealth
from app.models.products import Inventory, Product, ProductMetric
from app.models.recommendations import LearningEvent
from app.models.uploads import DataUpload
from app.schemas.upload import AnalysisChanges, CommitMapping, CommitResult
from app.services import audit, recommendation_engine

# Raw files are stored outside the package tree (gitignored: backend/var/).
_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "var" / "uploads"
_PREVIEW_LIMIT = 20
_TEXT_LIMIT = 20_000

_EXT_KIND = {
    "csv": "csv", "tsv": "csv", "txt": "csv",
    "xlsx": "excel", "xlsm": "excel", "xls": "excel",
    "pdf": "pdf",
    "docx": "word", "doc": "word",
    "png": "image", "jpg": "image", "jpeg": "image",
    "gif": "image", "bmp": "image", "webp": "image", "tiff": "image",
}


# --- Parse result ------------------------------------------------------------


@dataclass
class ParsedFile:
    kind: str
    status: str  # parsed | text_only | manual_required | failed
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    text: str | None = None
    error: str | None = None


def _detect_kind(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_KIND.get(ext, "unknown")


# --- Format parsers (lazy imports) -------------------------------------------


def _rows_from_table(table: list[list]) -> tuple[list[str], list[dict]]:
    """Turn a list-of-rows table (first row = header) into dict rows."""
    table = [r for r in table if r and any(_clean(c) != "" for c in r)]
    if not table:
        return [], []
    header = [_clean(h) or f"column_{i + 1}" for i, h in enumerate(table[0])]
    data: list[dict] = []
    for raw in table[1:]:
        cells = list(raw) + [None] * (len(header) - len(raw))
        data.append({header[i]: cells[i] for i in range(len(header))})
    return header, data


def _clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def _parse_csv(raw: bytes) -> ParsedFile:
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    columns, rows = _rows_from_table(list(reader))
    if not columns:
        return ParsedFile(kind="csv", status="failed", error="No readable rows found.")
    return ParsedFile(kind="csv", status="parsed", columns=columns, rows=rows)


def _parse_excel(raw: bytes) -> ParsedFile:
    try:
        from openpyxl import load_workbook
    except ImportError:
        return ParsedFile("excel", "failed", error="Excel support (openpyxl) not installed.")
    wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.active
    table = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    columns, rows = _rows_from_table(table)
    if not columns:
        return ParsedFile("excel", "failed", error="No readable rows in the worksheet.")
    return ParsedFile("excel", "parsed", columns=columns, rows=rows)


def _parse_pdf(raw: bytes) -> ParsedFile:
    try:
        import pdfplumber
    except ImportError:
        return ParsedFile("pdf", "failed", error="PDF support (pdfplumber) not installed.")
    table: list[list] | None = None
    texts: list[str] = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            if table is None:
                found = page.extract_table()
                if found:
                    table = found
            texts.append(page.extract_text() or "")
    text = "\n".join(texts).strip() or None
    if table:
        columns, rows = _rows_from_table(table)
        if columns:
            return ParsedFile("pdf", "parsed", columns=columns, rows=rows, text=text)
    return ParsedFile("pdf", "text_only", text=text)


def _parse_word(raw: bytes) -> ParsedFile:
    try:
        import docx
    except ImportError:
        return ParsedFile("word", "failed", error="Word support (python-docx) not installed.")
    document = docx.Document(io.BytesIO(raw))
    if document.tables:
        table = [[c.text for c in row.cells] for row in document.tables[0].rows]
        columns, rows = _rows_from_table(table)
        if columns:
            text = "\n".join(p.text for p in document.paragraphs).strip() or None
            return ParsedFile("word", "parsed", columns=columns, rows=rows, text=text)
    text = "\n".join(p.text for p in document.paragraphs).strip() or None
    return ParsedFile("word", "text_only", text=text)


def _parse(kind: str, raw: bytes) -> ParsedFile:
    if kind == "csv":
        return _parse_csv(raw)
    if kind == "excel":
        return _parse_excel(raw)
    if kind == "pdf":
        return _parse_pdf(raw)
    if kind == "word":
        return _parse_word(raw)
    if kind == "image":
        return ParsedFile(
            "image", "manual_required",
            error="Images can't be auto-parsed offline — enter the figures manually.",
        )
    return ParsedFile("unknown", "manual_required", error="Unsupported file type.")


# --- Mapping suggestion ------------------------------------------------------

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "date": ("date", "month", "period", "week", "day", "quarter", "year", "time"),
    "customer_name": ("customer", "client", "account", "company", "buyer"),
    "product_name": ("product", "item", "sku", "service", "model"),
    "category": ("category", "type", "segment", "class"),
    "segment": ("segment", "tier", "plan"),
    "revenue": ("revenue", "sales", "amount", "total", "income", "value", "price"),
    "sales_count": ("units", "quantity", "qty", "count", "orders", "volume"),
    "quantity": ("stock", "inventory", "on hand", "available"),
    "churn_risk": ("churn", "risk"),
    "health_score": ("health", "score", "nps", "satisfaction"),
}


def _match(columns: list[str], keys: tuple[str, ...]) -> str | None:
    for col in columns:
        low = col.lower()
        if any(k in low for k in keys):
            return col
    return None


def suggest_mapping(columns: list[str]) -> dict:
    """Best-effort guess of target entity + field→column map (transparent)."""
    if not columns:
        return {}
    product = _match(columns, _KEYWORDS["product_name"])
    customer = _match(columns, _KEYWORDS["customer_name"])
    revenue = _match(columns, _KEYWORDS["revenue"])
    date_col = _match(columns, _KEYWORDS["date"])

    if product:
        fields = {"product_name": product}
        for f in ("category", "revenue", "sales_count", "quantity"):
            col = _match(columns, _KEYWORDS[f])
            if col:
                fields[f] = col
        return {"target": "products", "fields": fields}

    if customer:
        fields = {"customer_name": customer}
        for f in ("segment", "churn_risk", "health_score"):
            col = _match(columns, _KEYWORDS[f])
            if col:
                fields[f] = col
        return {"target": "customers", "fields": fields}

    if revenue:
        fields = {"value": revenue}
        if date_col:
            fields["date"] = date_col
        return {"target": "kpi", "fields": fields, "kpi_label": revenue}

    return {}


# --- Persistence of the upload record ----------------------------------------


def ingest(
    db: DBSession,
    org_id: uuid.UUID,
    user_id: uuid.UUID | None,
    filename: str,
    content_type: str | None,
    raw: bytes,
) -> DataUpload:
    """Parse an uploaded file and persist a ``DataUpload`` (no entities yet)."""
    kind = _detect_kind(filename)
    parsed = _parse(kind, raw)

    upload = DataUpload(
        organization_id=org_id,
        uploaded_by=user_id,
        filename=filename[:255],
        content_type=(content_type or "")[:120] or None,
        file_kind=parsed.kind,
        size_bytes=len(raw),
        status=parsed.status,
        columns=parsed.columns,
        preview_rows=[_jsonable(r) for r in parsed.rows[:_PREVIEW_LIMIT]],
        row_count=len(parsed.rows),
        extracted_text=(parsed.text or None) and parsed.text[:_TEXT_LIMIT],
        suggested_mapping=suggest_mapping(parsed.columns),
        error=parsed.error,
    )
    db.add(upload)
    db.flush()

    # Persist the raw bytes so a commit can re-read the full file later.
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    path = _UPLOAD_DIR / f"{upload.id}.{ext}"
    path.write_bytes(raw)
    upload.storage_path = str(path)
    db.flush()
    return upload


def _jsonable(row: dict) -> dict:
    """Coerce cell values (dates, Decimals) to JSON-safe primitives for preview."""
    out: dict = {}
    for k, v in row.items():
        if isinstance(v, datetime | date):
            out[k] = v.isoformat()
        elif v is None or isinstance(v, str | int | float | bool):
            out[k] = v
        else:
            out[k] = str(v)
    return out


# --- Commit: rows -> entities ------------------------------------------------


def _reparse_rows(upload: DataUpload) -> list[dict]:
    if not upload.storage_path:
        return [dict(r) for r in upload.preview_rows]
    raw = Path(upload.storage_path).read_bytes()
    return _parse(upload.file_kind, raw).rows


def _to_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    s = str(value).strip()
    for ch in ("$", "€", "£", "₹", ",", "%"):
        s = s.replace(ch, "")
    s = s.strip()
    if s in {"", "-", "n/a", "na", "none"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


_DATE_FORMATS = (
    "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
    "%b %Y", "%B %Y", "%b-%Y", "%Y-%m", "%m/%Y", "%Y",
)


def _to_date(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    s = str(value).strip()
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def commit(
    db: DBSession, org_id: uuid.UUID, upload: DataUpload, mapping: CommitMapping
) -> CommitResult:
    """Map parsed rows into real entities, then refresh recommendations."""
    rows = _reparse_rows(upload)
    fields = mapping.fields

    if mapping.target == "kpi":
        created, skipped = _commit_kpi(db, org_id, rows, fields, mapping.kpi_label)
    elif mapping.target == "customers":
        created, skipped = _commit_customers(db, org_id, rows, fields)
    elif mapping.target == "products":
        created, skipped = _commit_products(db, org_id, rows, fields)
    else:  # pragma: no cover - guarded by schema Literal
        raise ValueError(f"Unknown target: {mapping.target}")

    db.flush()
    recs, change = recommendation_engine.refresh_with_changes(db, org_id)

    # Record how this fresh data moved the analysis so the shift is auditable
    # over time, not just visible in the moment.
    if change.changed:
        db.add(LearningEvent(
            organization_id=org_id,
            event_summary=f"{upload.filename}: {change.summary()}",
            learning_type="data_ingestion",
        ))

    # Leave an audit trail of who imported what data into which entities.
    audit.record(
        db,
        action="data.commit",
        user_id=upload.uploaded_by,
        organization_id=org_id,
        resource=upload.filename,
        detail=f"target={mapping.target}, created={created}, skipped={skipped}",
    )

    summary = {
        "target": mapping.target,
        "created": created,
        "skipped": skipped,
        "new_insights": change.new_insights,
        "resolved_insights": change.resolved_insights,
    }
    upload.status = "committed"
    upload.commit_summary = summary
    db.flush()

    return CommitResult(
        upload_id=upload.id,
        target=mapping.target,
        created=created,
        skipped=skipped,
        total=len(rows),
        recommendations_refreshed=len(recs),
        analysis_changes=AnalysisChanges(
            new_insights=change.new_insights,
            resolved_insights=change.resolved_insights,
            unchanged=change.unchanged,
        ),
    )


def _commit_kpi(db, org_id, rows, fields, kpi_label) -> tuple[dict, int]:
    value_col = fields.get("value")
    if not value_col:
        raise ValueError("KPI import requires a 'value' column mapping.")
    date_col = fields.get("date")
    name_col = fields.get("kpi_name")
    label = (kpi_label or value_col or "Metric")[:120]

    count = skipped = 0
    for row in rows:
        val = _to_number(row.get(value_col))
        if val is None:
            skipped += 1
            continue
        name = (str(row.get(name_col)).strip() if name_col and row.get(name_col) else label)
        kpi = KPI(organization_id=org_id, kpi_name=name[:120], value=val)
        when = _to_date(row.get(date_col)) if date_col else None
        if when:
            kpi.recorded_at = when
        db.add(kpi)
        count += 1
    return {"kpis": count}, skipped


def _commit_customers(db, org_id, rows, fields) -> tuple[dict, int]:
    name_col = fields.get("customer_name")
    if not name_col:
        raise ValueError("Customer import requires a 'customer_name' column mapping.")
    seg_col = fields.get("segment")
    churn_col = fields.get("churn_risk")
    health_col = fields.get("health_score")

    customers = health = skipped = 0
    for row in rows:
        name = str(row.get(name_col) or "").strip()
        if not name:
            skipped += 1
            continue
        customer = Customer(
            organization_id=org_id,
            customer_name=name[:255],
            segment=(str(row.get(seg_col)).strip()[:80] if seg_col and row.get(seg_col) else None),
        )
        db.add(customer)
        db.flush()
        churn = _to_number(row.get(churn_col)) if churn_col else None
        score = _to_number(row.get(health_col)) if health_col else None
        if churn is not None or score is not None:
            db.add(CustomerHealth(customer_id=customer.id, churn_risk=churn, health_score=score))
            health += 1
        customers += 1
    return {"customers": customers, "health_records": health}, skipped


def _commit_products(db, org_id, rows, fields) -> tuple[dict, int]:
    name_col = fields.get("product_name")
    if not name_col:
        raise ValueError("Product import requires a 'product_name' column mapping.")
    cat_col = fields.get("category")
    rev_col = fields.get("revenue")
    sales_col = fields.get("sales_count")
    qty_col = fields.get("quantity")

    products = metrics = inventory = skipped = 0
    for row in rows:
        name = str(row.get(name_col) or "").strip()
        if not name:
            skipped += 1
            continue
        category = str(row.get(cat_col)).strip()[:120] if cat_col and row.get(cat_col) else None
        product = Product(
            organization_id=org_id, product_name=name[:255], category=category
        )
        db.add(product)
        db.flush()
        rev = _to_number(row.get(rev_col)) if rev_col else None
        sales = _to_number(row.get(sales_col)) if sales_col else None
        if rev is not None or sales is not None:
            db.add(ProductMetric(
                product_id=product.id, sales_count=int(sales or 0), revenue=rev
            ))
            metrics += 1
        qty = _to_number(row.get(qty_col)) if qty_col else None
        if qty is not None:
            db.add(Inventory(product_id=product.id, quantity=int(qty)))
            inventory += 1
        products += 1
    return {"products": products, "metrics": metrics, "inventory": inventory}, skipped


def get_upload(db: DBSession, org_id: uuid.UUID, upload_id: uuid.UUID) -> DataUpload | None:
    return db.scalar(
        select(DataUpload).where(
            DataUpload.id == upload_id, DataUpload.organization_id == org_id
        )
    )
