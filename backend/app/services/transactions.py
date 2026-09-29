from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.services.errors import ConflictError


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Data conflicts with an existing record") from exc
