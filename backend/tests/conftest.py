import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.currency import Currency
from app.models.exchange_rate import ExchangeRateSource
from app.worker import scheduler as scheduler_module

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_static_data(session: Session) -> None:
    if not session.query(Currency).count():
        session.add_all(
            [
                Currency(code="ARS", name="Peso Argentino", symbol="$"),
                Currency(code="USD", name="Dólar estadounidense", symbol="USD"),
                Currency(code="BTC", name="Bitcoin", symbol="BTC"),
            ]
        )
    if not session.query(ExchangeRateSource).count():
        session.add_all(
            [
                ExchangeRateSource(name="DolarAPI", base_url=str(settings.dolar_api_url)),
                ExchangeRateSource(name="Coingecko", base_url=str(settings.coingecko_api_url)),
            ]
        )
    session.commit()


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> None:
    Base.metadata.create_all(bind=engine)
    try:
        session = TestingSessionLocal()
        seed_static_data(session)
    finally:
        session.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        seed_static_data(session)
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    monkeypatch.setattr(scheduler_module, "start_scheduler", lambda: None)
    monkeypatch.setattr(scheduler_module, "shutdown_scheduler", lambda: None)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
