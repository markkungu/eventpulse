from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    type: str = Field(..., examples=["user.signup", "payment.completed", "order.created"])
    source: str = Field(..., examples=["web", "mobile", "api"])
    payload: dict = Field(default_factory=dict)


class EventQueued(BaseModel):
    event_id: UUID
    status: str = "queued"


class EventResponse(BaseModel):
    event_id: UUID
    type: str
    source: str
    payload: dict
    status: str
    result: dict | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}
