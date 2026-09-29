from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, field_validator


class PatientStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    discharged = "discharged"


class BloodType(str, Enum):
    a_positive = "A+"
    a_negative = "A-"
    b_positive = "B+"
    b_negative = "B-"
    ab_positive = "AB+"
    ab_negative = "AB-"
    o_positive = "O+"
    o_negative = "O-"


class PatientWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    address_line_1: str | None = Field(default=None, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    blood_type: BloodType | None = None
    status: PatientStatus
    last_visit_at: AwareDatetime | None = None
    allergies: list[str] = Field(default_factory=list, max_length=30)
    conditions: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("first_name", "last_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator(
        "phone", "address_line_1", "address_line_2", "city", "state", "postal_code", mode="before"
    )
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("date_of_birth")
    @classmethod
    def birth_date_not_future(cls, value: date) -> date:
        if value > datetime.now(timezone.utc).date():
            raise ValueError("date of birth cannot be in the future")
        return value

    @field_validator("last_visit_at")
    @classmethod
    def last_visit_not_future(cls, value: datetime | None) -> datetime | None:
        if value is not None and value > datetime.now(timezone.utc):
            raise ValueError("last visit cannot be in the future")
        return value

    @field_validator("allergies", "conditions")
    @classmethod
    def clean_terms(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value or len(value) > 120 for value in cleaned):
            raise ValueError("each item must contain 1 to 120 characters")
        if len({value.casefold() for value in cleaned}) != len(cleaned):
            raise ValueError("duplicate items are not allowed")
        return cleaned


class PatientRead(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    age: int
    email: EmailStr | None
    phone: str | None
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    blood_type: BloodType | None
    status: PatientStatus
    last_visit_at: datetime | None
    created_at: datetime
    updated_at: datetime
    allergies: list[str]
    conditions: list[str]


class PatientPage(BaseModel):
    items: list[PatientRead]
    page: int
    page_size: int
    total: int
