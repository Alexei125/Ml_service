"""
Роутер для работы с балансом
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories import WalletRepository
from ..schemas import BalanceDepositRequest, BalanceDepositResponse, TransactionResponse
from ..auth import get_current_user
from ..orm_models import DBUser

router = APIRouter(prefix="/balance", tags=["balance"])


@router.post("/deposit", response_model=BalanceDepositResponse)
def deposit(
    request: BalanceDepositRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Пополнить баланс текущего пользователя."""
    try:
        wallet_repo = WalletRepository(db)
        transaction = wallet_repo.add_balance(
            current_user.user_id, request.amount, "Пополнение баланса"
        )

        return {
            "success": True,
            "amount": request.amount,
            "new_balance": current_user.wallet.balance,
            "transaction_id": transaction.transaction_id,
        }
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
    limit: int = 20,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить историю транзакций текущего пользователя."""
    wallet_repo = WalletRepository(db)
    transactions = wallet_repo.get_transactions(current_user.user_id, limit)

    return [
        {
            "transaction_id": tx.transaction_id,
            "amount": tx.amount,
            "type": tx.type.value,
            "description": tx.description,
            "timestamp": tx.timestamp,
            "balance_after": tx.balance_after,
        }
        for tx in transactions
    ]
