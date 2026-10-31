"""Pytest fixtures for backend tests."""

import pytest

from app.core.database import async_engine, sync_engine


@pytest.fixture(autouse=True)
def _dispose_engines():
    yield
    try:
        async_engine.sync_engine.dispose()
    except Exception:
        pass
    try:
        sync_engine.dispose()
    except Exception:
        pass
