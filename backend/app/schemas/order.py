"""Order Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrderCreate(BaseModel):
    symbol: str
    side: str  # BUY / SELL
    type: str  # MARKET / LIMIT / STOP
    quantity: int
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None


class OrderOut(BaseModel):
    id: int
    user_id: int
    stock_id: int
    symbol: Optional[str] = None
    side: str
    type: str
    quantity: int
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: str
    filled_price: Optional[Decimal] = None
    filled_at: Optional[datetime] = None
    created_at: datetime
    reject_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
