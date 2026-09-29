from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PatientNote
from app.routers.patients import get_active_patient, patient_read
from app.schemas.note import NoteRead, NoteWrite, PatientSummary
from app.services.patient_summary import generate_patient_summary

router = APIRouter(prefix="/patients/{patient_id}", tags=["patient notes"])


def active_notes(patient_id: UUID):
    return select(PatientNote).where(
        PatientNote.patient_id == patient_id, PatientNote.deleted_at.is_(None)
    )


def note_read(note: PatientNote) -> NoteRead:
    return NoteRead(
        id=note.id,
        patient_id=note.patient_id,
        content=note.content,
        recorded_at=note.recorded_at,
        created_at=note.created_at,
    )


@router.get("/notes", response_model=list[NoteRead])
def list_notes(patient_id: UUID, db: Session = Depends(get_db)) -> list[NoteRead]:
    get_active_patient(db, patient_id)
    notes = db.scalars(
        active_notes(patient_id).order_by(PatientNote.recorded_at.desc(), PatientNote.id.desc())
    ).all()
    return [note_read(note) for note in notes]


@router.post("/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(patient_id: UUID, data: NoteWrite, db: Session = Depends(get_db)) -> NoteRead:
    get_active_patient(db, patient_id)
    note = PatientNote(patient_id=patient_id, content=data.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note_read(note)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(patient_id: UUID, note_id: UUID, db: Session = Depends(get_db)) -> Response:
    get_active_patient(db, patient_id)
    note = db.scalar(active_notes(patient_id).where(PatientNote.id == note_id))
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary", response_model=PatientSummary)
def patient_summary(patient_id: UUID, db: Session = Depends(get_db)) -> PatientSummary:
    patient = get_active_patient(db, patient_id)
    recent_notes = list(
        db.scalars(
            active_notes(patient_id)
            .order_by(PatientNote.recorded_at.desc(), PatientNote.id.desc())
            .limit(3)
        )
    )
    return PatientSummary(
        patient_id=patient_id,
        summary=generate_patient_summary(patient_read(patient), recent_notes),
    )
