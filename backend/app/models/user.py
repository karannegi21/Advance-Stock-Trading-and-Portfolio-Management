"""User and Account database models."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.trading import Holding, Order, Transaction, WatchlistItem
    from app.models.portfolio import PortfolioSnapshot


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)  # 'user' or 'admin'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    account: Mapped[Optional["Account"]] = relationship(
        "Account", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    holdings: Mapped[List["Holding"]] = relationship(
        "Holding", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    watchlist_items: Mapped[List["WatchlistItem"]] = relationship(
        "WatchlistItem", back_populates="user", cascade="all, delete-orphan"
    )
    snapshots: Mapped[List["PortfolioSnapshot"]] = relationship(
        "PortfolioSnapshot", back_populates="user", cascade="all, delete-orphan"
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    cash_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("1000000.0000"), nullable=False
    )
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("1000000.0000"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="account")
