"""Analytics API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_async_db
from app.models.user import User
from app.services.analytics_service import compute_analytics, equity_curve

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("")
async def analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    return await compute_analytics(db, current_user.id)


@router.get("/equity-curve")
async def analytics_equity_curve(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    curve = await equity_curve(db, current_user.id)
    return {"points": curve}
