from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.note import NoteRead, NoteWrite, PatientSummary
from app.services import notes as note_service

router = APIRouter(prefix="/patients/{patient_id}", tags=["patient notes"])


@router.get("/notes", response_model=list[NoteRead])
def list_notes(patient_id: UUID, db: Session = Depends(get_db)) -> list[NoteRead]:
    return note_service.list_notes(patient_id, db)


@router.post("/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(patient_id: UUID, data: NoteWrite, db: Session = Depends(get_db)) -> NoteRead:
    return note_service.create_note(patient_id, data, db)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(patient_id: UUID, note_id: UUID, db: Session = Depends(get_db)) -> Response:
    note_service.delete_note(patient_id, note_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary", response_model=PatientSummary)
def patient_summary(patient_id: UUID, db: Session = Depends(get_db)) -> PatientSummary:
    return note_service.patient_summary(patient_id, db)
