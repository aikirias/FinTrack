from datetime import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.exchange_rates import ensure_daily_exchange_rate

scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)


def _rate_job() -> None:
    session = SessionLocal()
    try:
        ensure_daily_exchange_rate(session)
    finally:
        session.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        _rate_job,
        trigger="cron",
        hour=settings.rate_refresh_hour,
        minute=settings.rate_refresh_minute,
        id="daily_exchange_rate",
        replace_existing=True,
    )
    scheduler.start()
    # Run immediately on startup to ensure data exists
    _rate_job()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
