"""Patient note workflows and summary inputs, independent of HTTP routing."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PatientNote
from app.schemas.note import NoteRead, NoteWrite, PatientSummary
from app.services.errors import NotFoundError
from app.services.patient_summary import generate_patient_summary
from app.services.patients import get_active_patient, patient_read
from app.services.transactions import commit_or_conflict


def active_notes(patient_id: UUID):
    return select(PatientNote).where(
        PatientNote.patient_id == patient_id, PatientNote.deleted_at.is_(None)
    )


def note_read(note: PatientNote) -> NoteRead:
    return NoteRead(
        id=note.id,
        patient_id=note.patient_id,
        content=note.content,
        recorded_at=note.recorded_at.replace(tzinfo=timezone.utc)
        if note.recorded_at.tzinfo is None
        else note.recorded_at.astimezone(timezone.utc),
        created_at=note.created_at.replace(tzinfo=timezone.utc)
        if note.created_at.tzinfo is None
        else note.created_at.astimezone(timezone.utc),
    )


def list_notes(patient_id: UUID, db: Session) -> list[NoteRead]:
    get_active_patient(db, patient_id)
    notes = db.scalars(
        active_notes(patient_id).order_by(PatientNote.recorded_at.desc(), PatientNote.id.desc())
    ).all()
    return [note_read(note) for note in notes]


def create_note(patient_id: UUID, data: NoteWrite, db: Session) -> NoteRead:
    get_active_patient(db, patient_id)
    note = PatientNote(
        patient_id=patient_id,
        content=data.content,
        recorded_at=data.recorded_at or datetime.now(timezone.utc),
    )
    db.add(note)
    commit_or_conflict(db)
    db.refresh(note)
    return note_read(note)


def delete_note(patient_id: UUID, note_id: UUID, db: Session) -> None:
    get_active_patient(db, patient_id)
    note = db.scalar(active_notes(patient_id).where(PatientNote.id == note_id))
    if note is None:
        raise NotFoundError("Note not found")
    note.deleted_at = datetime.now(timezone.utc)
    commit_or_conflict(db)


def patient_summary(patient_id: UUID, db: Session) -> PatientSummary:
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
        summary=generate_patient_summary(
            patient_read(patient), [note_read(note) for note in recent_notes]
        ),
    )
