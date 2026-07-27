"""
Роутер для ML-моделей
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories import ModelRepository
from ..schemas import ModelResponse
from ..auth import get_current_user
from ..orm_models import DBUser

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/", response_model=list[ModelResponse])
def list_models(
    current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получить список всех моделей."""
    model_repo = ModelRepository(db)
    models = model_repo.list_models()

    return [
        {
            "id": m.model_id,
            "name": m.name,
            "version": m.version,
            "type": m.model_type.value,
            "active": m.is_active,
        }
        for m in models
    ]
