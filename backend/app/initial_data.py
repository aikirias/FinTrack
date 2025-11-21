from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.crud import crud_account, crud_transaction, crud_user
from app.schemas.transaction import TransactionCreate
from app.schemas.user import UserCreate
from app.services.defaults import seed_defaults_for_user
from app.services.exchange_rates import ensure_daily_exchange_rate
from app.schemas.exchange_rate import ExchangeRateValues
from app.models.category import Category
from app.models.transaction import Transaction

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


def _get_category_maps(session, user_id: int) -> tuple[dict[str, Category], dict[str, Category]]:
    categories = session.query(Category).filter(Category.user_id == user_id).all()
    parents = {cat.name: cat for cat in categories if cat.parent_id is None}
    children = {cat.name: cat for cat in categories if cat.parent_id is not None}
    return parents, children


def seed_demo_user(session: SessionLocal) -> None:
    demo_email = "test@test.com"
    demo_password = "test1234"
    existing = crud_user.get_by_email(session, demo_email)
    if existing:
        user = existing
    else:
        user = crud_user.create_user(session, UserCreate(email=demo_email, password=demo_password, timezone="UTC"))

    # Ensure defaults exist for the user
    seed_defaults_for_user(session, user.id)

    # If already has movements, skip reseeding
    has_tx = session.query(Transaction).filter(Transaction.user_id == user.id).count()
    if has_tx:
        return

    # Ensure we have at least one exchange rate to use for conversions
    rate = ensure_daily_exchange_rate(session)
    rates = ExchangeRateValues(
        usd_ars_oficial=rate.usd_ars_oficial,
        usd_ars_blue=rate.usd_ars_blue,
        btc_usd=rate.btc_usd,
        btc_ars=rate.btc_ars,
    )

    accounts = {acc.currency_code: acc.id for acc in crud_account.list_accounts(session, user.id)}
    ars_acc = accounts.get("ARS")
    usd_acc = accounts.get("USD")
    btc_acc = accounts.get("BTC")
    parent_map, child_map = _get_category_maps(session, user.id)

    def make_tx(date_str: str, account_id: int | None, currency: str, amount: str, category: str | None, subcategory: str | None, notes: str = "") -> None:
        if not account_id:
            return
        cat_id = parent_map.get(category).id if category and parent_map.get(category) else None
        sub_id = child_map.get(subcategory).id if subcategory and child_map.get(subcategory) else None
        tx_in = TransactionCreate(
            transaction_date=datetime.fromisoformat(date_str),
            account_id=account_id,
            currency_code=currency,
            amount_original=amount,
            category_id=cat_id,
            subcategory_id=sub_id,
            notes=notes or None,
        )
        crud_transaction.create_transaction(
            session,
            user_id=user.id,
            tx_in=tx_in,
            rates=rates,
            exchange_rate_id=rate.id,
        )

    # Seed last 12 months of data
    now = datetime.now(tz=timezone.utc).replace(day=1, hour=12, minute=0, second=0, microsecond=0)
    months: list[tuple[int, int]] = []
    for i in range(12):
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        months.append((year, month))
    months = sorted(months)

    for year, month in months:
        def dt(day: int, hour: int = 10) -> str:
            return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc).isoformat()

        # Income
        make_tx(dt(3), usd_acc, \"USD\", \"1000\", \"Salario\", None, \"Salario mensual\")

        # Savings ~100 USD in BTC if available
        if btc_acc:
            make_tx(dt(25), btc_acc, \"BTC\", \"0.0020\", None, None, \"Ahorro BTC\")

        # Housing: rent/expensas
        make_tx(dt(7), ars_acc, \"ARS\", \"350000\", \"Hogar\", \"Alquiler\", \"Alquiler/expensas\")

        # Utilities
        make_tx(dt(8), ars_acc, \"ARS\", \"25000\", \"Servicios\", \"Luz\", \"Luz\")
        make_tx(dt(8), ars_acc, \"ARS\", \"20000\", \"Servicios\", \"Internet\", \"Internet\")

        # Food
        make_tx(dt(12), ars_acc, \"ARS\", \"180000\", \"Comida\", \"Supermercado\", \"Supermercado\")
        make_tx(dt(12), ars_acc, \"ARS\", \"40000\", \"Comida\", \"Restaurantes\", \"Salidas a comer\")

        # Transport
        make_tx(dt(15), ars_acc, \"ARS\", \"30000\", \"Transporte\", \"Transporte público\", \"Transporte público\")

        # Education / entertainment
        make_tx(dt(18), ars_acc, \"ARS\", \"30000\", \"Ocio\", \"Cursos\", \"Cursos/online\")
        make_tx(dt(18), ars_acc, \"ARS\", \"20000\", \"Ocio\", \"Shows\", \"Shows/entretenimiento\")

        # Misc
        make_tx(dt(22), ars_acc, \"ARS\", \"20000\", \"Compras Personales\", \"Perfumería\", \"Perfumería/higiene\")


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

        seed_demo_user(session)
    finally:
        session.close()


if __name__ == "__main__":
    init_default_data()
