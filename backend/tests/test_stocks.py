"""Tests for Stocks endpoints and market data queries."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_list_stocks():
    """Verify listing stocks returns seeded NSE stocks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/stocks")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        symbols = [s["symbol"] for s in data]
        assert "RELIANCE" in symbols or "TCS" in symbols or "INFY" in symbols


@pytest.mark.asyncio
async def test_search_and_filter_stocks():
    """Verify search by query and sector filtering."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Search by symbol
        resp = await client.get("/api/v1/stocks?q=INFY")
        assert resp.status_code == 200
        data = resp.json()
        assert any(s["symbol"] == "INFY" for s in data)

        # Filter by sector
        resp_sector = await client.get("/api/v1/stocks?sector=FINANCIAL")
        assert resp_sector.status_code == 200
        sector_data = resp_sector.json()
        assert len(sector_data) > 0
        for s in sector_data:
            assert "FINANCIAL" in s["sector"].upper()


@pytest.mark.asyncio
async def test_stock_detail():
    """Verify stock detail endpoint returns valid price information."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/stocks/TCS")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "TCS"
        assert "name" in data
        assert "sector" in data
        assert data["current_price"] is not None


@pytest.mark.asyncio
async def test_stock_history():
    """Verify stock history endpoint returns chronological OHLCV bars."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/stocks/RELIANCE/history?range=1M")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "RELIANCE"
        assert "bars" in data
        assert data["count"] == len(data["bars"])
        if data["count"] > 0:
            first_bar = data["bars"][0]
            assert "open" in first_bar
            assert "high" in first_bar
            assert "low" in first_bar
            assert "close" in first_bar
            assert "volume" in first_bar


@pytest.mark.asyncio
async def test_stock_not_found():
    """Verify 404 for unknown stock symbol."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/stocks/NONEXISTENT_SYMBOL_XYZ")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Stock symbol 'NONEXISTENT_SYMBOL_XYZ' not found"

