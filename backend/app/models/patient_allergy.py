from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.allergen import Allergen
    from app.models.patient import Patient


class PatientAllergy(Base):
    __tablename__ = "patient_allergies"

    patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("patients.id"), primary_key=True
    )
    allergen_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("allergens.id"), primary_key=True
    )
    patient: Mapped["Patient"] = relationship(back_populates="allergies")
    allergen: Mapped["Allergen"] = relationship(lazy="joined")
