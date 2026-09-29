from datetime import datetime, timezone
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class NoteWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=5000)
    recorded_at: AwareDatetime | None = None

    @field_validator("recorded_at")
    @classmethod
    def recorded_at_not_future(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            if value > datetime.now(timezone.utc):
                raise ValueError("recorded timestamp cannot be in the future")
            return value.astimezone(timezone.utc)
        return value

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("note content cannot be blank")
        return value


class NoteRead(BaseModel):
    id: UUID
    patient_id: UUID
    content: str
    recorded_at: datetime
    created_at: datetime


class PatientSummary(BaseModel):
    patient_id: UUID
    summary: str
