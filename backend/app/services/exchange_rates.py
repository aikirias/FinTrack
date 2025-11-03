from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import crud_exchange_rate
from app.db.session import SessionLocal
from app.models.exchange_rate import ExchangeRate
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateOverride, ExchangeRateValues


def _to_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def fetch_remote_rates() -> tuple[ExchangeRateValues, dict[str, Any]]:
    with httpx.Client(timeout=10.0) as client:
        dolar_response = client.get(str(settings.dolar_api_url))
        dolar_response.raise_for_status()
        dolar_payload = dolar_response.json()

        oficial_rate = None
        blue_rate = None
        for entry in dolar_payload:
            if entry.get("casa") == "oficial":
                oficial_rate = _to_decimal(entry.get("venta"))
            if entry.get("casa") == "blue":
                blue_rate = _to_decimal(entry.get("venta"))

        if oficial_rate is None:
            raise ValueError("No se pudo obtener la cotización oficial USD/ARS")

        coingecko_response = client.get(
            str(settings.coingecko_api_url),
            params={"ids": "bitcoin", "vs_currencies": "usd,ars"},
        )
        coingecko_response.raise_for_status()
        coingecko_payload = coingecko_response.json()
        bitcoin_data = coingecko_payload.get("bitcoin")
        if not bitcoin_data:
            raise ValueError("No se pudo obtener la cotización de BTC")

        btc_usd = _to_decimal(bitcoin_data.get("usd"))
        btc_ars = _to_decimal(bitcoin_data.get("ars"))

    values = ExchangeRateValues(
        usd_ars_oficial=oficial_rate,
        usd_ars_blue=blue_rate,
        btc_usd=btc_usd,
        btc_ars=btc_ars,
    )

    metadata = {
        "dolarapi": dolar_payload,
        "coingecko": coingecko_payload,
    }

    return values, metadata


def ensure_daily_exchange_rate(db_session: Session | None = None) -> ExchangeRate:
    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True

    try:
        today = date.today()
        existing = crud_exchange_rate.get_rate_by_date(db_session, today)
        if existing:
            return existing

        values, metadata = fetch_remote_rates()
        rate_in = ExchangeRateCreate(
            effective_date=today,
            usd_ars_oficial=values.usd_ars_oficial,
            usd_ars_blue=values.usd_ars_blue,
            btc_usd=values.btc_usd,
            btc_ars=values.btc_ars,
            metadata_payload=json.dumps(metadata, default=str),
        )
        created = crud_exchange_rate.create_exchange_rate(db_session, rate_in)
        return created
    finally:
        if close_session:
            db_session.close()


def pick_rates(
    db_session: Session,
    exchange_rate_id: int | None,
    manual_rates: ExchangeRateOverride | None,
    fallback_to_latest: bool = True,
) -> tuple[ExchangeRate | None, ExchangeRateValues]:
    if manual_rates is not None:
        return None, manual_rates

    exchange_rate: ExchangeRate | None = None
    if exchange_rate_id is not None:
        exchange_rate = crud_exchange_rate.get_exchange_rate(db_session, exchange_rate_id)

    if exchange_rate is None and fallback_to_latest:
        exchange_rate = crud_exchange_rate.get_latest_rate(db_session)
        if exchange_rate is None:
            exchange_rate = ensure_daily_exchange_rate(db_session)

    if exchange_rate is None:
        raise ValueError("No exchange rate available")

    return exchange_rate, ExchangeRateValues(
        usd_ars_oficial=exchange_rate.usd_ars_oficial,
        usd_ars_blue=exchange_rate.usd_ars_blue,
        btc_usd=exchange_rate.btc_usd,
        btc_ars=exchange_rate.btc_ars,
    )
