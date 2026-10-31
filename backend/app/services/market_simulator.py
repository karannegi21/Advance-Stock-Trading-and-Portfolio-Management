"""Market simulator background task."""

import asyncio
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.simulator import SimState
from app.models.stock import PriceBar, Stock
from app.services.order_engine import process_pending_limit_orders
from app.ws.manager import manager

END_DATE = date(2021, 4, 30)
START_DATE = date(2015, 1, 1)


async def _fetch_prices(db: AsyncSession, sim_date: date) -> list[dict]:
    res = await db.execute(select(Stock).where(Stock.is_active == True))  # noqa: E712
    stocks = res.scalars().all()
    prices = []
    for s in stocks:
        q = (
            select(PriceBar.close)
            .where(PriceBar.stock_id == s.id, PriceBar.trade_date <= sim_date)
            .order_by(PriceBar.trade_date.desc())
            .limit(1)
        )
        r = await db.execute(q)
        close = r.scalar_one_or_none()
        prices.append({"symbol": s.symbol, "price": close})
    return prices


async def run_simulator():
    """Background loop advancing sim date and broadcasting prices."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                sim_res = await db.execute(select(SimState).where(SimState.id == 1))
                state = sim_res.scalar_one_or_none()
                if state is None:
                    await asyncio.sleep(settings.SIMULATOR_SPEED_SECONDS)
                    continue
                if not state.is_running:
                    await asyncio.sleep(1)
                    continue

                # advance date
                current = state.current_sim_date or START_DATE
                next_date = current + timedelta(days=1)
                if next_date > END_DATE:
                    next_date = START_DATE
                state.current_sim_date = next_date
                await db.commit()

                # process pending limit orders
                try:
                    await process_pending_limit_orders(db)
                except Exception:
                    pass

                # broadcast prices
                prices = await _fetch_prices(db, next_date)
                await manager.broadcast({
                    "type": "prices",
                    "sim_date": next_date.isoformat(),
                    "prices": prices,
                })
        except Exception:
            pass

        await asyncio.sleep(settings.SIMULATOR_SPEED_SECONDS)
