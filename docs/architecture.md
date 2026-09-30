# Architecture and data design

Detailed design decisions for contributors. For setup and the feature overview, see the [README](../README.md).

**Frontend.** React, TypeScript, Vite, MUI, and React Router provide the responsive interface. TanStack Query handles remote data, caching, mutations, and invalidation. React state owns local interactions such as dialogs, filters, and note drafts. There is currently no substantial cross-page client workflow state that needs a global store. React Hook Form and Zod power a shared create/edit form; FastAPI/Pydantic validation remains authoritative. The small typed `fetch` client maps backend errors to readable messages and field errors.

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

The current PostgreSQL schema is documented in [schema.dbml](../schema.dbml), including composite keys, foreign keys, checks, indexes, and lifecycle notes. Alembic remains the source of truth for database changes.

## Addresses and lookup data

Patient addresses are stored in `addresses`, with a unique, required `patient_id`: each patient has zero or one current mailing address. Partial addresses remain valid. Address changes update the same row, clearing all fields removes it, and patient soft deletion retains it. Addresses are patient-owned rather than shared between households; address history is outside scope.

`patient_statuses` and `blood_types` use UUID surrogate keys, unique codes, and `created_at` metadata, consistently with allergens and conditions. Patients store a required `status_id` and optional `blood_type_id`; the API still accepts and returns codes. NULL blood type means not recorded. Status labels are separate from codes; blood type codes serve as their display labels.

Natural code keys were considered and initially used: the standardized blood type codes and small fixed status vocabulary make natural keys defensible. UUID keys were chosen for consistency across lookup entities, stable identity independent of code changes, and uniform creation metadata. Existing rows receive creation timestamps at migration time because their original insertion times were not stored. Adding supported codes still requires coordinated changes to API validation and UI options.

## State management growth path

TanStack Query remains the owner of server data as the application grows. For shared client-only state across routes, such as a multi-patient review workspace, Zustand would be the first option to evaluate. Patient records, notes, and other cached server responses should remain in the query cache rather than being duplicated in a client-state store. Form values and validation stay in React Hook Form; small component interactions stay in local React state.

Redux Toolkit remains an alternative if cross-feature client logic or team conventions warrant a standardized action/reducer architecture. A concrete requirement would drive the choice, rather than application size alone. No additional global client-state store is currently implemented.

Real-time WebSocket or server-sent events can update or invalidate query entries. A future implementation should handle reconnects, missed events, and cache refreshes. Search, filters, and pagination can move into URL parameters when preserving or sharing navigation state becomes a requirement.

Multiple user types require backend-enforced permissions. User and permission data can be fetched through TanStack Query, while the interface adapts to permitted actions. Account or practice switches must clear or partition cached data to prevent reuse across identities. These future capabilities are not implemented by the take-home.
