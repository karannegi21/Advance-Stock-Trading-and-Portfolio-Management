"""Portfolio Snapshot database model."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    snap_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    cash: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    invested_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="snapshots")

    __table_args__ = (
        UniqueConstraint("user_id", "snap_date", name="uq_user_snap_date"),
        Index("ix_snapshots_user_date", "user_id", "snap_date"),
    )
