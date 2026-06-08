"""Product Intelligence schemas — catalog, inventory, demand, grounded signals."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProductOut(BaseModel):
    """One product with its derived inventory + demand picture."""

    id: str
    product_name: str
    category: str | None
    sales_count: int
    revenue: float | None
    quantity: int
    reorder_level: int
    stock_status: str  # ok | low | out
    demand_trend: str | None  # up | down | flat


class ProductStats(BaseModel):
    total_products: int
    total_revenue: float
    low_stock_count: int
    top_product: str | None


class ProductSignal(BaseModel):
    """A grounded, explainable finding about the product line."""

    title: str
    finding: str
    severity: str  # info | warning | danger | success
    confidence_score: float
    data_sources: list[str]
    recommended_action: str | None = None


class ProductOverview(BaseModel):
    stats: ProductStats
    products: list[ProductOut]
    signals: list[ProductSignal]
    generated_at: datetime
