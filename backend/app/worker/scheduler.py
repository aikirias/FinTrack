import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.exchange_rates import ensure_daily_exchange_rate

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

_FREQUENCY_DELTA = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


def _advance_date(current: date, frequency: str) -> date:
    if frequency in _FREQUENCY_DELTA:
        return current + _FREQUENCY_DELTA[frequency]
    if frequency == "monthly":
        month = current.month + 1
        year = current.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(current.day, last_day))
    if frequency == "yearly":
        import calendar
        last_day = calendar.monthrange(current.year + 1, current.month)[1]
        return date(current.year + 1, current.month, min(current.day, last_day))
    return current + timedelta(days=1)


def _rate_job() -> None:
    session = SessionLocal()
    try:
        logger.info("Ejecutando job de actualización de cotizaciones")
        ensure_daily_exchange_rate(session)
        logger.info("Cotizaciones actualizadas correctamente")
    except Exception:
        logger.exception("Error al actualizar cotizaciones en el job programado")
    finally:
        session.close()


def _recurring_job() -> None:
    from app.crud import crud_recurring_transaction
    from app.crud import crud_transaction
    from app.schemas.transaction import TransactionCreate
    from app.services.exchange_rates import pick_rates
    from datetime import datetime, timezone

    session = SessionLocal()
    try:
        today = date.today()
        due = crud_recurring_transaction.get_due(session, today)
        if not due:
            return

        logger.info("Procesando %d transacciones recurrentes vencidas", len(due))
        for rt in due:
            try:
                _, rate_values = pick_rates(session, exchange_rate_id=None, manual_rates=None)
                tx_in = TransactionCreate(
                    transaction_date=datetime.now(tz=timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0),
                    account_id=rt.account_id,
                    currency_code=rt.currency_code,
                    amount_original=rt.amount_original,
                    category_id=rt.category_id,
                    subcategory_id=rt.subcategory_id,
                    notes=rt.notes,
                    rate_type=rt.rate_type,
                )
                from app.services.exchange_rates import ensure_daily_exchange_rate
                rate_obj = ensure_daily_exchange_rate(session)
                crud_transaction.create_transaction(
                    session,
                    user_id=rt.user_id,
                    tx_in=tx_in,
                    rates=rate_values,
                    exchange_rate_id=rate_obj.id,
                )
                rt.last_run_date = today
                rt.next_run_date = _advance_date(today, rt.frequency)
                session.add(rt)
                session.commit()
                logger.info("Transacción recurrente '%s' (id=%d) ejecutada", rt.name, rt.id)
            except Exception:
                session.rollback()
                logger.exception("Error procesando transacción recurrente id=%d", rt.id)
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
    scheduler.add_job(
        _recurring_job,
        trigger="cron",
        hour=6,
        minute=0,
        id="recurring_transactions",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler iniciado (cotizaciones %02d:%02d, recurrentes 06:00 %s)",
        settings.rate_refresh_hour,
        settings.rate_refresh_minute,
        settings.scheduler_timezone,
    )
    _rate_job()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
