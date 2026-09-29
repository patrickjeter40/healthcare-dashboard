# Healthcare Dashboard

A full-stack patient management dashboard built with React, TypeScript, FastAPI, PostgreSQL, and Docker Compose. It ships with 40 fictional patients, clinical notes, and a deterministic patient summary. All sample names and records are fictional; do not enter real protected health information.

## Run locally

Ensure Docker is running.

```bash
docker compose up --build
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Liveness check | http://localhost:8000/health |
| Database readiness | http://localhost:8000/ready |

Compose provides local development defaults. Copy `.env.example` to `.env` only to override them. If database credentials change, update `DATABASE_URL` as well. The backend waits for PostgreSQL health, applies Alembic migrations, and runs an idempotent seed before serving requests. Rebuilding or restarting does not duplicate the 40 seed patients.

## What the dashboard does

- Browse patients with server-side search, status filtering, sorting, and pagination. Search waits 300 ms before requesting the server.
- Create and edit patients with client and server validation. Allergies and conditions are selected from seeded catalogs using searchable multi-select controls.
- Review patient details, soft-delete a patient with confirmation, and see readable loading, empty, and error states.
- Add and soft-delete clinical notes. Deleted notes disappear from the active record but remain stored for retention.
- View a summary generated from the current patient information and three most recent active notes. Notes accept a recorded date/time; the form converts local input to a timestamp with a timezone. The note list displays UTC date/time, and summary dates use UTC.

## Architecture and decisions

**Frontend.** React, TypeScript, Vite, MUI, and React Router provide the responsive interface. TanStack Query handles remote data, caching, mutations, and invalidation. Most meaningful state lives on the server, so Redux would add a second source of truth without solving a current problem. React Hook Form and Zod power a shared create/edit form; FastAPI/Pydantic validation remains authoritative. The small typed `fetch` client maps backend errors to readable messages and field errors.

**Frontend development tooling.** Oxlint provides linting (`npm run lint`), and Prettier provides formatting (`npm run format`) and a formatting check (`npm run format:check`). Both the application and Vite configuration use TypeScript with `strict: true`. The separate `npm run typecheck` command runs `tsc -b --pretty false` without emitting JavaScript. Vite transpiles TypeScript but does not type-check it; `npm run build` explicitly runs `tsc -b` before `vite build`, so type errors fail the build.

**Backend and data.** FastAPI and SQLAlchemy 2.x use PostgreSQL with Alembic migrations. Allergies and conditions are structured reference data with many-to-many patient associations rather than free-text fields. UUID catalogs require nonblank names without surrounding spaces, with unique constraints plus unique indexes on `lower(btrim(name))` to prevent casing-only duplicates; join tables use composite patient/reference primary keys and foreign keys. This prevents inconsistent new values and supports reliable structured filtering and reporting. The take-home uses a small seeded catalog for reproducibility, not clinical completeness; a production healthcare system would likely integrate standardized terminology such as SNOMED CT, ICD-10, or an external terminology service. Notes remain patient-owned records. Foreign keys, uniqueness constraints, check constraints, and Pydantic validation protect integrity. DOB is stored and age is calculated on read. The patient list uses an allowlist for sorting, bounded page sizes, and SQL search rather than loading every row into React.

**Service boundaries and SOLID.** Patient and note routers handle request validation, dependency injection, and response contracts. Application services own queries and transactional workflows; shared application exceptions are translated to HTTP at the composition root. Summary generation consumes read DTOs and has no database or HTTP dependency. The notes hook owns remote state and cache invalidation; the component owns its form and presentation, with patient identity resetting local draft/dialog state.

| Principle | Application and limits |
| --- | --- |
| Single responsibility | HTTP routing, patient/note workflows, narrative generation, persistence models, form validation, and remote-state hooks have separate responsibilities. |
| Open/closed | New routes, feature services, and UI components can be composed without changing unrelated features. Changing the supported status/blood-type contract deliberately changes validation and UI options. |
| Liskov substitution | There is no custom business inheritance hierarchy to assess; standard framework contracts and exception subclasses retain their expected behavior. |
| Interface segregation | Feature functions and DTOs expose focused inputs/outputs; there is no universal service interface requiring unrelated operations. |
| Dependency inversion | Routes use injected sessions and delegate to services; the narrative generator depends on DTOs rather than ORM objects. Query services still explicitly depend on SQLAlchemy. This is a pragmatic boundary for one database; repository protocols would be justified if interchangeable persistence became a requirement. |

**Health checks.** `/health` is process liveness and retains the required `{"status":"ok"}` response. `/ready` executes a database query and returns 503 with a generic message if the database is unavailable. Compose uses readiness for backend health and frontend startup dependencies. Readiness does not certify every table, migration, or external system; use Alembic and functional API checks alongside it.

**Lifecycle and retention.** Patients and notes have `deleted_at`. Normal queries exclude deleted records; deleted patients return 404 from detail, update, note, and summary endpoints. A note can only be removed through its owning patient's route. Related records remain when a patient is soft-deleted. Removing an allergy or condition selection physically deletes its join row; editing a patient overwrites earlier scalar values. Retention is not a complete audit trail: change history, actors, and reasons are outside this exercise, as are restore and purge workflows. Foreign keys protect references, while the application enforces soft-delete visibility and write restrictions.

**Empty selections.** An empty allergy or condition collection means nothing is documented. It does not distinguish an unreviewed record from a reviewed record with no findings. The UI uses "No allergies/conditions documented" rather than implying a completed assessment. An explicit assessment state would be appropriate if that distinction became a product requirement.

**Timestamps and concurrent writes.** Patient `updated_at` means the patient record was last edited through SQLAlchemy/the API, including selection changes and soft deletion. Adding or deleting a note does not update it; direct SQL changes do not automatically advance it because there is no database update trigger. Notes have independent timestamps. Patient write transactions prevent partial commits but do not prevent conflicting concurrent edits or a race between editing and soft deletion. Row locking/version checks are outside the take-home scope.

**Indexes and scope.** Join primary keys begin with `patient_id` and support patient-based relationship reads. Reverse catalog indexes can be added when filtering patients by allergen/condition is implemented. Note indexes and patient list scans are adequate for the sample dataset; larger workloads should use measured query plans to choose partial/composite indexes. Email is intentionally nonunique because patients can share contact details.

**Summary.** A small service assembles a deterministic narrative from the patient, allergies, conditions, and recent active notes. It is generated on request, not stored as duplicate derived state. The behavior is reproducible and needs no external credentials. A production LLM option would require evaluation, guardrails, source provenance, and auditability before use.

**Future multi-practice deployment.** Authentication and tenant isolation are deliberately outside this take-home. A production design would add users, memberships, and organizations, then enforce tenant-scoped queries, integrations, credentials, and configuration on the server. The frontend is not a security boundary.

The current PostgreSQL schema is documented in [schema.dbml](schema.dbml), including composite keys, foreign keys, checks, indexes, and lifecycle notes. Alembic remains the source of truth for database changes.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /allergens`, `GET /conditions` | Read-only alphabetical `{id, name}` catalogs |
| `GET /health` | Health status |
| `GET /patients` | Paginated list with `page`, `page_size`, `search`, `status`, `sort_by`, `sort_order` |
| `GET /patients/{id}` | Active patient detail |
| `POST /patients`, `PUT /patients/{id}`, `DELETE /patients/{id}` | Create, replace editable fields, soft-delete |
| `GET /patients/{id}/notes`, `POST /patients/{id}/notes` | List and add active notes |
| `DELETE /patients/{id}/notes/{note_id}` | Soft-delete a note owned by that patient |
| `GET /patients/{id}/summary` | Deterministic current summary |

