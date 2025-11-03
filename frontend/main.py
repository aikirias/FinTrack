from __future__ import annotations

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

import numpy as np

import altair as alt
import pandas as pd
import streamlit as st

from api import APIError, ApiClient, get_client

BACKEND_EXTERNAL_URL = os.getenv("BACKEND_EXTERNAL_URL", "http://localhost:8000")
MONTH_NAMES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def load_custom_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #0b1324;
            --card-bg: rgba(17, 25, 40, 0.85);
            --card-border: rgba(148, 163, 184, 0.08);
            --accent: #0ea5e9;
            --accent-soft: rgba(14, 165, 233, 0.12);
            --success: #22c55e;
            --warning: #facc15;
            --danger: #f87171;
        }

        .main {
            background: linear-gradient(180deg, #0b1324 0%, #020617 100%);
        }

        section[data-testid="stSidebar"] {
            background: var(--bg-secondary);
            border-right: 1px solid rgba(148, 163, 184, 0.1);
        }

        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #e2e8f0;
        }

        .app-card {
            border-radius: 18px;
            padding: 1.4rem;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            box-shadow: 0px 25px 60px -35px rgba(15, 23, 42, 0.7);
            margin-bottom: 1.2rem;
        }

        .app-card__title {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94a3b8;
            margin-bottom: 0.5rem;
        }

        .app-card__value {
            font-size: 2rem;
            font-weight: 600;
            color: #f8fafc;
        }

        .status-grid {
            display: grid;
            gap: 1.2rem;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        }

        .status-card {
            position: relative;
            overflow: hidden;
            border-radius: 18px;
            padding: 1.5rem;
            background: linear-gradient(135deg, rgba(14,165,233,0.18), rgba(59,130,246,0.18));
            border: 1px solid rgba(59, 130, 246, 0.25);
        }

        .status-card--income {
            background: linear-gradient(135deg, rgba(34,197,94,0.18), rgba(16,185,129,0.18));
            border-color: rgba(34,197,94,0.25);
        }

        .status-card--expense {
            background: linear-gradient(135deg, rgba(248,113,113,0.18), rgba(239,68,68,0.18));
            border-color: rgba(248,113,113,0.25);
        }

        .status-card__label {
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            color: #d0d8e5;
            text-transform: uppercase;
        }

        .status-card__value {
            font-size: 2.2rem;
            font-weight: 600;
            color: #f8fafc;
            margin-top: 0.4rem;
        }

        .status-card__meta {
            margin-top: 0.9rem;
            font-size: 0.85rem;
            color: #cbd5f5;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .calendar-container {
            background: var(--card-bg);
            border-radius: 18px;
            padding: 1.2rem 1.5rem;
            border: 1px solid var(--card-border);
        }

        .calendar-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }

        .timeline-item {
            padding: 0.8rem 1rem;
            border-radius: 14px;
            border: 1px solid rgba(148, 163, 184, 0.14);
            background: rgba(15, 23, 42, 0.5);
            margin-bottom: 0.6rem;
        }

        .timeline-item:hover {
            border-color: var(--accent);
            background: rgba(14,165,233,0.07);
        }

        .tag {
            display: inline-flex;
            padding: 0.1rem 0.55rem;
            border-radius: 999px;
            font-size: 0.72rem;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            background: rgba(148,163,184,0.2);
            color: #e2e8f0;
        }

        .tag--income { background: rgba(34,197,94,0.22); color: #bbf7d0; }
        .tag--expense { background: rgba(248,113,113,0.22); color: #fecaca; }

        div[data-testid="stMetricValue"] {
            font-size: 1.7rem;
            color: #f8fafc;
        }

        div[data-testid="stMetricDelta"] {
            font-size: 0.85rem;
        }

        div[data-testid="stForm"] {
            background: var(--card-bg);
            padding: 1.2rem 1.5rem 1.4rem 1.5rem;
            border-radius: 18px;
            border: 1px solid var(--card-border);
            box-shadow: 0px 25px 60px -40px rgba(15, 23, 42, 0.8);
        }

        div[data-testid="stForm"] label {
            font-weight: 600;
        }

        .stButton>button {
            border-radius: 14px;
            background: linear-gradient(90deg, #0284c7 0%, #22d3ee 100%);
            color: #f8fafc;
            border: none;
            font-weight: 600;
            padding: 0.6rem 1rem;
        }

        .stButton>button:hover {
            filter: brightness(1.08);
        }

        .category-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: rgba(148, 163, 184, 0.18);
            color: #e2e8f0;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            margin: 0.2rem 0.4rem 0.2rem 0;
            font-size: 0.8rem;
        }

        .scroll-container {
            max-height: 420px;
            overflow-y: auto;
            padding-right: 0.4rem;
        }

        .subtle-card {
            padding: 1rem;
            border-radius: 12px;
            background: rgba(148,163,184,0.08);
            border: 1px solid rgba(148,163,184,0.12);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_currency_symbol(currency: str) -> str:
    return {"ARS": "$", "USD": "US$", "BTC": "₿"}.get(currency.upper(), "")


def format_currency(value: float, currency: str, precision: int | None = None) -> str:
    symbol = get_currency_symbol(currency)
    if precision is None:
        precision = 8 if currency.upper() == "BTC" else 2
    formatted = f"{value:,.{precision}f}"
    return f"{symbol}{formatted}"


def format_month_label(period: pd.Period) -> str:
    if pd.isna(period):
        return ""
    month_name = MONTH_NAMES[period.month - 1].capitalize()
    return f"{month_name} {period.year}"


def format_delta(current: float, previous: float, suffix: str = "", inverse: bool = False) -> str:
    if previous == 0:
        return "–"
    diff = current - previous
    if inverse:
        diff = -diff
    pct = abs(diff) / abs(previous) * 100
    arrow = "▲" if diff >= 0 else "▼"
    sign = "+" if diff >= 0 else "-"
    return f"{arrow} {sign}{pct:.1f}% {suffix}".strip()


def prepare_transactions_dataframe(
    transactions: list[dict[str, Any]], base_currency: str, category_map: Dict[int, Dict[str, Any]]
) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    value_key = f"amount_{base_currency.lower()}"
    df["value"] = df[value_key].astype(float)
    df["category_name"] = df["category_id"].map(lambda cid: category_map.get(cid, {}).get("name", "Sin categoría"))
    df["category_type"] = df["category_id"].map(lambda cid: category_map.get(cid, {}).get("type"))
    df["category_type"] = df["category_type"].fillna("otros")
    df["signed_value"] = np.where(df["category_type"] == "expense", -df["value"], df["value"])
    df["period"] = df["transaction_date"].dt.to_period("M")
    df["date"] = df["transaction_date"].dt.date
    if "notes" in df.columns:
        df["notes"] = df["notes"].fillna("")
    else:
        df["notes"] = ""
    return df


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
    if "dashboard_base_currency" not in st.session_state:
        st.session_state.dashboard_base_currency = "ARS"
    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = None


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
    st.markdown("## Visión general")
    transactions = st.session_state.transactions
    if not transactions:
        st.info("Todavía no registraste movimientos. Cargá tu primera transacción para ver paneles e insights.")
        return

    base_options = ["ARS", "USD", "BTC"]
    default_index = base_options.index(st.session_state.dashboard_base_currency)
    base_currency = st.radio(
        "Moneda base",
        base_options,
        index=default_index,
        horizontal=True,
        key="dashboard_base_currency_choice",
    )
    st.session_state.dashboard_base_currency = base_currency

    df = prepare_transactions_dataframe(transactions, base_currency, category_map)

    current_period = df["period"].max()
    previous_period = current_period - 1 if current_period is not pd.NaT else None

    balance = df["signed_value"].sum()
    income_total = df[df["category_type"] == "income"]["value"].sum()
    expense_total = df[df["category_type"] == "expense"]["value"].sum()

    balance_prev = df[df["period"] == previous_period]["signed_value"].sum() if previous_period else 0.0
    income_prev = df[df["period"] == previous_period]["value"].sum() if previous_period else 0.0
    expense_prev = (
        df[(df["period"] == previous_period) & (df["category_type"] == "expense")]["value"].sum()
        if previous_period
        else 0.0
    )

    top_expense = (
        df[df["category_type"] == "expense"]
        .groupby("category_name")["value"]
        .sum()
        .sort_values(ascending=False)
        .head(1)
    )
    top_expense_label = (
        f"{top_expense.index[0]} · {format_currency(top_expense.iloc[0], base_currency)}"
        if not top_expense.empty
        else "Sin gastos registrados"
    )

    summary = {
        "balance": format_currency(balance, base_currency),
        "balance_delta": format_delta(balance, balance_prev, "vs mes anterior"),
        "income": format_currency(income_total, base_currency),
        "income_delta": format_delta(income_total, income_prev, "vs mes anterior"),
        "expense": format_currency(expense_total, base_currency),
        "expense_delta": format_delta(expense_total, expense_prev, "vs mes anterior", inverse=True),
        "top_expense": top_expense_label,
    }

    render_status_cards(summary)

    primary_col, secondary_col = st.columns((2.1, 1))

    with primary_col:
        render_calendar_section(df, base_currency)
        render_trend_section(df, base_currency)

    with secondary_col:
        render_activity_timeline(df, base_currency)
        render_daily_digest(df, base_currency)


def render_status_cards(summary: Dict[str, str]) -> None:
    st.markdown(
        f"""
        <div class="status-grid">
            <div class="status-card">
                <div class="status-card__label">Balance neto</div>
                <div class="status-card__value">{summary['balance']}</div>
                <div class="status-card__meta">{summary['balance_delta']}</div>
            </div>
            <div class="status-card status-card--income">
                <div class="status-card__label">Ingresos acumulados</div>
                <div class="status-card__value">{summary['income']}</div>
                <div class="status-card__meta">{summary['income_delta']}</div>
            </div>
            <div class="status-card status-card--expense">
                <div class="status-card__label">Gastos acumulados</div>
                <div class="status-card__value">{summary['expense']}</div>
                <div class="status-card__meta">{summary['expense_delta']} · {summary['top_expense']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_calendar_section(df: pd.DataFrame, base_currency: str) -> None:
    st.markdown("### Calendario de gastos")
    expenses_df = df[df["category_type"] == "expense"].copy()
    if expenses_df.empty:
        st.caption("Todavía no hay gastos para representar en el calendario.")
        return

    month_periods = sorted(expenses_df["period"].unique())
    month_labels = [format_month_label(period) for period in month_periods]
    default_idx = month_labels.index(st.session_state.calendar_month) if st.session_state.calendar_month in month_labels else len(month_labels) - 1

    selected_label = st.selectbox("Seleccioná el mes", month_labels, index=default_idx, key="calendar_month_select")
    st.session_state.calendar_month = selected_label
    selected_period = month_periods[month_labels.index(selected_label)]

    month_df = expenses_df[expenses_df["period"] == selected_period].copy()
    month_df["date"] = pd.to_datetime(month_df["date"])

    month_start = selected_period.to_timestamp()
    month_end = (selected_period + 1).to_timestamp() - pd.Timedelta(days=1)
    calendar_df = pd.DataFrame({"date": pd.date_range(month_start, month_end, freq="D")})

    daily_totals = month_df.groupby("date")["value"].sum().reindex(calendar_df["date"], fill_value=0)
    calendar_df["value"] = daily_totals.values
    weekday_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    calendar_df["weekday"] = calendar_df["date"].dt.dayofweek.apply(lambda idx: weekday_labels[idx])
    calendar_df["week"] = ((calendar_df["date"].dt.day - 1) // 7) + 1
    calendar_df["day_number"] = calendar_df["date"].dt.day

    max_value = calendar_df["value"].max() or 1

    heat = (
        alt.Chart(calendar_df)
        .mark_rect(cornerRadius=8)
        .encode(
            x=alt.X("week:O", title="Semana"),
            y=alt.Y("weekday:O", sort=weekday_labels, title=""),
            color=alt.Color(
                "value:Q",
                title=f"Gasto ({base_currency})",
                scale=alt.Scale(scheme="teals", domain=[0, max_value]),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Fecha"),
                alt.Tooltip("value:Q", title="Total", format=",.2f"),
            ],
        )
        .properties(height=260)
    )

    text = (
        alt.Chart(calendar_df)
        .mark_text(color="#f8fafc", fontSize=12)
        .encode(x="week:O", y=alt.Y("weekday:O", sort=weekday_labels), text="day_number:Q")
    )

    st.altair_chart((heat + text).interactive(), use_container_width=True)

    highlight = calendar_df.loc[calendar_df["value"].idxmax()]
    if highlight["value"] > 0:
        st.caption(
            f"Mayor gasto del mes: {format_currency(highlight['value'], base_currency)} el {highlight['date'].strftime('%d/%m')}"
        )


def render_trend_section(df: pd.DataFrame, base_currency: str) -> None:
    st.markdown("### Tendencias y categorías")
    monthly = (
        df.groupby(["period", "category_type"])["value"]
        .sum()
        .reset_index()
    )
    monthly["month"] = monthly["period"].dt.to_timestamp()
    monthly["signed"] = np.where(monthly["category_type"] == "expense", -monthly["value"], monthly["value"])

    if monthly.empty:
        st.caption("Sin datos suficientes para tendencias.")
    else:
        line = (
            alt.Chart(monthly)
            .mark_line(point=True)
            .encode(
                x=alt.X("month:T", title="Mes"),
                y=alt.Y("signed:Q", title=f"Saldo ({base_currency})"),
                color=alt.Color(
                    "category_type:N",
                    title="Tipo",
                    scale=alt.Scale(range=["#22d3ee", "#f87171", "#fbbf24"]),
                ),
                tooltip=[
                    alt.Tooltip("month:T", title="Mes"),
                    alt.Tooltip("category_type:N", title="Tipo"),
                    alt.Tooltip("signed:Q", title="Saldo", format=",.2f"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(line, use_container_width=True)

    top_expenses = (
        df[df["category_type"] == "expense"]
        .groupby("category_name")["value"]
        .sum()
        .reset_index()
        .sort_values("value", ascending=False)
        .head(5)
    )
    if not top_expenses.empty:
        top_expenses["value"] = top_expenses["value"].astype(float)
        bar = (
            alt.Chart(top_expenses)
            .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
            .encode(
                x=alt.X("value:Q", title=f"Gasto ({base_currency})"),
                y=alt.Y("category_name:N", sort="-x", title=""),
                color=alt.value("#fb7185"),
                tooltip=[
                    alt.Tooltip("category_name:N", title="Categoría"),
                    alt.Tooltip("value:Q", title="Total", format=",.2f"),
                ],
            )
            .properties(height=220)
        )
        st.markdown("#### Categorías con mayor gasto")
        st.altair_chart(bar, use_container_width=True)


def render_activity_timeline(df: pd.DataFrame, base_currency: str) -> None:
    st.markdown("### Movimientos recientes")
    recent = df.sort_values("transaction_date", ascending=False).head(6)
    if recent.empty:
        st.caption("Sin movimientos registrados todavía.")
        return

    for row in recent.itertuples():
        signed = row.signed_value
        amount_display = format_currency(abs(row.value), base_currency)
        prefix = "-" if signed < 0 else "+"
        badge_class = "tag--expense" if signed < 0 else "tag--income"
        st.markdown(
            f"""
            <div class="timeline-item">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-weight:600;color:#f8fafc;">{row.category_name}</div>
                        <div style="color:#94a3b8;font-size:0.78rem;">{row.transaction_date.strftime('%d %b %Y • %H:%M')}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-weight:600;color:{'#fda4af' if signed < 0 else '#86efac'};">{prefix}{amount_display}</div>
                        <span class="tag {badge_class}">{row.category_type.capitalize()}</span>
                    </div>
                </div>
                {'<div style="margin-top:0.45rem;font-size:0.78rem;color:#cbd5f5;">' + row.notes + '</div>' if row.notes else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_daily_digest(df: pd.DataFrame, base_currency: str) -> None:
    st.markdown("### Diario inteligente")
    available_dates = sorted(df["date"].unique(), reverse=True)
    if not available_dates:
        st.caption("Sin movimientos para resumir.")
        return

    format_date = lambda d: pd.to_datetime(d).strftime("%d %b %Y")
    default_idx = 0
    if st.session_state.get("daily_digest_date") in available_dates:
        default_idx = available_dates.index(st.session_state.daily_digest_date)

    selected_date = st.selectbox(
        "Seleccioná un día",
        options=available_dates,
        format_func=format_date,
        index=default_idx,
        key="daily_digest_date",
    )

    day_df = df[df["date"] == selected_date]
    if day_df.empty:
        st.caption("Sin movimientos en el día seleccionado.")
        return

    incomes = day_df[day_df["category_type"] == "income"]["value"].sum()
    expenses = day_df[day_df["category_type"] == "expense"]["value"].sum()
    net = day_df["signed_value"].sum()

    st.markdown(
        f"""
        <div class="subtle-card" style="margin-bottom:0.8rem;">
            <div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;">
                <div>
                    <div class="app-card__title">Ingresos</div>
                    <div class="app-card__value" style="font-size:1.4rem;">{format_currency(incomes, base_currency)}</div>
                </div>
                <div>
                    <div class="app-card__title">Gastos</div>
                    <div class="app-card__value" style="font-size:1.4rem;">{format_currency(expenses, base_currency)}</div>
                </div>
                <div>
                    <div class="app-card__title">Diferencial</div>
                    <div class="app-card__value" style="font-size:1.4rem;">{format_currency(net, base_currency)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    grouped = (
        day_df.groupby("category_name")["value"].sum().sort_values(ascending=False)
    )
    for category, value in grouped.items():
        st.markdown(
            f"<div class='category-chip'>{category}<span style='opacity:0.7;'>· {format_currency(value, base_currency)}</span></div>",
            unsafe_allow_html=True,
        )
def transaction_form(category_map: Dict[int, Dict[str, Any]]) -> None:
    st.markdown("## Registrar movimiento")
    accounts = st.session_state.accounts
    if not accounts:
        st.warning("Necesitás crear al menos una cuenta antes de cargar transacciones.")
        return

    categories = st.session_state.categories
    parent_options = ["Sin categoría"] + [c["name"] for c in categories]

    with st.form("transaction_form"):
        st.markdown("### Datos principales")
        col_account, col_currency, col_rate = st.columns((2.2, 1, 1))
        account = col_account.selectbox(
            "Cuenta",
            options=accounts,
            format_func=lambda item: f"{item['name']} ({item['currency_code']})",
        )
        currency = col_currency.selectbox("Moneda", ["ARS", "USD", "BTC"], index=0)
        rate_type = col_rate.selectbox("Tipo de cambio", ["official", "blue"], index=0)

        col_amount, col_date, col_time = st.columns((1.6, 1, 1))
        amount = col_amount.number_input("Monto", min_value=0.0, step=0.01)
        date_value = col_date.date_input("Fecha", value=datetime.now().date())
        time_value = col_time.time_input("Hora", value=datetime.now().time())

        st.markdown("### Clasificación")
        col_parent, col_sub = st.columns(2)
        selected_parent = col_parent.selectbox("Categoría", options=parent_options)
        parent_id = None
        current_parent = None
        if selected_parent != "Sin categoría":
            current_parent = next((cat for cat in categories if cat["name"] == selected_parent), None)
            parent_id = current_parent["id"] if current_parent else None

        sub_options = ["Sin subcategoría"]
        if current_parent:
            sub_options += [child["name"] for child in current_parent.get("children", [])]

        selected_sub = col_sub.selectbox("Subcategoría", options=sub_options)
        sub_id = None
        if selected_sub != "Sin subcategoría" and current_parent:
            sub_child = next((child for child in current_parent.get("children", []) if child["name"] == selected_sub), None)
            sub_id = sub_child["id"] if sub_child else None

        notes = st.text_area("Notas", max_chars=300, placeholder="Detalles opcionales, referencia o número de comprobante")

        preview_container = st.empty()
        col_preview, col_submit = st.columns(2)
        preview_clicked = col_preview.form_submit_button("Previsualizar conversión", type="secondary")
        submit_clicked = col_submit.form_submit_button("Guardar movimiento")

        if preview_clicked:
            rates = st.session_state.latest_rates
            if not rates:
                preview_container.warning("Esperando cotizaciones. Intentá nuevamente en unos segundos.")
            else:
                amount_decimal = Decimal(str(amount or 0))
                if currency == "ARS":
                    usd_rate = Decimal(str(rates["usd_ars_blue"])) if rate_type == "blue" and rates.get("usd_ars_blue") else Decimal(str(rates["usd_ars_oficial"]))
                    amount_ars = amount_decimal
                    amount_usd = amount_decimal / usd_rate if usd_rate else Decimal("0")
                    amount_btc = amount_decimal / Decimal(str(rates["btc_ars"])) if rates.get("btc_ars") else Decimal("0")
                elif currency == "USD":
                    usd_rate = Decimal(str(rates["usd_ars_blue"])) if rate_type == "blue" and rates.get("usd_ars_blue") else Decimal(str(rates["usd_ars_oficial"]))
                    amount_ars = amount_decimal * usd_rate
                    amount_usd = amount_decimal
                    amount_btc = amount_decimal / Decimal(str(rates["btc_usd"])) if rates.get("btc_usd") else Decimal("0")
                else:
                    amount_btc = amount_decimal
                    amount_usd = amount_decimal * Decimal(str(rates["btc_usd"])) if rates.get("btc_usd") else Decimal("0")
                    amount_ars = amount_decimal * Decimal(str(rates["btc_ars"])) if rates.get("btc_ars") else Decimal("0")

                preview_container.success(
                    f"ARS: {amount_ars:,.2f} · USD: {amount_usd:,.4f} · BTC: {amount_btc:,.6f}"
                )

        if submit_clicked:
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
            set_flash("Movimiento guardado", "success")
            st.rerun()


def transactions_view(category_map: Dict[int, Dict[str, Any]]) -> None:
    st.markdown("## Movimientos")
    transactions = st.session_state.transactions
    if not transactions:
        st.info("No hay movimientos todavía.")
        return

    base_currency = st.session_state.dashboard_base_currency
    accounts_lookup = {acc["id"]: acc["name"] for acc in st.session_state.accounts}

    df_raw = pd.DataFrame(transactions)
    df_raw["transaction_date"] = pd.to_datetime(df_raw["transaction_date"])
    df_raw["date"] = df_raw["transaction_date"].dt.date
    prepared = prepare_transactions_dataframe(transactions, base_currency, category_map)

    df_raw["category_name"] = prepared["category_name"]
    df_raw["category_type"] = prepared["category_type"]
    df_raw["base_value"] = prepared["value"]
    df_raw["signed_value"] = prepared["signed_value"]
    df_raw["subcategory_name"] = df_raw["subcategory_id"].map(lambda cid: category_map.get(cid, {}).get("name"))
    df_raw["account_name"] = df_raw["account_id"].map(lambda aid: accounts_lookup.get(aid, "Cuenta"))

    min_date = df_raw["date"].min()
    max_date = df_raw["date"].max()

    col_a, col_b, col_c = st.columns(3)
    start_date = col_a.date_input("Desde", value=min_date, min_value=min_date, max_value=max_date)
    end_date = col_b.date_input("Hasta", value=max_date, min_value=min_date, max_value=max_date)
    type_options = sorted(df_raw["category_type"].unique())
    selected_types = col_c.multiselect("Tipo", options=type_options, default=type_options)

    col_d, col_e = st.columns(2)
    category_options = sorted(set(df_raw["category_name"]))
    selected_categories = col_d.multiselect("Categorías", options=category_options)
    account_options = sorted(set(df_raw["account_name"]))
    selected_accounts = col_e.multiselect("Cuentas", options=account_options)

    mask = (df_raw["date"] >= start_date) & (df_raw["date"] <= end_date)
    if selected_types:
        mask &= df_raw["category_type"].isin(selected_types)
    if selected_categories:
        mask &= df_raw["category_name"].isin(selected_categories)
    if selected_accounts:
        mask &= df_raw["account_name"].isin(selected_accounts)

    filtered = df_raw[mask].copy().sort_values("transaction_date", ascending=False)

    total_income = filtered[filtered["category_type"] == "income"]["base_value"].sum()
    total_expense = filtered[filtered["category_type"] == "expense"]["base_value"].sum()
    net_total = filtered["signed_value"].sum()

    metrics = st.columns(3)
    metrics[0].metric("Ingresos", format_currency(total_income, base_currency))
    metrics[1].metric("Gastos", format_currency(total_expense, base_currency))
    metrics[2].metric("Resultado", format_currency(net_total, base_currency))

    daily = (
        filtered.groupby("date")["signed_value"].sum().reset_index()
        if not filtered.empty
        else pd.DataFrame({"date": [], "signed_value": []})
    )
    if not daily.empty:
        daily_chart = (
            alt.Chart(daily)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("date:T", title="Fecha"),
                y=alt.Y("signed_value:Q", title=f"Saldo ({base_currency})"),
                color=alt.condition("datum.signed_value > 0", alt.value("#22d3ee"), alt.value("#fb7185")),
                tooltip=[
                    alt.Tooltip("date:T", title="Fecha"),
                    alt.Tooltip("signed_value:Q", title="Saldo", format=",.2f"),
                ],
            )
            .properties(height=280)
        )
        st.altair_chart(daily_chart, use_container_width=True)

    display_cols = [
        "transaction_date",
        "account_name",
        "category_name",
        "subcategory_name",
        "currency_code",
        "amount_original",
        "base_value",
        "notes",
    ]
    df_display = filtered[display_cols].rename(
        columns={
            "transaction_date": "Fecha",
            "account_name": "Cuenta",
            "category_name": "Categoría",
            "subcategory_name": "Subcategoría",
            "currency_code": "Moneda",
            "amount_original": "Monto original",
            "base_value": f"Monto en {base_currency}",
            "notes": "Notas",
        }
    )
    st.dataframe(df_display, use_container_width=True)


def categories_view() -> None:
    st.markdown("## Categorías & subcategorías")
    categories = st.session_state.categories

    col_tree, col_forms = st.columns((1.8, 1.2))

    with col_tree:
        st.markdown("### Mapa de categorías")
        if not categories:
            st.info("Aún no configuraste categorías. Creá la primera desde la derecha.")
        else:
            for category in categories:
                badge = f"<span class='tag'>{category['type'].capitalize()}</span>"
                with st.expander(f"{category['name']} {badge}", expanded=False):
                    children = category.get("children", [])
                    if children:
                        chips = "".join(
                            f"<span class='category-chip'>{child['name']}</span>" for child in children
                        )
                        st.markdown(chips, unsafe_allow_html=True)
                    else:
                        st.caption("Sin subcategorías todavía.")

                    with st.form(f"add_sub_{category['id']}"):
                        sub_name = st.text_input("Nueva subcategoría", key=f"sub_name_{category['id']}")
                        if st.form_submit_button("Agregar subcategoría") and sub_name:
                            payload = {"name": sub_name, "type": category["type"], "parent_id": category["id"]}
                            handle_api_call(
                                lambda: st.session_state.api_client.create_category(payload),
                                "Subcategoría creada",
                            )
                            st.rerun()

    with col_forms:
        st.markdown("### Crear nueva categoría")
        with st.form("create_category_form"):
            name = st.text_input("Nombre")
            category_type = st.selectbox("Tipo", ["income", "expense", "transfer"], index=1)
            if st.form_submit_button("Guardar categoría") and name:
                payload = {"name": name, "type": category_type, "parent_id": None}
                handle_api_call(
                    lambda: st.session_state.api_client.create_category(payload),
                    "Categoría creada",
                )
                st.rerun()

        if categories:
            st.markdown("### Crear subcategoría rápida")
            with st.form("quick_subcategory_form"):
                parent_lookup = {c["name"]: c for c in categories}
                parent_name = st.selectbox("Categoría padre", list(parent_lookup.keys()))
                sub_name = st.text_input("Nombre de la subcategoría")
                if st.form_submit_button("Crear subcategoría") and sub_name:
                    parent = parent_lookup[parent_name]
                    payload = {"name": sub_name, "type": parent["type"], "parent_id": parent["id"]}
                    handle_api_call(
                        lambda: st.session_state.api_client.create_category(payload),
                        "Subcategoría creada",
                    )
                    st.rerun()


def accounts_view() -> None:
    st.markdown("## Cuentas")
    accounts = st.session_state.accounts
    if accounts:
        rows = [accounts[i : i + 3] for i in range(0, len(accounts), 3)]
        for row in rows:
            cols = st.columns(len(row))
            for col, account in zip(cols, row):
                status = "Archivada" if account["is_archived"] else "Activa"
                col.markdown(
                    f"""
                    <div class="app-card">
                        <div class="app-card__title">{account['currency_code']}</div>
                        <div class="app-card__value" style="font-size:1.6rem;">{account['name']}</div>
                        <div style="color:#94a3b8;font-size:0.8rem;margin-top:0.4rem;">{account.get('description') or 'Sin descripción'}</div>
                        <div style="margin-top:0.6rem;" class="tag">{status}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Sin cuentas registradas aún")

    st.markdown("### Agregar cuenta")
    with st.form("new_account"):
        name = st.text_input("Nombre de la cuenta")
        currency = st.selectbox("Moneda", ["ARS", "USD", "BTC"])
        description = st.text_input("Descripción (opcional)")
        if st.form_submit_button("Crear cuenta") and name:
            payload = {"name": name, "currency_code": currency, "description": description or None}
            handle_api_call(lambda: st.session_state.api_client.create_account(payload), "Cuenta creada")
            st.rerun()


def app() -> None:
    st.set_page_config(page_title="FinTrack", layout="wide", page_icon="💸")
    init_session_state()
    load_custom_css()
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
