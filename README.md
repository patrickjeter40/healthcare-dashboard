# Healthcare Dashboard

A full-stack patient management dashboard built with React, TypeScript, FastAPI, PostgreSQL, and Docker Compose. It ships with 40 fictional patients, clinical notes, and a deterministic patient summary. All sample names and records are fictional; do not enter real protected health information.

## Run locally

```bash
docker compose up --build
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

Compose provides local development defaults. Copy `.env.example` to `.env` only to override them. If database credentials change, update `DATABASE_URL` as well. The backend waits for PostgreSQL health, applies Alembic migrations, and runs an idempotent seed before serving requests. Rebuilding or restarting does not duplicate the 40 seed patients.

## What the dashboard does

- Browse patients with server-side search, status filtering, sorting, and pagination. Search waits 300 ms before requesting the server.
- Create and edit patients with client and server validation. Allergies and conditions are entered as tags and stored in related tables.
- Review patient details, soft-delete a patient with confirmation, and see readable loading, empty, and error states.
- Add and soft-delete clinical notes. Deleted notes disappear from the active record but remain stored for audit purposes.
- View a summary generated from the current patient information and three most recent active notes. Note dates in the summary and note list use UTC.

## Architecture and decisions

**Frontend.** React, TypeScript, Vite, MUI, and React Router provide the responsive interface. TanStack Query handles remote data, caching, mutations, and invalidation. Most meaningful state lives on the server, so Redux would add a second source of truth without solving a current problem. React Hook Form and Zod power a shared create/edit form; FastAPI/Pydantic validation remains authoritative. The small typed `fetch` client maps backend errors to readable messages and field errors.

**Backend and data.** FastAPI and SQLAlchemy 2.x use PostgreSQL with Alembic migrations. The schema is pragmatically normalized: allergies, conditions, and notes are related rows rather than comma-separated fields or JSON blobs. Foreign keys, uniqueness constraints, check constraints, and Pydantic validation protect integrity. DOB is stored and age is calculated on read. The patient list uses an allowlist for sorting, bounded page sizes, and SQL search rather than loading every row into React.

**Lifecycle and audit.** Patients and notes have `deleted_at`. Normal queries exclude deleted records; deleted patients return 404 from detail, update, note, and summary endpoints. A note can only be removed through its owning patient's route. Related records remain when a patient is soft-deleted. Restore and purge workflows are outside this exercise.

**Summary.** A small service assembles a deterministic narrative from the patient, allergies, conditions, and recent active notes. It is generated on request, not stored as duplicate derived state. The behavior is reproducible and needs no external credentials. A production LLM option would require evaluation, guardrails, source provenance, and auditability before use.

**Future multi-practice deployment.** Authentication and tenant isolation are deliberately outside this take-home. A production design would add users, memberships, and organizations, then enforce tenant-scoped queries, integrations, credentials, and configuration on the server. The frontend is not a security boundary.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Health status |
| `GET /patients` | Paginated list with `page`, `page_size`, `search`, `status`, `sort_by`, `sort_order` |
| `GET /patients/{id}` | Active patient detail |
| `POST /patients`, `PUT /patients/{id}`, `DELETE /patients/{id}` | Create, replace editable fields, soft-delete |
| `GET /patients/{id}/notes`, `POST /patients/{id}/notes` | List and add active notes |
| `DELETE /patients/{id}/notes/{note_id}` | Soft-delete a note owned by that patient |
| `GET /patients/{id}/summary` | Deterministic current summary |

Patient list queries support a maximum `page_size` of 100. Invalid input returns 422; missing or deleted records return 404. The OpenAPI page documents request and response shapes.

## Verification

Backend tests use an isolated in-memory database and never alter the seeded PostgreSQL data. They exercise the API flows; Docker and Alembic checks separately verify the PostgreSQL startup path.

```bash
# From backend/ (Python 3.10+)
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt  # Windows
.venv/Scripts/python -m pytest -q
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check .

# From frontend/
npm ci
npm run format:check
npm run typecheck
npm run lint
npm run build

# From the project root, with Compose running
docker compose exec backend alembic check
```

On macOS/Linux, use `.venv/bin/python` and `.venv/bin/ruff` in place of the Windows paths.

## Scope and next steps

This exercise omits authentication, roles, tenant isolation, a full audit event stream, restore/purge controls, clinical coding systems, real-time updates, and LLM summaries. Before handling real patient data, it would also need access controls, stronger audit and observability, security review, and operational policies. The current seed data and local Compose defaults are for evaluation only.
