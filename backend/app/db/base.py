from app.db.base_class import Base  # noqa: F401

# Import models here so Alembic can detect them
from app.models.user import User  # noqa: F401
from app.models.currency import Currency  # noqa: F401
from app.models.exchange_rate import ExchangeRate, ExchangeRateSource  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.account import Account  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.budget import Budget, BudgetItem  # noqa: F401
