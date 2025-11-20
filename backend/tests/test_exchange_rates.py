from datetime import date
from decimal import Decimal
from http import HTTPStatus

from app.models.exchange_rate import ExchangeRate
from app.schemas.exchange_rate import ExchangeRateValues
from app.services import exchange_rates


def test_ensure_daily_exchange_rate_uses_cached_value(db_session, monkeypatch):
    db_session.query(ExchangeRate).delete()
    db_session.commit()

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


def register_user(client, email="rates@example.com"):
    payload = {"email": email, "password": "supersecure", "timezone": "UTC"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == HTTPStatus.CREATED


def create_manual_rate(client, *, effective_date: str, usd_ars: str) -> int:
    response = client.post(
        "/exchange-rates/override",
        json={
            "effective_date": effective_date,
            "usd_ars_oficial": usd_ars,
            "usd_ars_blue": usd_ars,
            "btc_usd": "50000",
            "btc_ars": "60000000",
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    return response.json()["id"]


def test_override_marks_manual_flag(client):
    register_user(client, email="manual@example.com")
    response = client.post(
        "/exchange-rates/override",
        json={
            "effective_date": "2024-02-01",
            "usd_ars_oficial": "1000",
            "usd_ars_blue": "1200",
            "btc_usd": "50000",
            "btc_ars": "60000000",
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["is_manual"] is True


def test_reprocess_endpoint_updates_transactions(client):
    register_user(client, email="reprocess@example.com")
    account_id = client.get("/accounts/").json()[0]["id"]
    rate_initial = create_manual_rate(client, effective_date="2024-01-10", usd_ars="1000")

    tx_response = client.post(
        "/transactions/",
        json={
            "transaction_date": "2024-01-10T12:00:00+00:00",
            "account_id": account_id,
            "currency_code": "USD",
            "amount_original": "1",
            "exchange_rate_id": rate_initial,
        },
    )
    assert tx_response.status_code == HTTPStatus.CREATED

    rate_new = create_manual_rate(client, effective_date="2024-01-11", usd_ars="1500")
    reprocess_resp = client.post("/exchange-rates/reprocess", json={"exchange_rate_id": rate_new})
    assert reprocess_resp.status_code == HTTPStatus.OK
    result = reprocess_resp.json()
    assert result["processed"] >= 1
    assert result["updated"] >= 1

    txs = client.get("/transactions/").json()
    assert Decimal(txs[0]["amount_ars"]) == Decimal("1500")
