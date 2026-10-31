"""FastAPI Application entrypoint."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.orders import router as orders_router
from app.api.portfolio import router as portfolio_router
from app.api.stocks import router as stocks_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.simulator import SimState
from app.services.market_simulator import run_simulator
from app.ws.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-start simulator if configured
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res = await db.execute(select(SimState).where(SimState.id == 1))
        state = res.scalar_one_or_none()
        if state is not None and settings.SIMULATOR_AUTO_START:
            state.is_running = True
            await db.commit()

    task = asyncio.create_task(run_simulator())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Stock Platform API",
    description="Paper trading and portfolio management API with live market simulator.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(admin_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(stocks_router, prefix="/api/v1")


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Render and uptime monitoring."""
    return {
        "status": "healthy",
        "service": "stock-platform-backend",
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint redirecting information."""
    return {
        "message": "Stock Trading Platform API is operational.",
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
    }
