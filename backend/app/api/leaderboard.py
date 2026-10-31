"""Leaderboard API router."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_async_db
from app.models.user import Account, User
from app.services.portfolio_service import get_portfolio

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("")
async def leaderboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    users_res = await db.execute(select(User))
    users = users_res.scalars().all()
    rows = []
    for u in users:
        portfolio = await get_portfolio(db, u.id)
        account_res = await db.execute(select(Account).where(Account.user_id == u.id))
        account = account_res.scalar_one_or_none()
        initial = account.initial_balance if account else 1000000
        total_value = portfolio["total_value"]
        return_pct = 0
        if initial:
            return_pct = float((total_value - initial) / initial * 100)
        rows.append({
            "user_id": u.id,
            "name": u.full_name,
            "total_value": total_value,
            "return_pct": round(return_pct, 2),
        })
    rows.sort(key=lambda x: x["return_pct"], reverse=True)
    return rows[:10]
