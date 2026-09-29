# Database migration history

Alembic is the source of truth for schema changes. Startup applies the migration chain automatically. These notes explain data preservation and downgrade limitations; the current schema is documented in [schema.dbml](../schema.dbml).

## Reference catalogs and label integrity

The `20260929_02` Alembic migration preserves existing selections (including deleted patients), deduplicates exact text matches into catalogs, and replaces legacy association rows with composite-key joins. The follow-up `20260929_03` migration standardizes labels to title case, preserves COPD/GERD acronyms, and merges casing-only duplicates while retaining selections for active and deleted patients. It keeps an already-canonical catalog ID when possible. Misspellings remain distinct; no clinical equivalence is inferred. Seeding reuses capitalization matches and never overwrites existing patients. Casing cleanup is retained on downgrade because original casing and merged IDs cannot be recovered. Legacy `Sulfa Drugs` and `Arthritis` remain alongside the new catalog's more specific entries. Original association IDs/timestamps are removed by the requested two-column model; downgrade reconstructs text selections with new IDs/timestamps and drops unassociated catalog values. This is an intentional API change, so frontend and backend should deploy together. Migration data conversion needs a live database connection (online Alembic), not offline SQL generation.

The `20260929_04` migration adds normalized unique indexes, trims surrounding spaces without changing reference IDs or patient selections, and adds trimmed-name checks. It retains the original exact-name unique constraints. If normalized duplicates were introduced through direct SQL after the casing cleanup, the migration fails transactionally rather than discarding references. Downgrade removes the new indexes/checks and retains cleaned names.

## Patient addresses and lookup tables

Revision `20260929_05` moves nonempty patient addresses into a separate patient-owned table and replaces status/blood-type CHECK constraints with foreign keys to seeded lookup tables. It preserves partial addresses and values for both active and soft-deleted patients. Patients without address data have no address row. Status and blood-type codes and the API's flat address fields remain unchanged.

Downgrade copies address fields back into patients, restores the original status/blood-type checks, and removes the new tables. Any extra lookup codes added outside the supported API contract must satisfy the original checks before downgrade can succeed.
