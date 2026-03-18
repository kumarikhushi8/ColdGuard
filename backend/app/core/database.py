import asyncpg
from app.core.config import get_settings
from typing import AsyncGenerator
import asyncio
import logging

logger = logging.getLogger(__name__)
_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        settings = get_settings()
        for attempt in range(10):
            try:
                _pool = await asyncpg.create_pool(
                    settings.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                )
                logger.info("Database connected")
                return _pool
            except Exception as e:
                logger.warning(f"DB connect attempt {attempt+1}/10 failed: {e}")
                await asyncio.sleep(3)
        raise RuntimeError("Could not connect to database after 10 attempts")
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
