"""Market Simulator State model."""

from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SimState(Base):
    __tablename__ = "sim_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    current_sim_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    speed_seconds_per_day: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
