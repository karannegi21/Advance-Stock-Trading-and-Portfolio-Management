"""Stock and PriceBar Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class StockBase(BaseModel):
    symbol: str
    name: str
    sector: str
    is_active: bool = True


class StockOut(StockBase):
    id: int
    created_at: datetime
    current_price: Optional[Decimal] = None
    change_pct: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class StockDetailOut(StockOut):
    previous_close: Optional[Decimal] = None
    day_open: Optional[Decimal] = None
    day_high: Optional[Decimal] = None
    day_low: Optional[Decimal] = None
    volume: Optional[int] = None
    as_of_date: Optional[date] = None


class PriceBarOut(BaseModel):
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    model_config = ConfigDict(from_attributes=True)


class StockHistoryOut(BaseModel):
    symbol: str
    count: int
    bars: List[PriceBarOut]

