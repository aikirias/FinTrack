from app.core.config import Settings


def test_cors_origins_accepts_json_array_format():
    settings = Settings(
        DATABASE_URL="sqlite:///test.db",
        JWT_SECRET="test-secret-with-at-least-32-bytes",
        CORS_ORIGINS='["https://one.example", "https://two.example"]',
    )

    assert settings.cors_origins == ["https://one.example", "https://two.example"]


def test_cors_origins_accepts_comma_separated_format():
    settings = Settings(
        DATABASE_URL="sqlite:///test.db",
        JWT_SECRET="test-secret-with-at-least-32-bytes",
        CORS_ORIGINS="https://one.example, https://two.example",
    )

    assert settings.cors_origins == ["https://one.example", "https://two.example"]


def test_cors_origins_accepts_empty_environment_value(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("JWT_SECRET", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("CORS_ORIGINS", "")

    settings = Settings()

    assert settings.cors_origins == []
