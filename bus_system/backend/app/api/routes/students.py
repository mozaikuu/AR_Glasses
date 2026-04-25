from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.core.config import settings
from app.core.i18n import response_payload
from app.db.models import Student, WalletTransaction
from app.schemas.student import SubscriptionRequest


router = APIRouter(prefix="/students", tags=["Students"])


@router.get("")
def list_students(lang: str = "en", db: Session = Depends(db_session)):
    students = db.scalars(select(Student).order_by(Student.id)).all()
    return response_payload(
        {
            "students": [
                {
                    "id": student.id,
                    "name": student.name,
                    "home_location": student.home_location,
                    "home": {"lat": student.home_lat, "lng": student.home_lng},
                    "wallet_balance": student.wallet_balance,
                    "subscription_status": student.subscription_status,
                }
                for student in students
            ]
        },
        en="Students loaded successfully.",
        ar="تم تحميل بيانات الطلاب بنجاح.",
        lang=lang,
    )


@router.post("/{student_id}/subscribe")
def subscribe_student(
    student_id: int,
    payload: SubscriptionRequest,
    lang: str = "en",
    db: Session = Depends(db_session),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    amount = settings.monthly_subscription_fee_egp * payload.months
    if student.wallet_balance < amount:
        return response_payload(
            {
                "student_id": student.id,
                "required_amount": amount,
                "balance": student.wallet_balance,
                "status": "failed",
            },
            en="Subscription failed: insufficient wallet balance.",
            ar="فشل الاشتراك: الرصيد غير كافٍ.",
            lang=lang,
        )

    student.wallet_balance = round(student.wallet_balance - amount, 2)
    student.subscription_status = "active"
    base_date = student.subscription_expires_at or datetime.utcnow()
    student.subscription_expires_at = base_date + timedelta(days=30 * payload.months)

    tx = WalletTransaction(
        student_id=student.id,
        transaction_type="subscription",
        amount=amount,
        status="success",
        description=f"Subscription paid for {payload.months} month(s)",
    )

    db.add(tx)
    db.commit()
    db.refresh(student)
    db.refresh(tx)

    return response_payload(
        {
            "student_id": student.id,
            "status": "success",
            "months": payload.months,
            "charged": amount,
            "new_balance": student.wallet_balance,
            "subscription_expires_at": (
                student.subscription_expires_at.isoformat() if student.subscription_expires_at else None
            ),
            "transaction_id": tx.id,
        },
        en="Subscription completed successfully.",
        ar="تم الاشتراك بنجاح.",
        lang=lang,
    )
