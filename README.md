# Healthcare Dashboard

A patient management dashboard built with React, TypeScript, FastAPI, PostgreSQL, and Docker Compose. It includes 40 fictional patients, clinical notes, and a deterministic patient summary. Sample records and local defaults are for evaluation; do not enter real protected health information.

## Run locally

With Docker running:

```bash
docker compose up --build
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Liveness | http://localhost:8000/health |
| Database readiness | http://localhost:8000/ready |

Compose supplies local defaults. Copy `.env.example` to `.env` only to override them; if database credentials change, update `DATABASE_URL` too. Startup waits for PostgreSQL, applies migrations, and seeds 40 patients. Restarting preserves existing records and does not duplicate seed data. The frontend runs the Vite development server.

## Features and take-home coverage

| Requirement | Implementation |
| --- | --- |
| Foundation | Vite, strict TypeScript, MUI/Emotion, React Router, TanStack Query, linting and formatting; FastAPI health endpoint, PostgreSQL, Alembic |
| Dashboard | Header/sidebar navigation, responsive patient table/cards, CRUD, pagination, search, status filtering, column sorting, patient detail and 404 routes |
| Notes and summary | Add/list/soft-delete notes with timestamps; summary includes name, age, blood type, conditions, allergies, and the three most recent active notes |
| Forms and errors | Shared create/edit form for personal, contact, address, and medical fields; client/server validation, field errors, network failure messages |
| Local setup | Two Dockerfiles, Compose health dependencies, `.env.example`, automatic migrations and idempotent seed |

Stretch highlights are server-side sorting/filtering and lazy route loading. Search is debounced by 300 ms and requests can be cancelled. The 125-patient regression verifies bounded pages and batched association queries; virtualization is unnecessary for pages of 10 to 50 rows.

## Architecture and decisions

- **Frontend:** TanStack Query owns server data and cache invalidation; React Hook Form and Zod handle forms. MUI supplies responsive components, while React Router handles navigation. Oxlint and Prettier provide linting/formatting. Both TypeScript configurations are strict, and the production build runs typechecking first.
- **Backend:** Routers handle HTTP contracts and inject database sessions; application services handle queries and transactional workflows. Shared exceptions map to HTTP responses. The summary generator consumes read DTOs, without database or HTTP dependencies.
- **Data:** Patients have an optional separate address, required status lookup, and optional blood-type lookup. Allergies/conditions use UUID catalogs and composite-key joins. Foreign keys, uniqueness/check constraints, and validation enforce integrity. DOB is stored; age is calculated on read.
- **Lifecycle:** Patient/note deletion is soft deletion. Removed patients return 404; related records remain stored. Clearing a clinical selection deletes its join row. Empty selections mean nothing documented, rather than a confirmed negative assessment.
- **Summary:** A deterministic template assembles current profile data and recent notes on request. It requires no external credentials and stores no duplicate derived state. Note input uses local time; the form converts it to a timezone-aware timestamp, and note displays use UTC.

See [architecture and data design](docs/architecture.md) for SOLID tradeoffs, timestamp/concurrency semantics, and indexing decisions; [migration history](docs/migrations.md) for preservation and downgrade details; and [schema.dbml](schema.dbml) for the current schema. Alembic remains the schema source of truth.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Process liveness: `{"status":"ok"}` |
| `GET /ready` | Database readiness; returns 503 when unavailable |
| `GET /allergens`, `GET /conditions` | Alphabetical `{id, name}` catalogs |
| `GET /patients` | Pagination, search, status filtering, sorting |
| `GET /patients/{id}` | Active patient detail |
| `POST /patients`, `PUT /patients/{id}`, `DELETE /patients/{id}` | Create, replace editable fields, soft-delete |
| `GET /patients/{id}/notes`, `POST /patients/{id}/notes` | List and add notes |
| `DELETE /patients/{id}/notes/{note_id}` | Soft-delete a note owned by that patient |
| `GET /patients/{id}/summary` | Current deterministic summary |

List parameters are `page`, `page_size` (maximum 100), `search`, `status`, `sort_by`, and `sort_order`. Invalid input returns 422, missing/deleted records return 404, and integrity conflicts return 409. Swagger documents complete request/response shapes.

Patient writes use `allergy_ids` and `condition_ids` UUID arrays. Responses contain `allergies`/`conditions` as `{id, name}` arrays. PUT replaces editable fields; omitted selections become empty. Unknown/duplicate IDs return 422, and profile changes commit atomically. Catalogs are cached for one hour; the form blocks saving if they cannot load.

A note request accepts:

```json
{"content": "Fictional follow-up", "recorded_at": "2024-01-02T10:30:00Z"}
```

Supplied timestamps require a timezone and cannot be in the future. Omitting `recorded_at` defaults to current UTC time. `created_at` records insertion time separately. Notes are listed newest first.

## Verification

Backend tests use an isolated in-memory database and never alter the seeded PostgreSQL data. They exercise the API flows. The optional `TEST_POSTGRES_MIGRATIONS=1` tests verify catalog-integrity and address/lookup migrations against PostgreSQL in temporary schemas and roll all changes back. Docker and Alembic checks also verify the PostgreSQL startup path.

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
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

On macOS/Linux, use `.venv/bin/python` and `.venv/bin/ruff` in place of the Windows paths.

## Limitations and submission

Authentication, roles, tenant isolation, clinical terminology integration, full audit history, restore/purge controls, real-time updates, and LLM summaries are outside this exercise. Transactions prevent partial writes; optimistic locking and concurrent edit/delete protection are not implemented. Query services explicitly depend on SQLAlchemy, a pragmatic choice for one database.

Submit the public repository or a source ZIP. Exclude `.env`, dependencies, caches, and local database files; keep `.env.example`. The original specification is in [takehome_requirements.md](takehome_requirements.md).
