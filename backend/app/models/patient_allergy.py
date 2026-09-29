from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class PatientAllergy(Base):
    __tablename__ = "patient_allergies"
    __table_args__ = (
        UniqueConstraint("patient_id", "allergen", name="uq_patient_allergies_patient_allergen"),
        CheckConstraint("length(btrim(allergen)) > 0", name="allergen_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    allergen: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient: Mapped["Patient"] = relationship(back_populates="allergies")
