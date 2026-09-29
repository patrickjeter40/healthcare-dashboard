from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.condition import Condition
    from app.models.patient import Patient


class PatientCondition(Base):
    __tablename__ = "patient_conditions"

    patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("patients.id"), primary_key=True
    )
    condition_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("conditions.id"), primary_key=True
    )
    patient: Mapped["Patient"] = relationship(back_populates="conditions")
    condition: Mapped["Condition"] = relationship(lazy="joined")
