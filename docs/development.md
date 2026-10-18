# Development and verification

The executable backend is FastAPI + LangGraph,
Ollama/OpenAI-compatible inference, Supabase, optional Neo4j/Tavily/Azure Translator.

Use Python 3.12 and Node 22 LTS. From the repository root:

```sh
python -m venv .venv
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements-dev.txt
# Generate once and store securely in the deployment environment, not in Git:
python -c 'import secrets; print(secrets.token_urlsafe(48))'
# Supply that value as SECRET_KEY, then configure Supabase/service endpoints.
cd front
npm ci
npm test -- --watchAll=false --runInBand
npm run build
```

Start the API from `back/` with `../.venv/bin/uvicorn main:app --port 8080`.
Start the frontend from `front/` with `npm start`. The API port matches the
frontend development environment. The production API URL is configured in
`front/.env.production`; deployers should override it for their own backend.

`SECRET_KEY` is required at import/startup, at least 32 UTF-8 bytes, rejects known
placeholders, repeated characters and low character diversity. This heuristic
cannot prove entropy: use a cryptographic generator. Existing environment variables
win over `.env`. Never put a real key into a tracked example or CI configuration.
Passwords allow Unicode, spaces and punctuation: 8–72 characters and at most
72 UTF-8 bytes because bcrypt has a byte limit. Existing account login remains
compatible; the strengthened policy applies to registration.

`ALLOWED_ORIGINS` is a comma-separated exact origin list (no paths or wildcards).
Defaults: localhost/127.0.0.1 port 3000 and `https://antutor.pages.dev`. Set the
actual deployment origins explicitly. WebSockets require a matching Origin even
for native clients, plus the existing first-message JWT/session ownership checks.
`ENABLE_BENCHMARK_ENDPOINT=false` by default returns 404; enabling it still requires
an authenticated backend user. Enable only in a controlled development environment.

Validation responses contain field locations/types/messages, never Pydantic input
or context data. Guardrail blocks write classification, transport, optional UUID
and server timestamp to `security_logs`; no original/matched learner text. A DB
outage logs a generic warning and still blocks the request. The 2-second audit wait
bounds request delay; a synchronous worker already in flight may finish afterward.

## Database baseline and local Docker checks

The five `supabase/migrations` files are a **fresh database baseline inferred from
application code**, not a certified export of an existing Supabase project. IDs are
UUID for users and bigint for sessions/concepts/questions/attempts. The attendance
table is `user_attendance`, matching the code. The supplied requirements confirm cascade from users and concepts through sessions
to chat_logs; assessment adds hakes_gain and unique daily attendance. Review remaining type/constraint differences
and back up an existing database before preparing a deployment-specific upgrade;
do not run the baseline over existing tables. Existing `security_logs` may need
its columns aligned with `user_id`, `threat_type`, `transport`, `created_at`.
This is a **fresh-database baseline aligned with the current backend contract**,
not a claim about an RPC mismatch in the existing live database. The cache requires `namespace`, a unique namespace index, `hit_count`, and the v2
RPC. Existing unscoped cache rows are never read by the new application.

Supabase already supplies `anon`, `authenticated`, `service_role` roles. The local
Docker bootstrap supplies their equivalents. Every application table enables RLS,
with no browser policies or direct privileges. Only FastAPI's **service-role** key
can read/write; an anon key is deliberately insufficient. Custom application JWTs
are not Supabase Auth JWTs. The backend remains responsible for ownership checks.
Questions and both cache RPCs cannot be read/executed by PUBLIC/anon/authenticated.
Defaults are revoked for future objects created by the migration role too.

Set `LOCAL_DB_PASSWORD` and `LOCAL_NEO4J_PASSWORD` securely in the shell or ignored
`.env` (both required by Compose), then:

```sh
docker compose up -d --wait db
bash scripts/db/migrate.sh
bash scripts/db/migrate.sh  # no-op with unchanged checksums
docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < tests/sql/schema_checks.sql
```

The local DB listens only on loopback port 54322. For a complete local table/RPC
HTTP path compatible with the Supabase client, generate private settings first:

```sh
.venv/bin/python scripts/create_local_env.py  # creates ignored .env, refuses overwrite
docker compose --profile api up -d --wait db rest gateway
bash scripts/db/migrate.sh
docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < supabase/seed/concepts.sql
docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < supabase/seed/concepts.example.sql
docker compose restart rest  # reload schema after migrations
```

Run the generator **before the first Docker startup**, so the database and the
HTTP service use the same local credentials. With an existing `.env`, preserve it
and reconcile settings manually or generate a separate file with `--output` and
use Compose's `--env-file`. Changing a password does not update an existing DB
volume; regenerate only for a new/disposable stack. The generated service token
expires in 30 days. Do not use it or the local settings for production.