Patient writes accept `allergy_ids` and `condition_ids` UUID arrays, not free text. Responses include `allergies` and `conditions` arrays of `{id, name}`. PUT retains its existing replacement semantics: omitted selection arrays default to empty. Unknown or duplicate IDs return 422; both catalogs are validated before changes and scalar fields plus associations commit in one transaction. Soft deletion retains associations and catalog values. The frontend caches catalogs for one hour and blocks the form if either cannot load.

The `20260929_02` Alembic migration preserves existing selections (including deleted patients), deduplicates exact text matches into catalogs, and replaces legacy association rows with composite-key joins. The follow-up `20260929_03` migration standardizes labels to title case, preserves COPD/GERD acronyms, and merges casing-only duplicates while retaining selections for active and deleted patients. It keeps an already-canonical catalog ID when possible. Misspellings remain distinct; no clinical equivalence is inferred. Seeding reuses capitalization matches and never overwrites existing patients. Casing cleanup is retained on downgrade because original casing and merged IDs cannot be recovered. Legacy `Sulfa Drugs` and `Arthritis` remain alongside the new catalog's more specific entries. Original association IDs/timestamps are removed by the requested two-column model; downgrade reconstructs text selections with new IDs/timestamps and drops unassociated catalog values. This is an intentional API change, so frontend and backend should deploy together. Migration data conversion needs a live database connection (online Alembic), not offline SQL generation.

