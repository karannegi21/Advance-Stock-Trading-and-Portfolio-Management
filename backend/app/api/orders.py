"""Orders API router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_async_db
from app.models.stock import Stock
from app.models.trading import Order
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut
from app.services.order_engine import cancel_order, list_orders, place_order

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    stock_res = await db.execute(select(Stock).where(Stock.symbol == payload.symbol.strip().upper()))
    stock = stock_res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    order = await place_order(
        db,
        user_id=current_user.id,
        stock=stock,
        side=payload.side,
        order_type=payload.type,
        quantity=payload.quantity,
        limit_price=payload.limit_price,
    )
    # attach symbol
    order.stock = stock
    out = OrderOut.model_validate(order)
    out.symbol = stock.symbol
    return out


@router.get("", response_model=list[OrderOut])
async def get_orders(
    status_filter: str = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    orders = await list_orders(db, current_user.id, status_filter)
    out = []
    for o in orders:
        oo = OrderOut.model_validate(o)
        oo.symbol = o.stock.symbol if o.stock else None
        out.append(oo)
    return out


@router.delete("/{order_id}", response_model=OrderOut)
async def cancel_pending_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    order = await cancel_order(db, current_user.id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    oo = OrderOut.model_validate(order)
    if order.stock:
        oo.symbol = order.stock.symbol
    return oo
