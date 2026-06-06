"""Section 13: Product Intelligence."""

from __future__ import annotations

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120))


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[UUIDPk]
    product_id = fk("products.id")
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)


class ProductMetric(Base):
    __tablename__ = "product_metrics"

    id: Mapped[UUIDPk]
    product_id = fk("products.id")
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float | None] = mapped_column(Numeric(18, 2))


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id: Mapped[UUIDPk]
    product_id = fk("products.id")
    forecast_data: Mapped[dict] = mapped_column(JSONB, default=dict)
