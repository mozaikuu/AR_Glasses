from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.core.i18n import response_payload
from app.db.models import Student, WalletTransaction
from app.schemas.wallet import WalletAddRequest, WalletPayRequest
from app.services.wallet_service import add_balance, pay


router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.post("/add")
def wallet_add_balance(
    payload: WalletAddRequest,
    lang: str = "en",
    db: Session = Depends(db_session),
):
    student, transaction = add_balance(db, payload.student_id, payload.amount)
    if not student or not transaction:
        raise HTTPException(status_code=404, detail="Student not found")

    return response_payload(
        {
            "student_id": student.id,
            "new_balance": student.wallet_balance,
            "transaction_id": transaction.id,
        },
        en="Wallet balance added successfully.",
        ar="تمت إضافة رصيد المحفظة بنجاح.",
        lang=lang,
    )


@router.post("/pay")
def wallet_pay(
    payload: WalletPayRequest,
    lang: str = "en",
    db: Session = Depends(db_session),
):
    student, transaction = pay(
        db,
        student_id=payload.student_id,
        amount=payload.amount,
        payment_type=payload.payment_type,
        force_fail=payload.force_fail,
    )

    if not student or not transaction:
        raise HTTPException(status_code=404, detail="Student not found")

    return response_payload(
        {
            "student_id": student.id,
            "remaining_balance": student.wallet_balance,
            "transaction_id": transaction.id,
            "status": transaction.status,
            "description": transaction.description,
            "payment_type": payload.payment_type,
        },
        en="Wallet payment processed.",
        ar="تمت معالجة الدفع من المحفظة.",
        lang=lang,
    )


@router.get("/history")
def wallet_history(
    student_id: int = Query(...),
    lang: str = "en",
    db: Session = Depends(db_session),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    tx_rows = db.scalars(
        select(WalletTransaction)
        .where(WalletTransaction.student_id == student_id)
        .order_by(WalletTransaction.created_at.desc())
    ).all()

    return response_payload(
        {
            "student_id": student.id,
            "student_name": student.name,
            "balance": student.wallet_balance,
            "transactions": [
                {
                    "id": tx.id,
                    "type": tx.transaction_type,
                    "amount": tx.amount,
                    "status": tx.status,
                    "description": tx.description,
                    "created_at": tx.created_at.isoformat(),
                }
                for tx in tx_rows
            ],
        },
        en="Wallet history retrieved.",
        ar="تم جلب سجل المحفظة.",
        lang=lang,
    )


@router.get("/balance")
def wallet_balance(
    student_id: int = Query(...),
    lang: str = "en",
    db: Session = Depends(db_session),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return response_payload(
        {
            "student_id": student.id,
            "student_name": student.name,
            "balance": student.wallet_balance,
            "subscription_status": student.subscription_status,
            "subscription_expires_at": (
                student.subscription_expires_at.isoformat() if student.subscription_expires_at else None
            ),
        },
        en="Wallet balance fetched.",
        ar="تم جلب رصيد المحفظة.",
        lang=lang,
    )
