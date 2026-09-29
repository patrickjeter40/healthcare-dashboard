"""Deterministic patient narrative assembled from current clinical records."""

from app.models import PatientNote
from app.schemas.patient import PatientRead


def _terms(values: list[str], label: str) -> str:
    if not values:
        return f"No {label} are documented."
    return f"Documented {label} include {', '.join(values)}."


def generate_patient_summary(patient: PatientRead, recent_notes: list[PatientNote]) -> str:
    name = f"{patient.first_name} {patient.last_name}"
    blood_type = f" with blood type {patient.blood_type.value}" if patient.blood_type else ""
    overview = f"{name} is {patient.age} years old{blood_type}."
    clinical = " ".join(
        [
            _terms(patient.conditions, "conditions"),
            _terms(patient.allergies, "allergies"),
        ]
    )
    if recent_notes:
        history = "Recent clinical history:\n" + "\n".join(
            f"On {note.recorded_at.strftime('%B')} {note.recorded_at.day}, "
            f"{note.recorded_at.year}: {note.content}"
            for note in recent_notes
        )
    else:
        history = "No recent clinical notes are documented."
    return "\n\n".join([overview, clinical, history])
