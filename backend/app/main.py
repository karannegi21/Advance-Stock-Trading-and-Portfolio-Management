"""FastAPI Application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    }
