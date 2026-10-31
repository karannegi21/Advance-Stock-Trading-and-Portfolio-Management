"""FastAPI Application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.orders import router as orders_router
from app.api.portfolio import router as portfolio_router
from app.api.stocks import router as stocks_router
from app.core.config import settings

app = FastAPI(
    title="Stock Platform API",
    description="Paper trading and portfolio management API with live market simulator.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(auth_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(stocks_router, prefix="/api/v1")


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
