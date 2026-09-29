"""Idempotent fictional data for local evaluation."""

from datetime import date, datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Patient, PatientAllergy, PatientCondition, PatientNote

NAMES = [
    ("Avery", "Morgan"),
    ("Jordan", "Ellis"),
    ("Taylor", "Reed"),
    ("Morgan", "Hayes"),
    ("Riley", "Chen"),
    ("Casey", "Patel"),
    ("Quinn", "Walker"),
    ("Harper", "Brooks"),
    ("Emerson", "Rivera"),
    ("Parker", "Nguyen"),
    ("Sage", "Bennett"),
    ("Rowan", "Foster"),
    ("Drew", "Kim"),
    ("Finley", "Carter"),
    ("Skyler", "Price"),
    ("Alex", "Santos"),
    ("Jamie", "Turner"),
    ("Robin", "Diaz"),
    ("Devon", "Bailey"),
    ("Cameron", "James"),
    ("Noel", "Hughes"),
    ("Remy", "Clarke"),
    ("Ari", "Lopez"),
    ("Kendall", "Morris"),
    ("Shiloh", "Ward"),
    ("Micah", "Gray"),
    ("Blair", "Russell"),
    ("Dakota", "Perry"),
    ("Eden", "Flores"),
    ("Reese", "Coleman"),
    ("Lennon", "Bell"),
    ("Frankie", "Ross"),
    ("Phoenix", "Murphy"),
    ("Sam", "Cooper"),
    ("Charlie", "Howard"),
    ("Adrian", "Torres"),
    ("Jules", "Peterson"),
    ("Tatum", "Powell"),
    ("Marley", "Long"),
    ("Nico", "Gomez"),
]

ALLERGIES = ["penicillin", "peanuts", "latex", "shellfish", "pollen", "sulfa drugs"]
CONDITIONS = [
    "hypertension",
    "type 2 diabetes",
    "asthma",
    "arthritis",
    "migraine",
    "hypothyroidism",
]
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
CITIES = [("Portland", "OR"), ("Seattle", "WA"), ("Sacramento", "CA"), ("Denver", "CO")]
NOTE_TEXTS = [
    "Routine follow-up completed. Care plan reviewed with patient.",
    "Patient reports stable symptoms since the previous visit.",
    "Medication list reviewed and follow-up timing discussed.",
]


def seed() -> int:
    now = datetime.now(timezone.utc)
    ids = [uuid5(NAMESPACE_URL, f"healthcare-dashboard-fictional-patient-{i}") for i in range(40)]
    with SessionLocal() as db:
        existing = set(db.scalars(select(Patient.id).where(Patient.id.in_(ids))))
        created = 0
        for index, (first_name, last_name) in enumerate(NAMES):
            patient_id = ids[index]
            if patient_id in existing:
                continue
            city, state = CITIES[index % len(CITIES)]
            patient = Patient(
                id=patient_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date(1938 + (index * 11) % 68, index % 12 + 1, index % 27 + 1),
                email=f"patient{index + 1:02d}@example.com",
                phone=f"202-555-{1000 + index:04d}",
                address_line_1=f"{100 + index} Example Street",
                city=city,
                state=state,
                postal_code=f"{97000 + index:05d}",
                blood_type=BLOOD_TYPES[index % len(BLOOD_TYPES)],
                status="discharged"
                if index % 11 == 0
                else "inactive"
                if index % 5 == 0
                else "active",
                last_visit_at=None if index % 9 == 0 else now - timedelta(days=index * 9 + 2),
            )
            for offset in range(index % 3):
                patient.allergies.append(
                    PatientAllergy(allergen=ALLERGIES[(index + offset) % len(ALLERGIES)])
                )
            for offset in range((index + 1) % 3):
                patient.conditions.append(
                    PatientCondition(condition=CONDITIONS[(index + offset) % len(CONDITIONS)])
                )
            for offset in range(index % 4):
                patient.notes.append(
                    PatientNote(
                        content=NOTE_TEXTS[offset],
                        recorded_at=now - timedelta(days=index * 9 + offset * 18 + 2),
                    )
                )
            db.add(patient)
            created += 1
        db.commit()
    return created


if __name__ == "__main__":
    print(f"Seeded {seed()} fictional patients")
