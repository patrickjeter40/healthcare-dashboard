from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.patient import PatientPage, PatientRead, PatientStatus, PatientWrite
from app.services import patients as patient_service

router = APIRouter(prefix="/patients", tags=["patients"])


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
    return patient_service.list_patients(
        db,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{patient_id}", response_model=PatientRead)
def read_patient(patient_id: UUID, db: Session = Depends(get_db)) -> PatientRead:
    return patient_service.read_patient(patient_id, db)


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientWrite, db: Session = Depends(get_db)) -> PatientRead:
    return patient_service.create_patient(data, db)


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: UUID, data: PatientWrite, db: Session = Depends(get_db)
) -> PatientRead:
    return patient_service.update_patient(patient_id, data, db)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: UUID, db: Session = Depends(get_db)) -> Response:
    patient_service.delete_patient(patient_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
