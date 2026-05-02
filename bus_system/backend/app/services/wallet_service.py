from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Student, WalletTransaction


def _append_usage_history(student: Student, payload: dict[str, Any]) -> None:
    history = list(student.usage_history or [])
    history.append(payload)
    student.usage_history = history[-120:]


def add_balance(db: Session, student_id: int, amount: float) -> tuple[Student | None, WalletTransaction | None]:
    student = db.get(Student, student_id)
    if not student:
        return None, None

    student.wallet_balance = round(student.wallet_balance + amount, 2)
    transaction = WalletTransaction(
        student_id=student.id,
        transaction_type="add_balance",
        amount=amount,
        status="success",
        description="Wallet top-up completed",
    )

    db.add(transaction)
    db.commit()
    db.refresh(student)
    db.refresh(transaction)
    return student, transaction


def pay(
    db: Session,
    student_id: int,
    amount: float,
    payment_type: str,
    force_fail: bool = False,
) -> tuple[Student | None, WalletTransaction | None]:
    student = db.get(Student, student_id)
    if not student:
        return None, None

    random_failure = random.random() < 0.1
    insufficient = student.wallet_balance < amount
    failed = force_fail or insufficient or random_failure

    status = "failed" if failed else "success"
    description = "Payment failed"

    if failed:
        if insufficient:
            description = "Payment failed: insufficient balance"
        elif force_fail:
            description = "Payment failed: simulated failure"
        else:
            description = "Payment failed: gateway timeout simulation"
    else:
        student.wallet_balance = round(student.wallet_balance - amount, 2)
        if payment_type == "subscription":
            student.subscription_status = "active"
            base_date = student.subscription_expires_at or datetime.utcnow()
            student.subscription_expires_at = base_date + timedelta(days=30)
            description = "Monthly subscription renewed"
        else:
            _append_usage_history(
                student,
                {
                    "trip_paid_at": datetime.utcnow().isoformat(),
                    "amount": amount,
                    "note": "Trip fare deducted",
                },
            )
            description = "Trip fare paid"

    transaction = WalletTransaction(
        student_id=student.id,
        transaction_type=f"pay_{payment_type}",
        amount=amount,
        status=status,
        description=description,
    )

    db.add(transaction)
    db.commit()
    db.refresh(student)
    db.refresh(transaction)
    return student, transaction
