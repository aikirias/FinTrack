from decimal import Decimal
from http import HTTPStatus


def register_user(client, email="reports@example.com"):
    payload = {"email": email, "password": "supersecret", "timezone": "UTC"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == HTTPStatus.CREATED


def create_rate(client, effective_date="2024-01-01"):
    response = client.post(
        "/exchange-rates/override",
        json={
            "effective_date": effective_date,
            "usd_ars_oficial": "1000",
            "usd_ars_blue": "1200",
            "btc_usd": "50000",
            "btc_ars": "60000000",
        },
    )
    assert response.status_code in (HTTPStatus.CREATED, HTTPStatus.BAD_REQUEST)
    if response.status_code == HTTPStatus.CREATED:
        return response.json()["id"]
    latest = client.get("/exchange-rates/latest")
    return latest.json()["id"]


def seed_transactions(client, account_id, rate_id, income_cat, expense_cat):
    payloads = [
        # January (previous period)
        {
            "transaction_date": "2024-01-15T10:00:00+00:00",
            "account_id": account_id,
            "currency_code": "USD",
            "amount_original": "80",
            "exchange_rate_id": rate_id,
            "category_id": income_cat,
        },
        {
            "transaction_date": "2024-01-20T10:00:00+00:00",
            "account_id": account_id,
            "currency_code": "USD",
            "amount_original": "40",
            "exchange_rate_id": rate_id,
            "category_id": expense_cat,
        },
        # February (current period)
        {
            "transaction_date": "2024-02-05T10:00:00+00:00",
            "account_id": account_id,
            "currency_code": "USD",
            "amount_original": "100",
            "exchange_rate_id": rate_id,
            "category_id": income_cat,
        },
        {
            "transaction_date": "2024-02-10T10:00:00+00:00",
            "account_id": account_id,
            "currency_code": "USD",
            "amount_original": "50",
            "exchange_rate_id": rate_id,
            "category_id": expense_cat,
        },
    ]
    for payload in payloads:
        resp = client.post("/transactions/", json=payload)
        assert resp.status_code == HTTPStatus.CREATED


def seed_budget(client, income_cat, expense_cat):
    payload = {
        "month": "2024-02-01",
        "currency_code": "ARS",
        "name": "Febrero",
        "items": [
            {"category_id": income_cat, "amount": "110000"},
            {"category_id": expense_cat, "amount": "45000"},
        ],
    }
    resp = client.post("/budgets/", json=payload)
    assert resp.status_code == HTTPStatus.CREATED


def test_reports_endpoints(client):
    register_user(client)
    accounts_resp = client.get("/accounts/")
    account_id = accounts_resp.json()[0]["id"]

    categories = client.get("/categories/").json()
    expense_cat = next(cat["id"] for cat in categories if cat["type"] == "expense" and cat["parent_id"] is None)
    income_cat = next(cat["id"] for cat in categories if cat["type"] == "income" and cat["parent_id"] is None)

    rate_id = create_rate(client)
    seed_transactions(client, account_id, rate_id, income_cat, expense_cat)
    seed_budget(client, income_cat, expense_cat)

    summary_resp = client.get(
        "/reports/summary",
        params={
            "start": "2024-02-01T00:00:00+00:00",
            "end": "2024-03-01T00:00:00+00:00",
            "currency": "ARS",
        },
    )
    summary = summary_resp.json()
    assert Decimal(summary["totals"]["income"]) == Decimal("100000")
    assert Decimal(summary["totals"]["expense"]) == Decimal("50000")
    assert summary["previous_totals"] is not None
    assert Decimal(summary["previous_totals"]["income"]) == Decimal("80000")
    assert summary["budget_totals"] is not None
    assert Decimal(summary["budget_totals"]["income"]) == Decimal("110000")
    assert Decimal(summary["budget_totals"]["expense"]) == Decimal("45000")

    timeseries = client.get(
        "/reports/timeseries",
        params={
            "start": "2024-01-01T00:00:00+00:00",
            "end": "2024-03-01T00:00:00+00:00",
            "currency": "ARS",
            "interval": "month",
        },
    ).json()
    months = {point["period"]: point for point in timeseries["points"]}
    assert Decimal(months["2024-01-01"]["income"]) == Decimal("80000")
    assert Decimal(months["2024-02-01"]["expense"]) == Decimal("50000")

    category_resp = client.get(
        "/reports/categories",
        params={
            "start": "2024-02-01T00:00:00+00:00",
            "end": "2024-03-01T00:00:00+00:00",
            "currency": "ARS",
            "type": "expense",
        },
    )
    entries = category_resp.json()["entries"]
    assert any(entry["category_id"] == expense_cat and Decimal(entry["total"]) == Decimal("50000") for entry in entries)
