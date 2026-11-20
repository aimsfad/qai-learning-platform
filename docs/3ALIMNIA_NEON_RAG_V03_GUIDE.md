# 3alimnIA Hybrid RAG V0.3 - Neon staging integration

## Scope and status

This patch adds an **opt-in PostgreSQL + pgvector RAG index** to the existing
3alimnIA Streamlit application. V0.2 SQLite remains the default. This is a
staging-only prototype, not a completed production deployment.

No credentials, databases or GitHub branches are created or modified by the
patch itself. A separate, empty Neon staging database is required. Do not use
the Neon database serving existing students and teachers. Do not copy student
or teacher production data into staging.

## Changed interfaces

- `hybrid_rag.open_index()` routes to V0.2 SQLite or V0.3 PostgreSQL.
- `teacher_studio.py`, `rag_cli.py`, and `hybrid_rag.project_context()` now
  call that factory. All public index methods retain their V0.2 names.
- `rag_postgres.py` implements scoped ingest, lookup, approval, consent,
  revocation, removal and search; it never reads the platform's main DB URL.
- `rag_pg_migrate.py` applies a separate explicit schema migration; the
  Streamlit app does **not** migrate schema on startup.
- `rag_pg_health.py` checks availability of the `vector` extension and RAG
  tables in the configured staging database.
- `migrations/001_neon_rag.sql` stores text, provenance, audit events and
  optional Gemini vectors (`vector(768)`).
- `tests/test_online_hybrid_rag_v02.py` closes an older SQLite test connection
  explicitly, addressing the likely Windows temporary-file lock.

## Isolation policy

1. Configure `RAG_ENVIRONMENT=staging` and `RAG_STORAGE_BACKEND=postgres` only
   in a **separate Streamlit staging app** or staging terminal.
2. Set `RAG_DATABASE_URL` to the **separate** Neon staging database. Do NOT
   reuse `DATABASE_URL`, `NEON_DATABASE_URL` or production users/credentials.
3. The code rejects the same exact URL as known production environment
   variables, but cannot prove that different URLs do not reach the same DB.
   Verify the Neon branch/project and database name manually.
4. Keep `RAG_ENABLED=false` on the live production deployment until staging
   integration tests pass and an explicit rollout is approved.
5. A verified project owner in the Streamlit session is mandatory; the storage
   layer additionally scopes queries by `owner` and `project_id`.
6. This iteration **does not implement PostgreSQL row-level security** or a
   review of every authorization path; perform a security review before
   multi-institution rollout.

## Windows CMD: install and test patch

Extract the ZIP into a separate folder, for example:

    %USERPROFILE%\Downloads\3alimnia_NEON_RAG_V03_PATCH

Open CMD and navigate to your project directory. Ensure the current Git branch
is `feat/neon-rag-storage-v03` (created from the V0.2 branch).

    git switch -c feat/neon-rag-storage-v03
    py "%USERPROFILE%\Downloads\3alimnia_NEON_RAG_V03_PATCH\apply_v03.py" --target "%CD%" --dry-run
    py "%USERPROFILE%\Downloads\3alimnia_NEON_RAG_V03_PATCH\apply_v03.py" --target "%CD%"
    py -m unittest tests.test_hybrid_rag_v01 tests.test_online_hybrid_rag_v02 tests.test_neon_rag_v03 -v

The installer checks normalized source hashes and refuses unfamiliar files. It
backs up modified files locally under `.3alimnia_patch_backups/`.
Do not `git add .` in the working directory; explicitly stage the changed
source and test files.

## Neon staging provisioning

Create a separate, preferably empty Neon project/database for staging; ensure
it contains no production student records. Obtain its connection string
privately from Neon. Do not paste it in chat, git, logs or screenshots.

In Windows CMD for the migration session only:

    set "RAG_ENVIRONMENT=staging"
    set "RAG_STORAGE_BACKEND=postgres"
    set "RAG_DATABASE_URL=<the separate Neon staging connection URL>"
    py -m pip install "psycopg[binary]>=3.2,<4"
    py rag_pg_migrate.py --dry-run
    py rag_pg_migrate.py --apply --confirm-staging
    py rag_pg_health.py

The migration creates `vector`, `rag_documents`, `rag_chunks`, `rag_events`,
FTS and HNSW indexes. It does not change the existing platform's user/course
schema. Migrations are explicit and require confirmation. It does not
migrate any existing SQLite RAG index contents.

For the **separate Streamlit staging app** set root-level Streamlit Secrets:

    RAG_ENABLED = "true"
    RAG_STORAGE_BACKEND = "postgres"
    RAG_ENVIRONMENT = "staging"
    RAG_DATABASE_URL = "<staging URL - SECRET>"
    RAG_CLOUD_EMBEDDINGS_ENABLED = "false"
    RAG_USE_LOCAL_EMBEDDINGS = "false"

Configure model-generation credentials separately, preserving the app's
existing cloud provider settings. Start with lexical retrieval only. For a
non-sensitive document with explicit opt-in, test Gemini embeddings later.
Never put these values in the repository or in `.streamlit/secrets.toml`
committed to Git.

## Tests and verification

Offline tests:

    py -m unittest tests.test_neon_rag_v03 -v

Optional **real** staging integration test (requires prior migration and
explicit permission for test writes):

    set "RAG_TEST_DATABASE_URL=<the isolated test URL>"
    set "RAG_TEST_ALLOW_WRITES=yes"
    py -m unittest tests.test_neon_rag_v03_integration -v

Do not run that integration test against production. It inserts and removes a
small, synthetic sample document. Because it requires real credentials, it
is intentionally skipped by default.

## Retrieval and evaluation notes

- Sources start unapproved. Approved teacher sources outrank approved external
  sources. Cloud generation requires a separate consent flag per source.
- Online Gemini embedding is opt-in per document. The query is sent to Gemini
  only when at least one approved/consented compatible document exists in
  the caller's project.
- Lexical search uses PostgreSQL `to_tsvector('simple', ...)`; benchmark
  multilingual Arabic/French/English retrieval before scientific claims.
- V0.3 semantic retrieval uses exact cosine ranking over an explicitly
  materialized, tenant-scoped set. An HNSW index is created for future
  larger-scale comparison, but this precise query does not use that index.
- Vector storage is fixed at 768 dimensions for `gemini-embedding-001`.
- Citations identify source/chunk locations; they do NOT establish scientific
  truth or entailment. Teacher review remains compulsory.
- Cloud models, Gemini quotas and the live Streamlit UI have **not** been
  exercised by the offline tests.

## Remaining for production

1. Fully isolated staging login, project and course schemas with synthetic users.
2. Actual Neon integration tests, access-control tests and restart/persistence QA.
3. Multi-tenant role review / PostgreSQL RLS and abuse testing.
4. Retryable background embedding queue, quotas, cost logs and job statuses.
5. Consent version history, retention policies and disaster recovery tests.
6. Semantic claim-level verification, citation correctness benchmark and
   human-adjudicated comparisons for the paper.
7. Separate security gate before any main-branch rollout.
