from __future__ import annotations

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

import altair as alt
import pandas as pd
import streamlit as st

from api import APIError, ApiClient, get_client

BACKEND_EXTERNAL_URL = os.getenv("BACKEND_EXTERNAL_URL", "http://localhost:8000")


def init_session_state() -> None:
    if "api_client" not in st.session_state:
        st.session_state.api_client = get_client()
    if "user" not in st.session_state:
        st.session_state.user = None
    if "accounts" not in st.session_state:
        st.session_state.accounts = []
    if "categories" not in st.session_state:
        st.session_state.categories = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    if "latest_rates" not in st.session_state:
        st.session_state.latest_rates = None
    if "flash" not in st.session_state:
        st.session_state.flash = None


def set_flash(message: str, level: str = "success") -> None:
    st.session_state.flash = {"message": message, "level": level}


def consume_flash() -> None:
    flash = st.session_state.get("flash")
    if not flash:
        return
    level = flash.get("level", "info")
    message = flash.get("message")
    if not message:
        st.session_state.flash = None
        return
    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    elif level == "error":
        st.error(message)
    else:
        st.info(message)
    st.session_state.flash = None


def handle_api_call(func, success_message: str | None = None, refresh: bool = True):
    try:
        result = func()
        if success_message:
            st.success(success_message)
        if refresh:
            refresh_cached_data()
        return result
    except APIError as exc:
        detail = exc.detail
        if isinstance(detail, dict):
            detail = detail.get("detail") or detail
        st.error(f"Error: {detail}")
        return None


def refresh_cached_data(fetch_transactions: bool = True) -> None:
    client: ApiClient = st.session_state.api_client
    try:
        st.session_state.accounts = client.list_accounts()
        st.session_state.categories = client.list_categories()
        st.session_state.latest_rates = client.latest_rates()
        if fetch_transactions:
            st.session_state.transactions = client.list_transactions({"limit": 500})
    except APIError as exc:
        if exc.status_code == 401:
            st.session_state.user = None
        else:
            st.error(f"No se pudo actualizar la información ({exc.detail})")


