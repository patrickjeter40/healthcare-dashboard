"""Patient queries and transactional profile updates, independent of HTTP routing."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Address,
    Allergen,
    BloodTypeLookup,
    Condition,
    Patient,
    PatientAllergy,
    PatientCondition,
    PatientStatusLookup,
)
from app.schemas.patient import (
    PatientPage,
    PatientRead,
    PatientStatus,
    PatientWrite,
    ReferenceOption,
)
from app.services.errors import ConflictError, NotFoundError, ReferenceValidationError
from app.services.transactions import commit_or_conflict


def active_patients() -> Select[tuple[Patient]]:
    return select(Patient).where(Patient.deleted_at.is_(None))


def get_active_patient(db: Session, patient_id: UUID) -> Patient:
    patient = db.scalar(active_patients().where(Patient.id == patient_id))
    if patient is None:
        raise NotFoundError("Patient not found")
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
        address_line_1=patient.address.address_line_1 if patient.address else None,
        address_line_2=patient.address.address_line_2 if patient.address else None,
        city=patient.address.city if patient.address else None,
        state=patient.address.state if patient.address else None,
        postal_code=patient.address.postal_code if patient.address else None,
        blood_type=patient.blood_type.code if patient.blood_type else None,
        status=patient.status.code,
        last_visit_at=patient.last_visit_at,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
        allergies=sorted(
            (ReferenceOption.model_validate(item.allergen) for item in patient.allergies),
            key=lambda item: item.name.casefold(),
        ),
        conditions=sorted(
            (ReferenceOption.model_validate(item.condition) for item in patient.conditions),
            key=lambda item: item.name.casefold(),
        ),
    )


def referenced_values(db: Session, ids: list[UUID], model: type, field: str) -> list:
    values = list(db.scalars(select(model).where(model.id.in_(ids))))
    missing = set(ids) - {value.id for value in values}
    if missing:
        raise ReferenceValidationError(field, missing)
    return values


def replace_references(
    patient: Patient, values: list, attribute: str, model: type, field: str
) -> None:
    current = getattr(patient, attribute)
    wanted = {value.id: value for value in values}
    current[:] = [item for item in current if getattr(item, f"{field}_id") in wanted]
    existing = {getattr(item, f"{field}_id") for item in current}
    for identifier, value in wanted.items():
        if identifier not in existing:
            current.append(model(**{field: value}))


def apply_patient_write(db: Session, patient: Patient, data: PatientWrite) -> None:
    # Both catalogs are validated before any scalar or relationship is changed.
    allergens = referenced_values(db, data.allergy_ids, Allergen, "allergy_ids")
    conditions = referenced_values(db, data.condition_ids, Condition, "condition_ids")
    patient_status = db.scalar(
        select(PatientStatusLookup).where(PatientStatusLookup.code == data.status.value)
    )
    blood_type = (
        db.scalar(select(BloodTypeLookup).where(BloodTypeLookup.code == data.blood_type.value))
        if data.blood_type
        else None
    )
    if patient_status is None or (data.blood_type and blood_type is None):
        raise ConflictError("Required lookup data is unavailable")
    patient.status = patient_status
    patient.blood_type = blood_type
    for field in (
        "first_name",
        "last_name",
        "date_of_birth",
        "email",
        "phone",
        "last_visit_at",
    ):
        value = getattr(data, field)
        setattr(patient, field, value.value if hasattr(value, "value") else value)
    address_values = {
        field: getattr(data, field)
        for field in ("address_line_1", "address_line_2", "city", "state", "postal_code")
    }
    if any(value is not None for value in address_values.values()):
        if patient.address is None:
            patient.address = Address(**address_values)
        else:
            for field, value in address_values.items():
                setattr(patient.address, field, value)
    else:
        patient.address = None
    replace_references(patient, allergens, "allergies", PatientAllergy, "allergen")
    replace_references(patient, conditions, "conditions", PatientCondition, "condition")


def escaped_search(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_patients(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None,
    status_filter: PatientStatus | None,
    sort_by: str,
    sort_order: str,
) -> PatientPage:
    filters = [Patient.deleted_at.is_(None)]
    if status_filter is not None:
        filters.append(Patient.status.has(PatientStatusLookup.code == status_filter.value))
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
    elif sort_by == "status":
        columns = (
            select(PatientStatusLookup.code)
            .where(PatientStatusLookup.id == Patient.status_id)
            .scalar_subquery(),
        )
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


def read_patient(patient_id: UUID, db: Session) -> PatientRead:
    return patient_read(get_active_patient(db, patient_id))


def create_patient(data: PatientWrite, db: Session) -> PatientRead:
    patient = Patient()
    apply_patient_write(db, patient, data)
    db.add(patient)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient_read(patient)


def update_patient(patient_id: UUID, data: PatientWrite, db: Session) -> PatientRead:
    patient = get_active_patient(db, patient_id)
    apply_patient_write(db, patient, data)
    patient.updated_at = datetime.now(timezone.utc)
    commit_or_conflict(db)
    db.refresh(patient)
    return patient_read(patient)


def delete_patient(patient_id: UUID, db: Session) -> None:
    patient = get_active_patient(db, patient_id)
    patient.deleted_at = datetime.now(timezone.utc)
    commit_or_conflict(db)