The gateway listens only on port 54321 and forwards `/rest/v1` to PostgREST, which
logs in as a NOINHERIT authenticator and assumes the signed service-role claim.
Anonymous calls remain denied. This is a minimal local table/RPC gateway, not
Supabase Auth/Storage/Realtime. FastAPI's own registration/JWT logic needs only
these table/RPC operations. Start FastAPI normally; its dotenv loader reads the
ignored root `.env`. LLM responses still require a separately running model.
`LOCAL_DB_PORT` / `LOCAL_API_PORT` can override the loopback ports for isolated tests.

The two supplied concept CSVs differ only in column order. `concepts.sql` imports
30 original records with all supplied fields; see `supabase/seed/data-provenance.md`.
Apply it before `concepts.example.sql`, which adds one illustrative quiz question
without overwriting supplied concepts. Seeds are rerunnable. ID/name collisions
fail rather than silently remap existing relationships. A fresh Supabase project
can run the same migrations/seeds (its platform already supplies roles).

SQL verification rolls data back and tests actual denied operations, cascades,
quiz constraints and cache counters. Migration files apply transactionally with a
checksum ledger. Never edit an already deployed migration; add an upgrade file.
Volumes persist until explicitly removed. Local SQL smoke test:
`docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < tests/sql/schema_checks.sql`.
`tests/integration/check_api.py` writes synthetic accounts and verifies the complete
non-LLM flow; run it only against a disposable seeded API with `TEST_API_URL` and
the matching local `SUPABASE_URL`/`SUPABASE_KEY` in the process environment.

## Conservative synthesis cache

Both REST and WebSocket execute guardrails, expert evaluation, scaffolding and
session/log updates on every turn. Caching lives inside the shared graph's retry
and final synthesis nodes, **not an early return from the route**. A hit reuses the
structured synthesis result only; it does not invent zero scores or skip history.
Streaming cache hits deliver the normal final result without model token chunks.
Scaffolding generation and sandbox/benchmark calls without learner scope are not
cached.

The namespace hashes learner/session/concept identity, session state, last-question
hash, exact answer, scaffold state, mastery count, previous weakest agent, history,
full synthesis prompt (including current expert evidence), prompt version and model
configuration. Similar vectors alone cannot cross these boundaries. Exact prompt
and answer hashes intentionally reduce hit rate to protect pedagogical correctness.
Set `MODEL_VERSION` to an immutable deployment/model revision and bump it whenever
weights change under the same model name/URL. `PROMPT_VERSION` defaults to the
prompt source SHA-256; override only with a deliberate release version.

The scoped RPC atomically increments `hit_count` on real hits, excludes entries
over 24 hours old, and never increments during probes. Failed cache/embedding
operations fall back to generation. Invalid/unstructured synthesis is not cached.
Namespace uniqueness allows a B-tree lookup with at most one candidate, so no
unmeasured `IVFFlat lists=100` index is installed. If broad retrieval is reintroduced,
benchmark recall, latency and filtered-candidate counts on representative data
before selecting an ANN index or number of lists. Expired rows can be periodically
removed with `DELETE FROM semantic_cache WHERE created_at < now() - interval '24 hours'`
using backend/admin privileges.

## Neo4j

`neo4j/seed/relation_data.csv` comes from the original 80-row project relation dataset.
Normalization produces 32 concepts and 69 unique relationships. Reversed
RELATED_TO/CONTRASTS_WITH edges collapse; CAUSES/PART_OF/REQUIRES retain their
supplied direction. Distinct reasons on the same edge are joined, not discarded.
The supplied causal assertions have not been independently fact-checked. See
`neo4j/data-provenance.md` for the source checksum and transformation policy.
Unique concept names plus MERGE make reruns idempotent.

```sh
docker compose up -d neo4j
# Wait for Neo4j availability; supply NEO4J_URI=bolt://localhost:7687,
# NEO4J_USER=neo4j, NEO4J_PASSWORD=$LOCAL_NEO4J_PASSWORD, NEO4J_DATABASE=neo4j.
.venv/bin/python scripts/seed_neo4j.py
```

For hosted Neo4j use the verified `neo4j+s://` / `bolt+s://` URI unchanged. Local
plain Bolt is restricted to loopback by Compose. The driver now honors the configured
database; aliases such as 인플레이션/CPI/Interest_Rate normalize identically on
seed ingestion and retrieval.

## Tests and runtime data

Run `.venv/bin/pytest -q` from the root. Unit tests use fake external dependencies,
not real inference, learner records or paid API calls. SQL and Neo4j integration
checks are separate Docker jobs in CI. CI runs backend tests, frontend tests/build,
fresh migrations/permission checks, and repeatable Neo4j seed checks.

Legacy diagnostics are under `scripts/diagnostics`; manual integration/performance
scripts are under `tests/manual` and `tests/performance` and are excluded from pytest.
Review each before use: some write to databases or call paid inference APIs. Their
outputs are not evidence that the automated suite passed.
Runtime logs and generated reports are ignored. Debate/sandbox file dumps default to off;
`ENABLE_PRIVATE_DEBUG_LOGS=true` writes to ignored `runtime-logs/` (or `PRIVATE_LOG_DIR`). Committed learner/debate logs were
removed from the current tree; this does not erase historical Git commits. Treat
production logs as private data with deployment-specific retention/access controls.
