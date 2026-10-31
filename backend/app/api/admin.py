"""Admin API router for simulator control."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_async_db
from app.models.simulator import SimState
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])

START_DATE = date(2015, 1, 1)
END_DATE = date(2021, 4, 30)


async def _get_state(db: AsyncSession) -> SimState:
    res = await db.execute(select(SimState).where(SimState.id == 1))
    state = res.scalar_one_or_none()
    if state is None:
        state = SimState(id=1, current_sim_date=START_DATE, is_running=False)
        db.add(state)
        await db.commit()
        await db.refresh(state)
    return state


@router.post("/simulator/start")
async def start_simulator(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_async_db),
):
    state = await _get_state(db)
    state.is_running = True
    await db.commit()
    return {"status": "running", "current_sim_date": state.current_sim_date}


@router.post("/simulator/pause")
async def pause_simulator(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_async_db),
):
    state = await _get_state(db)
    state.is_running = False
    await db.commit()
    return {"status": "paused", "current_sim_date": state.current_sim_date}


@router.post("/simulator/reset")
async def reset_simulator(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_async_db),
):
    state = await _get_state(db)
    state.current_sim_date = START_DATE
    state.is_running = False
    await db.commit()
    return {"status": "reset", "current_sim_date": state.current_sim_date}


@router.get("/simulator/status")
async def simulator_status(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_async_db),
):
    state = await _get_state(db)
    return {
        "current_sim_date": state.current_sim_date,
        "is_running": state.is_running,
        "speed_seconds_per_day": state.speed_seconds_per_day,
    }
