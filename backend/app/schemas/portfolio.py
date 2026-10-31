"""Portfolio Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class HoldingOut(BaseModel):
    symbol: str
    name: str
    sector: str
    quantity: int
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal


class PortfolioOut(BaseModel):
    cash_balance: Decimal
    invested_value: Decimal
    total_value: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    holdings: List[HoldingOut]


class PortfolioSnapshotOut(BaseModel):
    snap_date: date
    total_value: Decimal
    cash: Decimal
    invested_value: Decimal
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
