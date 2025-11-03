from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_category
from app.db.session import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


def _to_schema(category: Category) -> CategoryOut:
    return CategoryOut.model_validate(
        {
            "id": category.id,
            "name": category.name,
            "type": category.type,
            "parent_id": category.parent_id,
            "is_default": category.is_default,
            "is_archived": category.is_archived,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "children": [_to_schema(child) for child in category.children],
        }
    )


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> list[CategoryOut]:
    categories = crud_category.list_categories(db, current_user.id)
    return [_to_schema(category) for category in categories]


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> CategoryOut:
    parent = None
    if category_in.parent_id is not None:
        parent = crud_category.get_category(db, current_user.id, category_in.parent_id)
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría padre no encontrada")
        if parent.type != category_in.type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El tipo debe coincidir con el padre")
    category = crud_category.create_category(db, current_user.id, category_in)
    return _to_schema(category)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> CategoryOut:
    category = crud_category.get_category(db, current_user.id, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")

    if category_in.parent_id is not None and category_in.parent_id == category_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Una categoría no puede ser su propio padre")

    if category_in.parent_id is not None:
        parent = crud_category.get_category(db, current_user.id, category_in.parent_id)
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría padre no encontrada")
        if category_in.type is not None and parent.type != category_in.type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El tipo debe coincidir con el padre")

    updated = crud_category.update_category(db, category, category_in)
    return _to_schema(updated)