The `20260929_04` migration adds normalized unique indexes, trims surrounding spaces without changing reference IDs or patient selections, and adds trimmed-name checks. It retains the original exact-name unique constraints. If normalized duplicates were introduced through direct SQL after the casing cleanup, the migration fails transactionally rather than discarding references. Downgrade removes the new indexes/checks and retains cleaned names.

`POST /patients/{id}/notes` accepts `{ "content": "Fictional follow-up", "recorded_at": "2024-01-02T10:30:00Z" }`. A supplied timestamp must include a timezone and cannot be in the future; malformed, timezone-free, or future timestamps return 422. Omitting `recorded_at` defaults to the current UTC time for compatibility. Stored note time represents the clinical record's supplied time; `created_at` separately represents insertion time. Notes are returned newest first by recorded time.

Patient list queries support a maximum `page_size` of 100. Invalid input returns 422; missing or deleted records return 404. The OpenAPI page documents request and response shapes.

## Take-home coverage

| Requirement | Implementation |
| --- | --- |
| Foundation | Vite, strict TypeScript, MUI/Emotion, React Router, TanStack Query, linting and formatting; FastAPI health endpoint; PostgreSQL and Alembic |
| Dashboard and patients | Header navigation, responsive sidebar/cards/table, patient CRUD, server pagination/search/status filtering/sorting, debounced search, required routes and 404 page |
| Notes and summary | Add/list/soft-delete notes with recorded timestamps; deterministic summary includes name, age, blood type (or explicit unknown), conditions, allergies, and recent notes |
| Forms and errors | Shared create/edit form with contact/address/medical fields, client/server validation, readable network and validation failures |
| Local setup | Backend/frontend Dockerfiles, Compose health dependencies, `.env.example`, automatic migration and idempotent fictional seed of 40 patients |

Stretch highlights are server-side sorting/filtering and lazy route loading. Alembic and API regression tests also support reproducibility and correctness. The 125-patient regression checks bounded page sizes and batched relationship queries; virtualization is unnecessary for pages of 10?50 rows. Clinical terminology, authentication, realtime features, and multi-tenancy remain outside scope.

For submission, share the repository or provide the source ZIP; exclude `.env`, dependencies, caches, and local database files. `.env.example` supplies reproducible local defaults.

## Verification

Backend tests use an isolated in-memory database and never alter the seeded PostgreSQL data. They exercise the API flows. The optional `TEST_POSTGRES_MIGRATIONS=1` tests verify catalog-integrity and address/lookup migrations against PostgreSQL in a temporary schema and rolls all changes back. Docker and Alembic checks also verify the PostgreSQL startup path.

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

## Scope and next steps

This exercise omits authentication, roles, tenant isolation, a full audit event stream, restore/purge controls, clinical coding systems, real-time updates, and LLM summaries. Before handling real patient data, it would also need access controls, stronger audit and observability, security review, and operational policies. The current seed data and local Compose defaults are for evaluation only.

Patient addresses are stored in `addresses`, with a unique, required `patient_id`: each patient has zero or one current mailing address. Partial addresses remain valid. Address changes update the same row, clearing all fields removes it, and patient soft deletion retains it. Addresses are patient-owned rather than shared between households; address history is outside scope.

`patient_statuses` and `blood_types` are seeded lookup tables. Patients reference their stable natural code keys through foreign keys: status is required, blood type is optional (`NULL` means not recorded). Status labels are separate from codes; blood type codes already serve as display labels. These small, immutable code sets do not need synthetic UUID keys. The API continues accepting and returning existing status/blood type codes and flat address fields, while persistence is normalized. Adding new codes requires updating API validation and UI options as well as lookup data. Revision `20260929_05` preserves all existing addresses, including soft-deleted patients; downgrade restores the original flat fields.
