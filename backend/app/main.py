from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import accounts, auth, budgets, categories, exchange_rates, reports, transactions, users
from app.db import base  # noqa: F401 - ensure models are registered
from app.core.config import settings
from app.worker.scheduler import shutdown_scheduler, start_scheduler

app = FastAPI(title="Finance Tracker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(exchange_rates.router)
app.include_router(reports.router)
app.include_router(budgets.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup() -> None:
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    shutdown_scheduler()
