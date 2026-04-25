from pydantic import BaseModel, Field


class SubscriptionRequest(BaseModel):
    months: int = Field(default=1, ge=1, le=12)
