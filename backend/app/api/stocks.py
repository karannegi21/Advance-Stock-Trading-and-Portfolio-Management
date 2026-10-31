"""Stocks API router."""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.simulator import SimState
from app.models.stock import PriceBar, Stock
from app.schemas.stock import PriceBarOut, StockDetailOut, StockHistoryOut, StockOut

router = APIRouter(prefix="/stocks", tags=["Stocks"])


async def get_current_sim_date(db: AsyncSession) -> Optional[date]:
    """Retrieve current simulator date or fallback to maximum trade date."""
    sim_res = await db.execute(select(SimState.current_sim_date).where(SimState.id == 1))
    sim_date = sim_res.scalar_one_or_none()
    if not sim_date:
        max_date_res = await db.execute(select(func.max(PriceBar.trade_date)))
        sim_date = max_date_res.scalar_one_or_none()
    return sim_date


@router.get("", response_model=List[StockOut])
async def list_stocks(
    q: Optional[str] = Query(None, description="Search symbol or company name"),
    sector: Optional[str] = Query(None, description="Filter by sector/industry"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """List stocks with optional search, sector filter, and pagination."""
    query = select(Stock).where(Stock.is_active == True)  # noqa: E712

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.where(
            (Stock.symbol.ilike(search_pattern)) | (Stock.name.ilike(search_pattern))
        )

    if sector:
        query = query.where(Stock.sector.ilike(f"%{sector.strip()}%"))

    query = query.order_by(Stock.symbol).offset(skip).limit(limit)
    result = await db.execute(query)
    stocks = result.scalars().all()

    sim_date = await get_current_sim_date(db)

    # Attach current price if sim_date is available
    out: List[StockOut] = []
    for stock in stocks:
        stock_out = StockOut.model_validate(stock)
        if sim_date:
            bar_query = (
                select(PriceBar.close)
                .where(PriceBar.stock_id == stock.id, PriceBar.trade_date <= sim_date)
                .order_by(desc(PriceBar.trade_date))
                .limit(1)
            )
            bar_res = await db.execute(bar_query)
            current_close = bar_res.scalar_one_or_none()
            if current_close is not None:
                stock_out.current_price = current_close
        out.append(stock_out)

    return out


@router.get("/{symbol}", response_model=StockDetailOut)
async def get_stock_detail(
    symbol: str,
    db: AsyncSession = Depends(get_async_db),
):
    """Get stock details, current price, and day change."""
    sym = symbol.strip().upper()
    stock_res = await db.execute(select(Stock).where(Stock.symbol == sym))
    stock = stock_res.scalar_one_or_none()

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{sym}' not found",
        )

    sim_date = await get_current_sim_date(db)
    detail = StockDetailOut.model_validate(stock)

    if sim_date:
        # Fetch the latest 2 bars up to sim_date to compute price and day change %
        bars_query = (
            select(PriceBar)
            .where(PriceBar.stock_id == stock.id, PriceBar.trade_date <= sim_date)
            .order_by(desc(PriceBar.trade_date))
            .limit(2)
        )
        bars_res = await db.execute(bars_query)
        bars = bars_res.scalars().all()

        if bars:
            latest = bars[0]
            detail.current_price = latest.close
            detail.day_open = latest.open
            detail.day_high = latest.high
            detail.day_low = latest.low
            detail.volume = latest.volume
            detail.as_of_date = latest.trade_date

            if len(bars) > 1:
                prev = bars[1]
                detail.previous_close = prev.close
                if prev.close and prev.close > 0:
                    pct = ((latest.close - prev.close) / prev.close) * Decimal("100")
                    detail.change_pct = round(pct, 2)
            else:
                detail.previous_close = latest.open
                if latest.open and latest.open > 0:
                    pct = ((latest.close - latest.open) / latest.open) * Decimal("100")
                    detail.change_pct = round(pct, 2)

    return detail


@router.get("/{symbol}/history", response_model=StockHistoryOut)
async def get_stock_history(
    symbol: str,
    range: str = Query("ALL", description="Date range: 1M, 6M, 1Y, or ALL"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get historical OHLCV bars for a stock up to the current sim date."""
    sym = symbol.strip().upper()
    stock_res = await db.execute(select(Stock).where(Stock.symbol == sym))
    stock = stock_res.scalar_one_or_none()

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{sym}' not found",
        )

    sim_date = await get_current_sim_date(db)
    if not sim_date:
        return StockHistoryOut(symbol=sym, count=0, bars=[])

    query = (
        select(PriceBar)
        .where(PriceBar.stock_id == stock.id, PriceBar.trade_date <= sim_date)
    )

    range_upper = range.strip().upper()
    if range_upper == "1M":
        start_date = sim_date - timedelta(days=30)
        query = query.where(PriceBar.trade_date >= start_date)
    elif range_upper == "6M":
        start_date = sim_date - timedelta(days=180)
        query = query.where(PriceBar.trade_date >= start_date)
    elif range_upper == "1Y":
        start_date = sim_date - timedelta(days=365)
        query = query.where(PriceBar.trade_date >= start_date)

    query = query.order_by(PriceBar.trade_date.asc())
    bars_res = await db.execute(query)
    bars = bars_res.scalars().all()

    return StockHistoryOut(
        symbol=sym,
        count=len(bars),
        bars=[PriceBarOut.model_validate(b) for b in bars],
    )

