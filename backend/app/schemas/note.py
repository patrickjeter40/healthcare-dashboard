from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NoteWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=5000)

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
