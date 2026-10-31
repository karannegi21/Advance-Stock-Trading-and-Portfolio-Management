"""Portfolio API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_async_db
from app.models.user import User
from app.schemas.portfolio import PortfolioOut, PortfolioSnapshotOut
from app.services.portfolio_service import get_history, get_portfolio, save_snapshot

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioOut)
async def portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    data = await get_portfolio(db, current_user.id)
    return PortfolioOut(
        cash_balance=data["cash_balance"],
        invested_value=data["invested_value"],
        total_value=data["total_value"],
        total_pnl=data["total_pnl"],
        total_pnl_pct=data["total_pnl_pct"],
        holdings=data["holdings"],
    )


@router.get("/history", response_model=list[PortfolioSnapshotOut])
async def portfolio_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    snaps = await get_history(db, current_user.id)
    return [PortfolioSnapshotOut.model_validate(s) for s in snaps]


@router.post("/snapshot", response_model=PortfolioSnapshotOut)
async def create_snapshot(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    snap = await save_snapshot(db, current_user.id)
    return PortfolioSnapshotOut.model_validate(snap)
