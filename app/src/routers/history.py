"""
Роутер для истории
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories import HistoryRepository
from ..schemas import PredictionHistoryResponse
from ..auth import get_current_user
from ..orm_models import DBUser

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/predictions", response_model=list[PredictionHistoryResponse])
def get_prediction_history(
    limit: int = 20,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить историю предсказаний текущего пользователя."""
    history_repo = HistoryRepository(db)
    history = history_repo.get_user_history(current_user.user_id, limit)

    return [
        {
            "id": h.history_id,
            "model_id": h.model_id,
            "input": h.input_data,
            "output": h.output_data,
            "cost": h.cost,
            "timestamp": h.timestamp,
        }
        for h in history
    ]
