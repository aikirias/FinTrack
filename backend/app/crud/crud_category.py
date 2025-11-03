from sqlalchemy.orm import Session

from app.models.category import Category, CategoryType
from app.schemas.category import CategoryCreate, CategoryUpdate


def list_categories(db: Session, user_id: int) -> list[Category]:
    return (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.parent_id.is_(None))
        .order_by(Category.type, Category.name)
        .all()
    )


def get_category(db: Session, user_id: int, category_id: int) -> Category | None:
    return (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.id == category_id)
        .first()
    )


def create_category(
    db: Session, user_id: int, category_in: CategoryCreate, is_default: bool = False
) -> Category:
    type_value = category_in.type
    if isinstance(type_value, CategoryType):
        db_type = type_value.value
    elif isinstance(type_value, str):
        try:
            db_type = CategoryType(type_value).value
        except ValueError:
            db_type = CategoryType[type_value].value if type_value in CategoryType.__members__ else type_value
    else:
        db_type = str(type_value)

    category = Category(
        user_id=user_id,
        name=category_in.name,
        type=db_type,
        parent_id=category_in.parent_id,
        is_default=is_default,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category: Category, category_in: CategoryUpdate) -> Category:
    data = category_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field == "type" and value is not None:
            if isinstance(value, CategoryType):
                value = value.value
            elif isinstance(value, str):
                try:
                    value = CategoryType(value).value
                except ValueError:
                    value = CategoryType[value].value if value in CategoryType.__members__ else value
            else:
                value = str(value)
        setattr(category, field, value)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def list_subcategories(db: Session, user_id: int, parent_id: int) -> list[Category]:
    return (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.parent_id == parent_id)
        .order_by(Category.name)
        .all()
    )


def ensure_parent_type(parent: Category | None, category_type: CategoryType) -> None:
    if parent and parent.type != category_type:
        raise ValueError("Parent category type mismatch")
