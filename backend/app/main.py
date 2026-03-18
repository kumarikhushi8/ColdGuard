import asyncio
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import get_pool, close_pool

from app.api import (
    facilities, sensors, readings, alerts,
    dashboard, notifications, mandi, auth, users, analytics
)

logger = logging.getLogger(__name__)
_bg_tasks = set()


async def _init_database(pool):
    """Initialize database tables if they don't exist (first-time Render deploy)."""
    async with pool.acquire() as conn:
        # Check if tables exist
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'facilities'
            )
        """)
        if not exists:
            # Try Render-compatible schema first, fallback to Docker schema
            for sql_path in [
                os.path.join(os.path.dirname(__file__), '..', 'infra', 'init_render.sql'),
                '/app/infra/init_render.sql',
                os.path.join(os.path.dirname(__file__), '..', 'infra', 'init.sql'),
                '/app/infra/init.sql',
            ]:
                if os.path.exists(sql_path):
                    with open(sql_path) as f:
                        sql = f.read()
                    await conn.execute(sql)
                    logger.info(f"[DB Init] Initialized database from {sql_path}")
                    break
            else:
                logger.error("[DB Init] No init SQL file found!")


async def _run_migrations(pool):
    """Run expansion migration if needed."""
    async with pool.acquire() as conn:
        for migration_path in [
            '/app/infra/expand_facilities.sql',
            os.path.join(os.path.dirname(__file__), '..', 'infra', 'expand_facilities.sql'),
        ]:
            if os.path.exists(migration_path):
                count = await conn.fetchval("SELECT COUNT(*) FROM facilities")
                if count <= 3:
                    with open(migration_path) as f:
                        sql = f.read()
                    await conn.execute(sql)
                    new_count = await conn.fetchval("SELECT COUNT(*) FROM facilities")
                    logger.info(f"[Migration] Expanded to {new_count} facilities across India")
                break

        # Seed mandi prices
        count = await conn.fetchval("SELECT COUNT(*) FROM mandi_prices")
        if count == 0:
            from app.api.mandi import seed_demo_prices
            await seed_demo_prices(conn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await get_pool()

    from app.services.notification_service import print_setup_guide
    print_setup_guide()

    # Initialize DB tables (for Render / first-time deploy)
    await _init_database(pool)

    # Run migrations
    await _run_migrations(pool)

    # Start mandi price fetcher
    from app.services.mandi_service import run_price_fetcher
    task = asyncio.create_task(run_price_fetcher(pool))
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)

    # Start simulator as background task (for Render — no separate container)
    settings = get_settings()
    if settings.run_simulator:
        from app.services.simulator import run_simulator
        sim_task = asyncio.create_task(run_simulator())
        _bg_tasks.add(sim_task)
        sim_task.add_done_callback(_bg_tasks.discard)
        logger.info("[Simulator] Started as background task")

    yield
    await close_pool()

settings = get_settings()
app = FastAPI(title="ColdGuard API", version="1.0.0", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/api/auth",          tags=["Auth"])
app.include_router(users.router,         prefix="/api/users",         tags=["Users"])
app.include_router(facilities.router,    prefix="/api/facilities",    tags=["Facilities"])
app.include_router(sensors.router,       prefix="/api/sensors",       tags=["Sensors"])
app.include_router(readings.router,      prefix="/api/readings",      tags=["Readings"])
app.include_router(alerts.router,        prefix="/api/alerts",        tags=["Alerts"])
app.include_router(dashboard.router,     prefix="/api/dashboard",     tags=["Dashboard"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(mandi.router,         prefix="/api/mandi",         tags=["Mandi"])
app.include_router(analytics.router,     prefix="/api/analytics",     tags=["Analytics"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ColdGuard API"}
