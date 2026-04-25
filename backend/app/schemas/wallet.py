from typing import Literal

from pydantic import BaseModel, Field


class WalletAddRequest(BaseModel):
    student_id: int
    amount: float = Field(gt=0)


class WalletPayRequest(BaseModel):
    student_id: int
    amount: float = Field(gt=0)
    payment_type: Literal["trip", "subscription"] = "trip"
    force_fail: bool = False
