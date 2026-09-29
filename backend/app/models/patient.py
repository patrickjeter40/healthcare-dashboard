from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.patient_allergy import PatientAllergy
    from app.models.patient_condition import PatientCondition
    from app.models.patient_note import PatientNote


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint("length(btrim(first_name)) > 0", name="first_name_not_blank"),
        CheckConstraint("length(btrim(last_name)) > 0", name="last_name_not_blank"),
        CheckConstraint("status IN ('active', 'inactive', 'discharged')", name="status_allowed"),
        CheckConstraint(
            "blood_type IS NULL OR blood_type IN "
            "('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="blood_type_allowed",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(40))
    address_line_1: Mapped[str | None] = mapped_column(String(200))
    address_line_2: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    blood_type: Mapped[str | None] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_visit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    allergies: Mapped[list["PatientAllergy"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", lazy="selectin"
    )
    conditions: Mapped[list["PatientCondition"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", lazy="selectin"
    )
    notes: Mapped[list["PatientNote"]] = relationship(back_populates="patient")
