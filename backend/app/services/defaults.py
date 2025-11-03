from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.crud import crud_account, crud_category
from app.models.category import CategoryType
from app.schemas.account import AccountCreate
from app.schemas.category import CategoryCreate


@dataclass(frozen=True)
class DefaultCategory:
    name: str
    type: CategoryType
    children: tuple["DefaultCategory", ...] = ()


DEFAULT_ACCOUNTS: tuple[AccountCreate, ...] = (
    AccountCreate(name="Efectivo ARS", currency_code="ARS", description="Efectivo disponible"),
    AccountCreate(name="Cuenta Bancaria USD", currency_code="USD", description="Caja de ahorro en USD"),
    AccountCreate(name="Wallet BTC", currency_code="BTC", description="Wallet de resguardo"),
)

DEFAULT_CATEGORIES: tuple[DefaultCategory, ...] = (
    DefaultCategory(name="Salario", type=CategoryType.INCOME),
    DefaultCategory(name="Honorarios", type=CategoryType.INCOME),
    DefaultCategory(name="Rentas", type=CategoryType.INCOME),
    DefaultCategory(name="Devoluciones", type=CategoryType.INCOME),
    DefaultCategory(name="Otros", type=CategoryType.INCOME),
    DefaultCategory(
        name="Hogar",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Alquiler", type=CategoryType.EXPENSE),
            DefaultCategory(name="Servicios", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(
        name="Comida",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Supermercado", type=CategoryType.EXPENSE),
            DefaultCategory(name="Delivery", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(
        name="Transporte",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Transporte Público", type=CategoryType.EXPENSE),
            DefaultCategory(name="Combustible", type=CategoryType.EXPENSE),
            DefaultCategory(name="Mantenimiento", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(
        name="Salud",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Obra Social", type=CategoryType.EXPENSE),
            DefaultCategory(name="Medicamentos", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(
        name="Educación",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Cursos", type=CategoryType.EXPENSE),
            DefaultCategory(name="Libros", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(
        name="Ocio",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Salidas", type=CategoryType.EXPENSE),
            DefaultCategory(name="Streaming", type=CategoryType.EXPENSE),
            DefaultCategory(name="Viajes", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(
        name="Finanzas",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Tarjeta Crédito", type=CategoryType.EXPENSE),
            DefaultCategory(name="Impuestos", type=CategoryType.EXPENSE),
            DefaultCategory(name="Comisiones Bancarias", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(
        name="Tecnología",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Suscripciones", type=CategoryType.EXPENSE),
            DefaultCategory(name="Hardware", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(
        name="Ahorro/Inversión",
        type=CategoryType.EXPENSE,
        children=(
            DefaultCategory(name="Compra USD", type=CategoryType.EXPENSE),
            DefaultCategory(name="Compra BTC", type=CategoryType.EXPENSE),
        ),
    ),
    DefaultCategory(name="Misceláneos", type=CategoryType.EXPENSE),
)


def _create_category_tree(
    db: Session,
    user_id: int,
    defaults: Iterable[DefaultCategory],
    parent_id: int | None = None,
) -> None:
    for item in defaults:
        category = crud_category.create_category(
            db,
            user_id=user_id,
            category_in=CategoryCreate(name=item.name, type=item.type, parent_id=parent_id),
            is_default=True,
        )
        if item.children:
            _create_category_tree(db, user_id, item.children, parent_id=category.id)


def seed_defaults_for_user(db: Session, user_id: int) -> None:
    # Avoid duplicating defaults if they already exist
    existing = crud_category.list_categories(db, user_id)
    if existing:
        return

    _create_category_tree(db, user_id, DEFAULT_CATEGORIES)

    for account in DEFAULT_ACCOUNTS:
        crud_account.create_account(db, user_id=user_id, account_in=account, is_default=True)
