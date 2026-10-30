"""Trading models: Orders, Holdings, Transactions, Watchlist."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
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
    from app.models.user import User
    from app.models.stock import Stock


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # MARKET, LIMIT, STOP
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    stop_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False, index=True
    )  # PENDING, FILLED, CANCELLED, REJECTED
    filled_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    filled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    reject_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    stock: Mapped["Stock"] = relationship("Stock", back_populates="orders")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_orders_user_status", "user_id", "status"),
    )


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="holdings")
    stock: Mapped["Stock"] = relationship("Stock", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint("user_id", "stock_id", name="uq_user_stock_holding"),
        Index("ix_holdings_user_id", "user_id"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    order: Mapped[Optional["Order"]] = relationship("Order", back_populates="transactions")
    stock: Mapped["Stock"] = relationship("Stock", back_populates="transactions")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    stock_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlist_items")
    stock: Mapped["Stock"] = relationship("Stock", back_populates="watchlist_items")

    __table_args__ = (
        UniqueConstraint("user_id", "stock_id", name="uq_user_stock_watchlist"),
        Index("ix_watchlist_user_id", "user_id"),
    )
