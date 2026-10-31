"""Analytics calculations for portfolio performance."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portfolio import PortfolioSnapshot
from app.models.stock import Stock
from app.models.trading import Holding
from app.models.user import Account, User
from app.services.portfolio_service import get_portfolio


async def _snapshots(db: AsyncSession, user_id: int) -> List[PortfolioSnapshot]:
    res = await db.execute(
        select(PortfolioSnapshot).where(PortfolioSnapshot.user_id == user_id).order_by(PortfolioSnapshot.snap_date.asc())
    )
    return res.scalars().all()


async def equity_curve(db: AsyncSession, user_id: int) -> List[dict]:
    snaps = await _snapshots(db, user_id)
    return [{"date": s.snap_date.isoformat(), "total_value": s.total_value} for s in snaps]


async def compute_analytics(db: AsyncSession, user_id: int) -> dict:
    account_res = await db.execute(select(Account).where(Account.user_id == user_id))
    account = account_res.scalar_one_or_none()
    initial = account.initial_balance if account else Decimal("1000000")

    portfolio = await get_portfolio(db, user_id)
    current_value = portfolio["total_value"]

    total_return_pct = Decimal("0")
    if initial != 0:
        total_return_pct = ((current_value - initial) / initial * Decimal("100")).quantize(Decimal("0.01"))

    snaps = await _snapshots(db, user_id)

    # annualized return (CAGR)
    annualized = Decimal("0")
    if len(snaps) >= 2:
        start_val = snaps[0].total_value
        end_val = snaps[-1].total_value
        days = (snaps[-1].snap_date - snaps[0].snap_date).days
        if days > 0 and start_val > 0:
            ratio = float(end_val / start_val)
            annualized = Decimal(str((ratio ** (365.0 / days) - 1) * 100)).quantize(Decimal("0.01"))

    # sharpe ratio from daily returns of snapshots
    sharpe = Decimal("0")
    if len(snaps) >= 3:
        returns = []
        for i in range(1, len(snaps)):
            prev = float(snaps[i - 1].total_value)
            cur = float(snaps[i].total_value)
            if prev != 0:
                returns.append((cur - prev) / prev)
        if returns:
            import statistics
            mean_r = statistics.fmean(returns)
            std_r = statistics.pstdev(returns) if len(returns) > 1 else 0
            if std_r and std_r > 0:
                sharpe = Decimal(str(mean_r / std_r * (252 ** 0.5))).quantize(Decimal("0.01"))

    # max drawdown from equity curve (snapshots + current)
    values = [float(s.total_value) for s in snaps]
    if not values:
        values = [float(current_value)]
    max_dd = 0.0
    peak = values[0] if values else 0.0
    for v in values:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak * 100
            if dd > max_dd:
                max_dd = dd
    max_drawdown_pct = Decimal(str(max_dd)).quantize(Decimal("0.01"))

    # sector allocation
    holdings_res = await db.execute(
        select(Holding).options(selectinload(Holding.stock)).where(Holding.user_id == user_id)
    )
    holdings = holdings_res.scalars().all()
    sector_values = {}
    total_holdings_value = Decimal("0")
    for h in holdings:
        price = h.avg_cost
        # use current price from portfolio if possible
        mv = h.avg_cost * h.quantity
        sector = h.stock.sector if h.stock else "Unknown"
        sector_values[sector] = sector_values.get(sector, Decimal("0")) + mv
        total_holdings_value += mv

    # refine with current prices
    from app.services.order_engine import get_current_price

    sector_values = {}
    total_holdings_value = Decimal("0")
    for h in holdings:
        price = await get_current_price(db, h.stock_id)
        if price is None:
            price = h.avg_cost
        mv = (price * h.quantity).quantize(Decimal("0.0001"))
        sector = h.stock.sector if h.stock else "Unknown"
        sector_values[sector] = sector_values.get(sector, Decimal("0")) + mv
        total_holdings_value += mv

    sector_allocation = []
    for sector, val in sector_values.items():
        pct = Decimal("0")
        if total_holdings_value != 0:
            pct = (val / total_holdings_value * Decimal("100")).quantize(Decimal("0.01"))
        sector_allocation.append({"sector": sector, "value": val, "percentage": pct})

    return {
        "total_return_pct": total_return_pct,
        "annualized_return_pct": annualized,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_drawdown_pct,
        "sector_allocation": sector_allocation,
        "current_value": current_value,
        "initial_balance": initial,
    }
