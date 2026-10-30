"""Stock and PriceBar database models."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.trading import Holding, Order, Transaction, WatchlistItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), default="Unknown", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    price_bars: Mapped[List["PriceBar"]] = relationship(
        "PriceBar", back_populates="stock", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="stock"
    )
    holdings: Mapped[List["Holding"]] = relationship(
        "Holding", back_populates="stock"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="stock"
    )
    watchlist_items: Mapped[List["WatchlistItem"]] = relationship(
        "WatchlistItem", back_populates="stock"
    )


class PriceBar(Base):
    __tablename__ = "price_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="price_bars")

    __table_args__ = (
        UniqueConstraint("stock_id", "trade_date", name="uq_stock_trade_date"),
        Index("ix_price_bars_stock_date", "stock_id", "trade_date"),
    )
