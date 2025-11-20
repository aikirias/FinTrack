from http import HTTPStatus


def register_user(client, email="budget@example.com"):
    payload = {
        "email": email,
        "password": "verysecure",
        "timezone": "UTC",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == HTTPStatus.CREATED


def get_sample_categories(client):
    response = client.get("/categories/")
    assert response.status_code == HTTPStatus.OK
    categories = response.json()
    expense = next(cat for cat in categories if cat["type"] == "expense" and cat["parent_id"] is None)
    income = next(cat for cat in categories if cat["type"] == "income" and cat["parent_id"] is None)
    return income["id"], expense["id"]


def test_budget_crud_flow(client):
    register_user(client)
    income_cat, expense_cat = get_sample_categories(client)

    create_payload = {
        "month": "2024-02-01",
        "currency_code": "ARS",
        "name": "Febrero",
        "items": [
            {"category_id": income_cat, "amount": "200000"},
            {"category_id": expense_cat, "amount": "120000"},
        ],
    }
    response = client.post("/budgets/", json=create_payload)
    assert response.status_code == HTTPStatus.CREATED
    budget_id = response.json()["id"]

    # Duplicate budget should fail
    dup_response = client.post("/budgets/", json=create_payload)
    assert dup_response.status_code == HTTPStatus.BAD_REQUEST

    list_response = client.get("/budgets/", params={"month": "2024-02-01", "currency": "ARS"})
    assert list_response.status_code == HTTPStatus.OK
    assert len(list_response.json()) == 1

    update_resp = client.patch(
        f"/budgets/{budget_id}",
        json={
            "name": "Febrero Ajustado",
            "items": [
                {"category_id": income_cat, "amount": "250000"},
                {"category_id": expense_cat, "amount": "100000"},
            ],
        },
    )
    assert update_resp.status_code == HTTPStatus.OK
    assert update_resp.json()["name"] == "Febrero Ajustado"

    delete_resp = client.delete(f"/budgets/{budget_id}")
    assert delete_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.get("/budgets/", params={"month": "2024-02-01", "currency": "ARS"}).json() == []
