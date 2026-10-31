"""Portfolio valuation and snapshot service."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portfolio import PortfolioSnapshot
from app.models.stock import PriceBar, Stock
from app.models.trading import Holding
from app.models.user import Account
from app.services.order_engine import get_current_sim_date, get_current_price


async def get_portfolio(db: AsyncSession, user_id: int) -> dict:
    account_res = await db.execute(select(Account).where(Account.user_id == user_id))
    account = account_res.scalar_one_or_none()
    cash = account.cash_balance if account else Decimal("0")

    holdings_res = await db.execute(
        select(Holding).options(selectinload(Holding.stock)).where(Holding.user_id == user_id)
    )
    holdings = holdings_res.scalars().all()

    holding_rows = []
    invested_value = Decimal("0")
    for h in holdings:
        price = await get_current_price(db, h.stock_id)
        if price is None:
            price = h.avg_cost
        market_value = (price * h.quantity).quantize(Decimal("0.0001"))
        cost_basis = (h.avg_cost * h.quantity).quantize(Decimal("0.0001"))
        unrealized_pnl = (market_value - cost_basis).quantize(Decimal("0.0001"))
        if cost_basis != 0:
            pnl_pct = ((unrealized_pnl / cost_basis) * Decimal("100")).quantize(Decimal("0.01"))
        else:
            pnl_pct = Decimal("0")
        invested_value += market_value
        holding_rows.append({
            "symbol": h.stock.symbol,
            "name": h.stock.name,
            "sector": h.stock.sector,
            "quantity": h.quantity,
            "avg_cost": h.avg_cost,
            "current_price": price,
            "market_value": market_value,
            "cost_basis": cost_basis,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": pnl_pct,
        })

    total_value = (cash + invested_value).quantize(Decimal("0.0001"))
    initial = account.initial_balance if account else Decimal("1000000")
    total_pnl = (total_value - initial).quantize(Decimal("0.0001"))
    if initial != 0:
        total_pnl_pct = ((total_pnl / initial) * Decimal("100")).quantize(Decimal("0.01"))
    else:
        total_pnl_pct = Decimal("0")

    return {
        "cash_balance": cash,
        "invested_value": invested_value,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "holdings": holding_rows,
    }

async def save_snapshot(db: AsyncSession, user_id: int) -> PortfolioSnapshot:
    portfolio = await get_portfolio(db, user_id)
    sim_date = await get_current_sim_date(db)
    snap_date = sim_date if sim_date else date.today()

    # upsert
    res = await db.execute(
        select(PortfolioSnapshot).where(
            PortfolioSnapshot.user_id == user_id, PortfolioSnapshot.snap_date == snap_date
        )
    )
    snap = res.scalar_one_or_none()
    if snap is None:
        snap = PortfolioSnapshot(
            user_id=user_id,
            snap_date=snap_date,
            total_value=portfolio["total_value"],
            cash=portfolio["cash_balance"],
            invested_value=portfolio["invested_value"],
        )
        db.add(snap)
    else:
        snap.total_value = portfolio["total_value"]
        snap.cash = portfolio["cash_balance"]
        snap.invested_value = portfolio["invested_value"]
    await db.commit()
    await db.refresh(snap)
    return snap

async def get_history(db: AsyncSession, user_id: int) -> list[PortfolioSnapshot]:
    res = await db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.user_id == user_id)
        .order_by(PortfolioSnapshot.snap_date.asc())
    )
    return res.scalars().all()
