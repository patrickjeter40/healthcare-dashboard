from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient, PatientAllergy, PatientCondition
from app.schemas.patient import PatientPage, PatientRead, PatientStatus, PatientWrite

router = APIRouter(prefix="/patients", tags=["patients"])


def active_patients() -> Select[tuple[Patient]]:
    return select(Patient).where(Patient.deleted_at.is_(None))


def get_active_patient(db: Session, patient_id: UUID) -> Patient:
    patient = db.scalar(active_patients().where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def patient_read(patient: Patient) -> PatientRead:
    today = datetime.now(timezone.utc).date()
    born = patient.date_of_birth
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return PatientRead(
        id=patient.id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=born,
        age=age,
        email=patient.email,
        phone=patient.phone,
        address_line_1=patient.address_line_1,
        address_line_2=patient.address_line_2,
        city=patient.city,
        state=patient.state,
        postal_code=patient.postal_code,
        blood_type=patient.blood_type,
        status=patient.status,
        last_visit_at=patient.last_visit_at,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
        allergies=sorted((item.allergen for item in patient.allergies), key=str.casefold),
        conditions=sorted((item.condition for item in patient.conditions), key=str.casefold),
    )


def replace_terms(patient: Patient, values: list[str], attribute: str, model: type) -> None:
    current = getattr(patient, attribute)
    wanted = {value.casefold(): value for value in values}
    for item in list(current):
        term = item.allergen if attribute == "allergies" else item.condition
        if term.casefold() not in wanted:
            current.remove(item)
    existing = {
        (item.allergen if attribute == "allergies" else item.condition).casefold()
        for item in current
    }
    for key, value in wanted.items():
        if key not in existing:
            current.append(
                model(**{("allergen" if attribute == "allergies" else "condition"): value})
            )


def apply_patient_write(patient: Patient, data: PatientWrite) -> None:
    for field in (
        "first_name",
        "last_name",
        "date_of_birth",
        "email",
        "phone",
        "address_line_1",
        "address_line_2",
        "city",
        "state",
        "postal_code",
        "blood_type",
        "status",
        "last_visit_at",
    ):
        value = getattr(data, field)
        setattr(patient, field, value.value if hasattr(value, "value") else value)
    replace_terms(patient, data.allergies, "allergies", PatientAllergy)
    replace_terms(patient, data.conditions, "conditions", PatientCondition)


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Patient data conflicts with an existing record"
        ) from exc


def escaped_search(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=PatientPage)
def list_patients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    status_filter: PatientStatus | None = Query(default=None, alias="status"),
    sort_by: Literal[
        "name", "date_of_birth", "last_visit_at", "created_at", "status"
    ] = "last_visit_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
) -> PatientPage:
    filters = [Patient.deleted_at.is_(None)]
    if status_filter is not None:
        filters.append(Patient.status == status_filter.value)
    if search and search.strip():
        pattern = f"%{escaped_search(search.strip())}%"
        filters.append(
            or_(
                Patient.first_name.ilike(pattern, escape="\\"),
                Patient.last_name.ilike(pattern, escape="\\"),
                (Patient.first_name + " " + Patient.last_name).ilike(pattern, escape="\\"),
                Patient.email.ilike(pattern, escape="\\"),
            )
        )
    total = db.scalar(select(func.count()).select_from(Patient).where(*filters)) or 0
    if sort_by == "name":
        columns = (func.lower(Patient.last_name), func.lower(Patient.first_name))
    else:
        columns = (getattr(Patient, sort_by),)
    order = asc if sort_order == "asc" else desc
    patients = db.scalars(
        select(Patient)
        .where(*filters)
        .order_by(*(order(column).nulls_last() for column in columns), Patient.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return PatientPage(
        items=[patient_read(patient) for patient in patients],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{patient_id}", response_model=PatientRead)
def read_patient(patient_id: UUID, db: Session = Depends(get_db)) -> PatientRead:
    return patient_read(get_active_patient(db, patient_id))


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientWrite, db: Session = Depends(get_db)) -> PatientRead:
    patient = Patient()
    apply_patient_write(patient, data)
    db.add(patient)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient_read(patient)


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: UUID, data: PatientWrite, db: Session = Depends(get_db)
) -> PatientRead:
    patient = get_active_patient(db, patient_id)
    apply_patient_write(patient, data)
    patient.updated_at = datetime.now(timezone.utc)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient_read(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: UUID, db: Session = Depends(get_db)) -> Response:
    patient = get_active_patient(db, patient_id)
    patient.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
