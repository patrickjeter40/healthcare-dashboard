from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Allergen, Condition
from app.schemas.patient import ReferenceOption

router = APIRouter(tags=["reference data"])


@router.get("/allergens", response_model=list[ReferenceOption])
def list_allergens(db: Session = Depends(get_db)) -> list[Allergen]:
    return list(db.scalars(select(Allergen).order_by(func.lower(Allergen.name), Allergen.name)))


@router.get("/conditions", response_model=list[ReferenceOption])
def list_conditions(db: Session = Depends(get_db)) -> list[Condition]:
    return list(db.scalars(select(Condition).order_by(func.lower(Condition.name), Condition.name)))
