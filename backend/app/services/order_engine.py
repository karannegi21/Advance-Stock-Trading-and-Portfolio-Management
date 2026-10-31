"""Order execution engine."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.simulator import SimState
from app.models.stock import PriceBar, Stock
from app.models.trading import Holding, Order, Transaction
from app.models.user import Account

FEE_RATE = Decimal("0.001")

async def get_current_sim_date(db: AsyncSession):
    sim_res = await db.execute(select(SimState.current_sim_date).where(SimState.id == 1))
    sim_date = sim_res.scalar_one_or_none()
    if not sim_date:
        max_date_res = await db.execute(select(func.max(PriceBar.trade_date)))
        sim_date = max_date_res.scalar_one_or_none()
    return sim_date

async def get_current_price(db: AsyncSession, stock_id: int):
    sim_date = await get_current_sim_date(db)
    if not sim_date:
        return None
    q = (
        select(PriceBar.close)
        .where(PriceBar.stock_id == stock_id, PriceBar.trade_date <= sim_date)
        .order_by(PriceBar.trade_date.desc())
        .limit(1)
    )
    res = await db.execute(q)
    return res.scalar_one_or_none()

async def _get_account(db: AsyncSession, user_id: int) -> Account:
    res = await db.execute(select(Account).where(Account.user_id == user_id))
    account = res.scalar_one_or_none()
    if account is None:
        raise ValueError("Account not found")
    return account

async def _get_holding(db: AsyncSession, user_id: int, stock_id: int):
    res = await db.execute(
        select(Holding).where(Holding.user_id == user_id, Holding.stock_id == stock_id)
    )
    return res.scalar_one_or_none()



async def _fill_order(db: AsyncSession, order: Order, price: Decimal) -> Order:
    account = await _get_account(db, order.user_id)
    side = order.side.upper()
    qty = order.quantity
    trade_value = price * qty
    fee = (trade_value * FEE_RATE).quantize(Decimal("0.0001"))

    if side == "BUY":
        total_cost = trade_value + fee
        if account.cash_balance < total_cost:
            order.status = "REJECTED"
            order.reject_reason = "Insufficient funds"
            return order
        account.cash_balance = account.cash_balance - total_cost
        holding = await _get_holding(db, order.user_id, order.stock_id)
        if holding is None:
            holding = Holding(
                user_id=order.user_id,
                stock_id=order.stock_id,
                quantity=qty,
                avg_cost=price,
            )
            db.add(holding)
        else:
            new_qty = holding.quantity + qty
            if new_qty > 0:
                new_avg = (holding.avg_cost * holding.quantity + price * qty) / new_qty
                holding.avg_cost = new_avg.quantize(Decimal("0.0001"))
            holding.quantity = new_qty
    else:
        holding = await _get_holding(db, order.user_id, order.stock_id)
        if holding is None or holding.quantity < qty:
            order.status = "REJECTED"
            order.reject_reason = "Insufficient shares"
            return order
        proceeds = trade_value - fee
        account.cash_balance = account.cash_balance + proceeds
        holding.quantity = holding.quantity - qty
        if holding.quantity <= 0:
            await db.delete(holding)

    txn = Transaction(
        user_id=order.user_id,
        order_id=order.id,
        stock_id=order.stock_id,
        side=side,
        quantity=qty,
        price=price,
        fees=fee,
    )
    db.add(txn)

    order.status = "FILLED"
    order.filled_price = price
    order.filled_at = datetime.now(timezone.utc)
    return order



async def place_order(db: AsyncSession, user_id: int, stock: Stock, side: str, order_type: str, quantity: int, limit_price=None) -> Order:
    side = side.upper()
    order_type = order_type.upper()
    if side not in ("BUY", "SELL"):
        raise ValueError("side must be BUY or SELL")
    if order_type not in ("MARKET", "LIMIT", "STOP"):
        raise ValueError("type must be MARKET, LIMIT, or STOP")
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    order = Order(
        user_id=user_id,
        stock_id=stock.id,
        side=side,
        type=order_type,
        quantity=quantity,
        limit_price=limit_price,
        status="PENDING",
    )
    db.add(order)
    await db.flush()

    if order_type == "MARKET":
        price = await get_current_price(db, stock.id)
        if price is None:
            order.status = "REJECTED"
            order.reject_reason = "No price available"
            await db.commit()
            await db.refresh(order)
            return order
        await _fill_order(db, order, price)

    await db.commit()
    await db.refresh(order)
    return order

async def cancel_order(db: AsyncSession, user_id: int, order_id: int):
    res = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    order = res.scalar_one_or_none()
    if order is None:
        return None
    if order.status != "PENDING":
        return order
    order.status = "CANCELLED"
    await db.commit()
    await db.refresh(order)


async def process_pending_limit_orders(db: AsyncSession) -> int:
    filled_count = 0
    res = await db.execute(
        select(Order).where(Order.status == "PENDING", Order.type == "LIMIT")
    )
    orders = res.scalars().all()
    for order in orders:
        price = await get_current_price(db, order.stock_id)
        if price is None:
            continue
        should_fill = False
        if order.side.upper() == "BUY" and order.limit_price is not None:
            if price <= order.limit_price:
                should_fill = True
        elif order.side.upper() == "SELL" and order.limit_price is not None:
            if price >= order.limit_price:
                should_fill = True
        if should_fill:
            await _fill_order(db, order, price)
            if order.status == "FILLED":
                filled_count += 1
            await db.commit()
    return filled_count

async def list_orders(db: AsyncSession, user_id: int, status_filter=None):
    q = select(Order).where(Order.user_id == user_id).options(selectinload(Order.stock))
    if status_filter:
        q = q.where(Order.status == status_filter.upper())
    q = q.order_by(Order.created_at.desc())
    res = await db.execute(q)
    return res.scalars().all()

    return order
