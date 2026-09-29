from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.notes import router as notes_router
from app.routers.patients import router as patient_router

app = FastAPI(title="Healthcare Patient Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(patient_router)
app.include_router(notes_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
