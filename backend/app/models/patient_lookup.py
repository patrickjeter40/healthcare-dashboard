from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PatientStatusLookup(Base):
    __tablename__ = "patient_statuses"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)


class BloodTypeLookup(Base):
    __tablename__ = "blood_types"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
