from __future__ import annotations

import os
from typing import Any

import requests


class APIError(Exception):
    def __init__(self, status_code: int, detail: Any):
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


class ApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("BACKEND_INTERNAL_URL", "http://localhost:8000")
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        response = self.session.request(method, self._url(path), timeout=10, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise APIError(response.status_code, detail)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    # Auth
    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/auth/register", json=payload)

    def login(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/auth/login", json=payload)

    def logout(self) -> None:
        self._request("POST", "/auth/logout")

    def get_me(self) -> dict[str, Any]:
        return self._request("GET", "/auth/me")

    # Accounts
    def list_accounts(self) -> list[dict[str, Any]]:
        return self._request("GET", "/accounts/")

    def create_account(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/accounts/", json=payload)

    def update_account(self, account_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/accounts/{account_id}", json=payload)

    # Categories
    def list_categories(self) -> list[dict[str, Any]]:
        return self._request("GET", "/categories/")

    def create_category(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/categories/", json=payload)

    def update_category(self, category_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/categories/{category_id}", json=payload)

    # Transactions
    def list_transactions(self, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self._request("GET", "/transactions/", params=params or {})

    def create_transaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/transactions/", json=payload)

    def update_transaction(self, transaction_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/transactions/{transaction_id}", json=payload)

    def delete_transaction(self, transaction_id: int) -> None:
        self._request("DELETE", f"/transactions/{transaction_id}")

    # Exchange rates
    def latest_rates(self) -> dict[str, Any]:
        return self._request("GET", "/exchange-rates/latest")


def get_client() -> ApiClient:
    return ApiClient()