def flatten_categories(categories: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    mapping: Dict[int, Dict[str, Any]] = {}

    def _walk(nodes: List[Dict[str, Any]], parent: Dict[str, Any] | None = None) -> None:
        for node in nodes:
            entry = {
                "id": node["id"],
                "name": node["name"],
                "type": node["type"],
                "parent_id": node.get("parent_id"),
                "parent_name": parent["name"] if parent else None,
                "is_archived": node.get("is_archived", False),
            }
            mapping[node["id"]] = entry
            children = node.get("children") or []
            if children:
                _walk(children, node)

    _walk(categories)
    return mapping


def login_view() -> None:
    st.title("FinTrack Multi Moneda")
    st.caption("Controlá tus finanzas en ARS, USD y BTC")
    tabs = st.tabs(["Ingresar", "Crear cuenta"])

    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar")
            if submitted:
                client: ApiClient = st.session_state.api_client
                try:
                    user = client.login({"email": email, "password": password})
                except APIError as exc:
                    detail = exc.detail
                    if isinstance(detail, dict):
                        detail = detail.get("detail") or detail
                    st.error(f"No se pudo iniciar sesión: {detail}")
                else:
                    st.session_state.user = user
                    refresh_cached_data()
                    set_flash("Sesión iniciada correctamente", "success")
                    st.rerun()

    with tabs[1]:
        with st.form("register_form"):
            email = st.text_input("Email nuevo")
            timezone = st.text_input("Zona horaria", value="America/Argentina/Buenos_Aires")
            password = st.text_input("Contraseña", type="password")
            confirm = st.text_input("Repetí la contraseña", type="password")
            if st.form_submit_button("Crear cuenta"):
                if password != confirm:
                    st.error("Las contraseñas no coinciden")
                else:
                    client: ApiClient = st.session_state.api_client
                    try:
                        user = client.register(
                            {"email": email, "password": password, "timezone": timezone}
                        )
                    except APIError as exc:
                        detail = exc.detail
                        if isinstance(detail, dict):
                            detail = detail.get("detail") or detail
                        st.error(f"No se pudo registrar: {detail}")
                    else:
                        st.session_state.user = user
                        refresh_cached_data()
                        set_flash("Cuenta creada con éxito", "success")
                        st.rerun()


def logout() -> None:
    client: ApiClient = st.session_state.api_client
    try:
        client.logout()
    except APIError:
        pass
    st.session_state.user = None
    st.session_state.transactions = []
    st.session_state.accounts = []
    st.session_state.categories = []
    st.session_state.latest_rates = None
    set_flash("Sesión cerrada", "info")
    st.rerun()


def sidebar(user: Dict[str, Any], category_map: Dict[int, Dict[str, Any]]) -> str:
    with st.sidebar:
        st.markdown(f"### {user['email']}")
        st.caption(f"Zona horaria: {user['timezone']}")
        st.button("Cerrar sesión", on_click=logout)
        st.divider()
        page = st.radio(
            "Secciones",
            options=["Dashboard", "Nueva transacción", "Movimientos", "Categorías", "Cuentas"],
        )
        st.divider()
        if st.session_state.latest_rates:
            rates = st.session_state.latest_rates
            st.markdown(
                f"**USD oficial:** {rates['usd_ars_oficial']} | **Blue:** {rates.get('usd_ars_blue') or '-'}"
            )
            st.markdown(
                f"**BTC/USD:** {rates['btc_usd']} | **BTC/ARS:** {rates['btc_ars']}"
            )
    return page


def dashboard_view(category_map: Dict[int, Dict[str, Any]]) -> None:
    st.header("Dashboard")
    transactions = st.session_state.transactions
    if not transactions:
        st.info("Todavía no registraste movimientos. Cargá tu primera transacción para ver el dashboard.")
        return

    base_currency = st.selectbox("Moneda base", options=["ARS", "USD", "BTC"], index=0)
    amount_key = f"amount_{base_currency.lower()}"

    df = pd.DataFrame(transactions)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["date"] = df["transaction_date"].dt.date
    df["month"] = df["transaction_date"].dt.to_period("M").dt.to_timestamp()

    df["category_name"] = df["category_id"].map(lambda cid: category_map.get(cid, {}).get("name", "Sin categoría"))
    df["type"] = df["category_id"].map(lambda cid: category_map.get(cid, {}).get("type", "n/a"))

    df["value"] = df[amount_key].astype(float)
    df.loc[df["type"] == "expense", "value"] *= -1

    total_balance = df["value"].sum()
    incomes = df[df["type"] == "income"]["value"].sum()
    expenses = df[df["type"] == "expense"]["value"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric(f"Balance ({base_currency})", f"{total_balance:,.2f}")
    col2.metric("Ingresos", f"{incomes:,.2f}")
    col3.metric("Gastos", f"{abs(expenses):,.2f}")

    st.subheader("Evolución por categoría")
    area_source = (
        df.groupby(["month", "category_name"], as_index=False)["value"].sum()
        .sort_values("month")
    )
    area_chart = (
        alt.Chart(area_source)
        .mark_area()
        .encode(
            x="month:T",
            y="value:Q",
            color="category_name:N",
            tooltip=["month:T", "category_name:N", "value:Q"],
        )
        .interactive()
    )
    st.altair_chart(area_chart, use_container_width=True)

    st.subheader("Distribución por categoría")
    dist_source = df.groupby("category_name", as_index=False)["value"].sum()
    dist_source["value"] = dist_source["value"].abs()
    pie_chart = (
        alt.Chart(dist_source)
        .mark_arc(innerRadius=60)
        .encode(theta="value:Q", color="category_name:N", tooltip=["category_name", "value"])
    )
    st.altair_chart(pie_chart, use_container_width=True)

    st.subheader("Heatmap de gastos por día")
    heat_df = df[df["type"] == "expense"].copy()
    if not heat_df.empty:
        heat_df["day"] = heat_df["transaction_date"].dt.day
        heat_df["month"] = heat_df["transaction_date"].dt.strftime("%Y-%m")
        heat_df["value"] = heat_df[amount_key].astype(float) * -1
        heat_chart = (
            alt.Chart(heat_df)
            .mark_rect()
            .encode(
                x="day:O",
                y="month:O",
                color=alt.Color("value:Q", scale=alt.Scale(scheme="reds")),
                tooltip=["month", "day", "value"],
            )
        )
        st.altair_chart(heat_chart, use_container_width=True)
    else:
        st.caption("Sin gastos registrados aún para el heatmap")


def transaction_form(category_map: Dict[int, Dict[str, Any]]) -> None:
    st.header("Nueva transacción")
    accounts = st.session_state.accounts
    if not accounts:
        st.warning("Necesitás crear una cuenta antes de cargar transacciones")
        return

    categories = st.session_state.categories
    parent_options = ["Sin categoría"] + [c["name"] for c in categories]

    with st.form("transaction_form"):
        account = st.selectbox("Cuenta", options=accounts, format_func=lambda item: f"{item['name']} ({item['currency_code']})")
        amount = st.number_input("Monto", min_value=0.0, step=0.01)
        currency = st.selectbox("Moneda", ["ARS", "USD", "BTC"], index=0)
        rate_type = st.selectbox("Tipo de cambio", ["official", "blue"], index=0)
        date_value = st.date_input("Fecha", value=datetime.now().date())
        time_value = st.time_input("Hora", value=datetime.now().time())

        selected_parent = st.selectbox("Categoría", options=parent_options)
        parent_id = None
        if selected_parent != "Sin categoría":
            for cat in categories:
                if cat["name"] == selected_parent:
                    parent_id = cat["id"]
                    break

        sub_options = ["Sin subcategoría"]
        if parent_id:
            parent = next((cat for cat in categories if cat["id"] == parent_id), None)
            if parent:
                sub_options += [child["name"] for child in parent.get("children", [])]
        selected_sub = st.selectbox("Subcategoría", options=sub_options)
        sub_id = None
        if selected_sub != "Sin subcategoría" and parent_id:
            parent = next((cat for cat in categories if cat["id"] == parent_id), None)
            if parent:
                for child in parent.get("children", []):
                    if child["name"] == selected_sub:
                        sub_id = child["id"]
                        break

        notes = st.text_area("Notas", max_chars=300)

        preview_placeholder = st.empty()

        def preview_conversion() -> None:
            rates = st.session_state.latest_rates
            if not rates:
                return
            amount_decimal = Decimal(str(amount))
            if currency == "ARS":
                usd_rate = Decimal(str(rates["usd_ars_blue"])) if rate_type == "blue" and rates.get("usd_ars_blue") else Decimal(str(rates["usd_ars_oficial"]))
                amount_ars = amount_decimal
                amount_usd = amount_decimal / usd_rate
                amount_btc = amount_decimal / Decimal(str(rates["btc_ars"]))
            elif currency == "USD":
                usd_rate = Decimal(str(rates["usd_ars_blue"])) if rate_type == "blue" and rates.get("usd_ars_blue") else Decimal(str(rates["usd_ars_oficial"]))
                amount_ars = amount_decimal * usd_rate
                amount_usd = amount_decimal
                amount_btc = amount_decimal / Decimal(str(rates["btc_usd"]))
            else:
                amount_btc = amount_decimal
                amount_usd = amount_decimal * Decimal(str(rates["btc_usd"]))
                amount_ars = amount_decimal * Decimal(str(rates["btc_ars"]))
            preview_placeholder.info(
                f"ARS: {amount_ars:.2f} | USD: {amount_usd:.4f} | BTC: {amount_btc:.6f}"
            )

        st.button("Previsualizar conversión", on_click=preview_conversion)

        submitted = st.form_submit_button("Guardar")
        if submitted:
            payload = {
                "transaction_date": datetime.combine(date_value, time_value).isoformat(),
                "account_id": account["id"],
                "currency_code": currency,
                "amount_original": str(amount),
                "rate_type": rate_type,
                "category_id": parent_id,
                "subcategory_id": sub_id,
                "notes": notes or None,
            }
            handle_api_call(lambda: st.session_state.api_client.create_transaction(payload), "Transacción registrada")
            st.rerun()


def transactions_view(category_map: Dict[int, Dict[str, Any]]) -> None:
    st.header("Movimientos")
    transactions = st.session_state.transactions
    if not transactions:
        st.info("No hay movimientos todavía")
        return

    df = pd.DataFrame(transactions)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["currency"] = df["currency_code"]
    df["category"] = df["category_id"].map(lambda cid: category_map.get(cid, {}).get("name", "Sin categoría"))
    df["subcategory"] = df["subcategory_id"].map(lambda cid: category_map.get(cid, {}).get("name"))

    df_display = df[[
        "transaction_date",
        "currency",
        "amount_original",
        "amount_ars",
        "amount_usd",
        "amount_btc",
        "category",
        "subcategory",
        "notes",
    ]].copy()
    df_display = df_display.sort_values("transaction_date", ascending=False)
    st.dataframe(df_display, use_container_width=True)


def categories_view() -> None:
    st.header("Categorías")
    categories = st.session_state.categories
    if not categories:
        st.info("No hay categorías disponibles")
    else:
        def render_tree(nodes: List[Dict[str, Any]], level: int = 0) -> None:
            for node in nodes:
                prefix = "➜ " if level == 0 else "".ljust(level * 2, " ") + "• "
                st.write(f"{prefix}{node['name']} ({node['type']})")
                if node.get("children"):
                    render_tree(node["children"], level + 1)

        render_tree(categories)

    with st.form("new_category"):
        st.subheader("Crear nueva categoría")
        name = st.text_input("Nombre")
        category_type = st.selectbox("Tipo", ["income", "expense", "transfer"], index=1)
        parent_options = ["Sin categoría"] + [c["name"] for c in categories]
        selected_parent = st.selectbox("Padre", parent_options)
        parent_id = None
        if selected_parent != "Sin categoría":
            for cat in categories:
                if cat["name"] == selected_parent:
                    parent_id = cat["id"]
                    break
        if st.form_submit_button("Guardar categoría"):
            payload = {"name": name, "type": category_type, "parent_id": parent_id}
            handle_api_call(lambda: st.session_state.api_client.create_category(payload), "Categoría creada")
            st.rerun()


def accounts_view() -> None:
    st.header("Cuentas")
    accounts = st.session_state.accounts
    if accounts:
        st.table(
            {
                "Cuenta": [acc["name"] for acc in accounts],
                "Moneda": [acc["currency_code"] for acc in accounts],
                "Estado": ["Archivada" if acc["is_archived"] else "Activa" for acc in accounts],
            }
        )
    else:
        st.info("Sin cuentas registradas aún")

    with st.form("new_account"):
        st.subheader("Agregar cuenta")
        name = st.text_input("Nombre de la cuenta")
        currency = st.selectbox("Moneda", ["ARS", "USD", "BTC"])
        description = st.text_input("Descripción (opcional)")
        if st.form_submit_button("Crear cuenta"):
            payload = {"name": name, "currency_code": currency, "description": description or None}
            handle_api_call(lambda: st.session_state.api_client.create_account(payload), "Cuenta creada")
            st.rerun()


def app() -> None:
    st.set_page_config(page_title="FinTrack", layout="wide", page_icon="💸")
    init_session_state()
    consume_flash()

    user = st.session_state.user
    if not user:
        login_view()
        return

    if not st.session_state.transactions:
        refresh_cached_data()

    category_map = flatten_categories(st.session_state.categories)
    page = sidebar(user, category_map)

    if page == "Dashboard":
        dashboard_view(category_map)
    elif page == "Nueva transacción":
        transaction_form(category_map)
    elif page == "Movimientos":
        transactions_view(category_map)
    elif page == "Categorías":
        categories_view()
    elif page == "Cuentas":
        accounts_view()


if __name__ == "__main__":
    app()
