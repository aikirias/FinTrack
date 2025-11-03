from datetime import datetime, timezone
from decimal import Decimal

from http import HTTPStatus


def register_user(client, email="tx@example.com"):
    payload = {
        "email": email,
        "password": "verysecure",
        "timezone": "UTC",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == HTTPStatus.CREATED
    return response.json()


def create_rate(client, effective_date="2024-01-01") -> int:
    response = client.post(
        "/exchange-rates/override",
        json={
            "effective_date": effective_date,
            "usd_ars_oficial": "1000",
            "usd_ars_blue": "1300",
            "btc_usd": "50000",
            "btc_ars": "65000000",
        },
    )
    assert response.status_code in (HTTPStatus.CREATED, HTTPStatus.BAD_REQUEST)
    if response.status_code == HTTPStatus.CREATED:
        return response.json()["id"]
    latest = client.get("/exchange-rates/latest")
    assert latest.status_code == HTTPStatus.OK
    return latest.json()["id"]


def test_create_transaction_conversion(client):
    register_user(client, email="conv@example.com")
    accounts_resp = client.get("/accounts/")
    assert accounts_resp.status_code == HTTPStatus.OK
    account_id = accounts_resp.json()[0]["id"]

    rate_id = create_rate(client, "2024-01-02")

    tx_response = client.post(
        "/transactions/",
        json={
            "transaction_date": "2024-01-02T12:00:00+00:00",
            "account_id": account_id,
            "currency_code": "USD",
            "amount_original": "100",
            "exchange_rate_id": rate_id,
        },
    )
    assert tx_response.status_code == HTTPStatus.CREATED
    data = tx_response.json()
    assert Decimal(data["amount_usd"]) == Decimal("100")
    assert Decimal(data["amount_ars"]) == Decimal("100000")
    assert Decimal(data["amount_btc"]) == Decimal("0.00200000")


def test_update_transaction_switch_to_blue_rate(client):
    register_user(client, email="blue@example.com")
    account_id = client.get("/accounts/").json()[0]["id"]
    rate_id = create_rate(client, "2024-01-03")

    tx_response = client.post(
        "/transactions/",
        json={
            "transaction_date": "2024-01-03T10:00:00+00:00",
            "account_id": account_id,
            "currency_code": "USD",
            "amount_original": "50",
            "exchange_rate_id": rate_id,
        },
    )
    tx_id = tx_response.json()["id"]

    update_resp = client.patch(
        f"/transactions/{tx_id}",
        json={"rate_type": "blue"},
    )
    assert update_resp.status_code == HTTPStatus.OK
    updated = update_resp.json()
    assert Decimal(updated["amount_ars"]) == Decimal("65000")
    assert updated["rate_type"] == "blue"
