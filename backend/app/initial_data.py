from __future__ import annotations

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.currency import Currency
from app.models.exchange_rate import ExchangeRateSource

DEFAULT_CURRENCIES = (
    {"code": "ARS", "name": "Peso Argentino", "symbol": "$"},
    {"code": "USD", "name": "Dólar estadounidense", "symbol": "USD"},
    {"code": "BTC", "name": "Bitcoin", "symbol": "₿"},
)

DEFAULT_SOURCES = (
    {"name": "DolarAPI", "base_url": str(settings.dolar_api_url)},
    {"name": "Coingecko", "base_url": str(settings.coingecko_api_url)},
)


def init_default_data() -> None:
    session = SessionLocal()
    try:
        for item in DEFAULT_CURRENCIES:
            exists = session.execute(select(Currency).where(Currency.code == item["code"])).scalar_one_or_none()
            if not exists:
                session.add(Currency(**item))

        for source in DEFAULT_SOURCES:
            exists = (
                session.execute(select(ExchangeRateSource).where(ExchangeRateSource.name == source["name"]))
                .scalar_one_or_none()
            )
            if not exists:
                session.add(ExchangeRateSource(**source))

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    init_default_data()
