"""Watchlist API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_async_db
from app.models.stock import Stock
from app.models.trading import WatchlistItem
from app.models.user import User

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("")
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    res = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id)
    )
    items = res.scalars().all()
    # load stocks
    out = []
    for item in items:
        stock_res = await db.execute(select(Stock).where(Stock.id == item.stock_id))
        stock = stock_res.scalar_one_or_none()
        out.append({"id": item.id, "symbol": stock.symbol if stock else None, "name": stock.name if stock else None, "added_at": item.created_at})
    return out


@router.post("/{symbol}", status_code=status.HTTP_201_CREATED)
async def add_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    stock_res = await db.execute(select(Stock).where(Stock.symbol == symbol.strip().upper()))
    stock = stock_res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    # check existing
    existing = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.stock_id == stock.id)
    )
    if existing.scalar_one_or_none():
        return {"message": "Already in watchlist"}
    item = WatchlistItem(user_id=current_user.id, stock_id=stock.id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "symbol": stock.symbol}


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    stock_res = await db.execute(select(Stock).where(Stock.symbol == symbol.strip().upper()))
    stock = stock_res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    res = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.stock_id == stock.id)
    )
    item = res.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.commit()
    return None
