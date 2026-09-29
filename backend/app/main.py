from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers.health import router as health_router
from app.routers.notes import router as notes_router
from app.routers.patients import router as patient_router
from app.routers.references import router as reference_router
from app.services.errors import ConflictError, NotFoundError, ReferenceValidationError

app = FastAPI(title="Healthcare Patient Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(patient_router)
app.include_router(notes_router)
app.include_router(reference_router)


@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ReferenceValidationError)
async def reference_validation_handler(
    _request: Request, exc: ReferenceValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {
                    "loc": ["body", exc.field],
                    "msg": str(exc),
                    "type": "value_error",
                }
            ]
        },
    )
