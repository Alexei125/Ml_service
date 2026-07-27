"""
Роутер для ML-предсказаний
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories import (
    ModelRepository,
    HistoryRepository,
    WalletRepository,
    InsufficientBalanceError,
)
from ..schemas import PredictRequest, PredictResponse
from ..auth import get_current_user
from ..orm_models import DBUser

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("/", response_model=PredictResponse)
def predict(
    request: PredictRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Выполнить ML-предсказание."""
    try:
        # Получаем активную модель
        model_repo = ModelRepository(db)
        model = model_repo.get_active_model()
        if not model:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No active model found")

        # Проверяем баланс
        cost = 1.0
        if current_user.wallet.balance < cost:
            raise InsufficientBalanceError(
                f"Need {cost} credits, have {current_user.wallet.balance}"
            )

        # Имитируем предсказание
        # В реальности здесь вызывается ML модель
        result = {"class": "spam", "confidence": 0.95}

        # Списываем средства
        wallet_repo = WalletRepository(db)
        transaction = wallet_repo.deduct_balance(
            current_user.user_id, cost, f"Prediction: {model.name} (v{model.version})"
        )

        # Сохраняем историю
        history_repo = HistoryRepository(db)
        history = history_repo.create_prediction_history(
            user_id=current_user.user_id,
            model_id=model.model_id,
            input_data=request.data,
            output_data=result,
            cost=cost,
            duration_ms=0.0,
            transaction_id=transaction.transaction_id,
        )

        return {
            "success": True,
            "result": result,
            "credits_used": cost,
            "credits_remaining": current_user.wallet.balance,
        }

    except InsufficientBalanceError as e:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
