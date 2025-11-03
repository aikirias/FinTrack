from datetime import date
from decimal import Decimal

from app.schemas.exchange_rate import ExchangeRateValues
from app.services import exchange_rates


def test_ensure_daily_exchange_rate_uses_cached_value(db_session, monkeypatch):
    call_count = {"count": 0}

    def fake_fetch():
        call_count["count"] += 1
        values = ExchangeRateValues(
            usd_ars_oficial=Decimal("900"),
            usd_ars_blue=Decimal("950"),
            btc_usd=Decimal("40000"),
            btc_ars=Decimal("36000000"),
        )
        return values, {"mock": True}

    monkeypatch.setattr(exchange_rates, "fetch_remote_rates", fake_fetch)

    rate = exchange_rates.ensure_daily_exchange_rate(db_session)
    assert rate.usd_ars_oficial == Decimal("900")
    assert call_count["count"] == 1

    # Running again on the same day should not trigger an API call
    rate_again = exchange_rates.ensure_daily_exchange_rate(db_session)
    assert rate_again.id == rate.id
    assert call_count["count"] == 1
