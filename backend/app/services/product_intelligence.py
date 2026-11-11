"""Product Intelligence service.

Joins the catalog, inventory, sales metrics, and demand forecasts into an
executive view: per-product stock + demand, line-level stats, and grounded
signals (stockout risk, revenue concentration, demand shifts). Deterministic
so the page and tests agree; never generic advice.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.products import DemandForecast, Inventory, Product, ProductMetric
from app.schemas.products import (
    ProductOut,
    ProductOverview,
    ProductSignal,
    ProductStats,
)


def _stock_status(quantity: int, reorder_level: int) -> str:
    if quantity <= 0:
        return "out"
    if quantity <= reorder_level:
        return "low"
    return "ok"


def overview(db: DBSession, org_id: uuid.UUID) -> ProductOverview:
    products = list(
        db.scalars(select(Product).where(Product.organization_id == org_id)).all()
    )
    ids = [p.id for p in products]

    inv_by: dict[uuid.UUID, Inventory] = {}
    metric_by: dict[uuid.UUID, ProductMetric] = {}
    forecast_by: dict[uuid.UUID, dict] = {}
    if ids:
        for inv in db.scalars(select(Inventory).where(Inventory.product_id.in_(ids))).all():
            inv_by[inv.product_id] = inv
        for m in db.scalars(select(ProductMetric).where(ProductMetric.product_id.in_(ids))).all():
            metric_by[m.product_id] = m
        for f in db.scalars(
            select(DemandForecast).where(DemandForecast.product_id.in_(ids))
        ).all():
            forecast_by[f.product_id] = f.forecast_data or {}

    rows: list[ProductOut] = []
    total_revenue = 0.0
    for p in products:
        inv = inv_by.get(p.id)
        metric = metric_by.get(p.id)
        qty = inv.quantity if inv else 0
        reorder = inv.reorder_level if inv else 0
        revenue = float(metric.revenue) if metric and metric.revenue is not None else None
        if revenue:
            total_revenue += revenue
        trend = forecast_by.get(p.id, {}).get("trend")
        rows.append(
            ProductOut(
                id=str(p.id),
                product_name=p.product_name,
                category=p.category,
                sales_count=metric.sales_count if metric else 0,
                revenue=revenue,
                quantity=qty,
                reorder_level=reorder,
                stock_status=_stock_status(qty, reorder),
                demand_trend=trend,
            )
        )

    # Highest revenue first so the catalog leads with what drives the business.
    rows.sort(key=lambda r: -(r.revenue or 0))

    low_stock = [r for r in rows if r.stock_status in {"low", "out"}]
    top = rows[0] if rows and rows[0].revenue else None

    stats = ProductStats(
        total_products=len(products),
        total_revenue=round(total_revenue, 2),
        low_stock_count=len(low_stock),
        top_product=top.product_name if top else None,
    )

    return ProductOverview(
        stats=stats,
        products=rows,
        signals=_signals(rows, low_stock, top, total_revenue),
        generated_at=datetime.utcnow(),
    )


def _signals(
    rows: list[ProductOut],
    low_stock: list[ProductOut],
    top: ProductOut | None,
    total_revenue: float,
) -> list[ProductSignal]:
    out: list[ProductSignal] = []

    if not rows:
        return [
            ProductSignal(
                title="No product catalog yet",
                finding="Add products, inventory, and demand data to unlock stock and "
                "demand intelligence.",
                severity="info",
                confidence_score=55.0,
                data_sources=["products"],
            )
        ]

    if low_stock:
        names = ", ".join(r.product_name for r in low_stock[:3])
        out_of = [r for r in low_stock if r.stock_status == "out"]
        out.append(
            ProductSignal(
                title=f"{len(low_stock)} SKU(s) at/below reorder level",
                finding=f"{len(low_stock)} product(s) need restocking to avoid stockouts: "
                f"{names}." + (f" {len(out_of)} already out of stock." if out_of else ""),
                severity="danger" if out_of else "warning",
                confidence_score=76.0,
                data_sources=["inventory"],
                recommended_action="Raise purchase orders for the low-stock SKUs.",
            )
        )

    if top and top.revenue and total_revenue:
        share = top.revenue / total_revenue * 100
        out.append(
            ProductSignal(
                title=f"Top product: {top.product_name}",
                finding=f"'{top.product_name}' leads on revenue (${top.revenue:,.0f}, "
                f"{share:.0f}% of the line).",
                severity="warning" if share >= 50 else "success",
                confidence_score=72.0,
                data_sources=["product_metrics"],
                recommended_action="Diversify revenue — concentration is high."
                if share >= 50
                else None,
            )
        )

    rising = [r for r in rows if r.demand_trend == "up"]
    falling = [r for r in rows if r.demand_trend == "down"]
    if rising or falling:
        parts = []
        if rising:
            parts.append(f"demand rising for {', '.join(r.product_name for r in rising[:2])}")
        if falling:
            parts.append(f"falling for {', '.join(r.product_name for r in falling[:2])}")
        out.append(
            ProductSignal(
                title="Demand is shifting",
                finding="Forecasts show " + "; ".join(parts) + ".",
                severity="warning" if falling else "info",
                confidence_score=66.0,
                data_sources=["demand_forecasts"],
                recommended_action="Rebalance production toward rising demand."
                if rising and falling
                else None,
            )
        )

    if not out:
        out.append(
            ProductSignal(
                title=f"{len(rows)} product(s) tracked",
                finding=f"Catalog has {len(rows)} product(s); no stock or demand alerts.",
                severity="info",
                confidence_score=60.0,
                data_sources=["products"],
            )
        )
    return out
