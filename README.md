# AI Voice Calling Agent Platform — Backend Skeleton

Admins create AI agents that place outbound phone calls, converse naturally
using a custom prompt grounded in uploaded knowledge (RAG via ChromaDB),
collect structured lead data, and save transcripts/recordings/summaries.

## What's included in this pass

This is the **backend foundation**, built for correctness and clean
architecture so later pieces slot in cleanly:

- FastAPI app with async SQLAlchemy models for all 10 tables (users, agents,
  campaigns, knowledge_files, customers, calls, conversation_messages,
  call_summary, call_recordings, extracted_information, settings)
- Auto database creation + Alembic migrations (async-engine compatible)
- JWT auth, bcrypt password hashing, role-based access (admin), rate-limited login
- Agent CRUD, customer, campaign, knowledge upload, and call REST APIs
- ChromaDB knowledge ingestion (PDF/DOCX/TXT → chunk → embed → per-agent
  collection) with retrieval-augmented Gemini responses
- Gemini integration for conversation replies, call summaries, and
  structured lead extraction (all JSON, with retry/backoff)
- Twilio outbound calling, TwiML webhook, status callback (signature-verified)
- Celery + Redis background job for post-call summary/extraction so the
  "end call" request returns instantly
- Centralized exception handling, structured logging (loguru), request
  logging middleware
- Repository pattern + service layer (SOLID, DI via FastAPI `Depends`)
- Docker Compose (API, Celery worker, MySQL, Redis), Dockerfile
- Alembic setup, admin-seed script, Postman collection, pytest scaffold

## What's intentionally NOT done yet

The **real-time call audio loop** (`app/websocket/media_stream.py`) is wired
up for connection lifecycle and event routing, but the actual audio
pipeline — voice-activity detection, mu-law↔PCM transcoding, streaming
Whisper transcription, and streaming TTS playback back to Twilio — is left
as the next milestone. That inner loop is the highest-risk part of this
system (latency, interruption handling, audio format correctness) and
deserves a dedicated pass with real call testing rather than being written
speculatively. The module docstring lays out the exact next steps.

The **React frontend** has not been scaffolded yet — say the word and it's next.

## Config profiles (local / staging / production)

Profile selection works like Spring's `spring.profiles.active`: an `APP_ENV`
environment variable — `local`, `staging`, or `production` — decides which
`.env.<profile>` file gets loaded. `APP_ENV` itself always comes from the
real process/shell environment, never from a file, so it's explicit every
time you start the app.

**First-time setup — create your three profile files:**

```bash
cp .env.local .env.local
cp .env.staging .env.staging
cp .env.production .env.production
# fill in real values in each — never commit these three files
```

**Running with Docker Compose:**

```bash
./scripts/use_env.sh local        # or: staging / production
docker compose up --build
```

`use_env.sh` copies the chosen `.env.<profile>` into the plain `.env` file
that Docker Compose reads automatically (both for its own `${VAR}`
interpolation — e.g. the `mysql` service's password — and for injecting
env vars into the `api`/`celery_worker` containers). The profile file
already contains `APP_ENV=<profile>`, so once it's copied in, the app
picks the matching settings automatically. Re-run the script and restart
Compose to switch profiles.

**Running without Docker (bare uvicorn on your host):**

```bash
APP_ENV=staging uvicorn app.main:app --reload
```

No script needed here — the app reads `.env.staging` directly since
`APP_ENV` is already set in your shell.

**What differs per profile:** `DEBUG`, `BASE_URL`, `CORS_ORIGINS`,
`JWT_EXPIRATION_HOURS`, and all the DB/Redis/API-key values. Production
also disables the interactive `/docs`, `/redoc`, and `/openapi.json`
endpoints automatically (`settings.is_production` gates this in `main.py`).

## Setup

See "Config profiles" above to set up your `.env.local` / `.env.staging` /
`.env.production` files first, then:

```bash
./scripts/use_env.sh local
docker compose up --build
```

The API auto-creates the MySQL database and tables on first boot (via
`ensure_database_exists()` + `init_models()`). For production, prefer
Alembic migrations instead:

```bash
docker compose exec api alembic revision --autogenerate -m "init"
docker compose exec api alembic upgrade head
```

Create your first admin user:

```bash
docker compose exec api python scripts/seed_admin.py
```

API docs: `http://localhost:8000/docs`

## Project structure

```
app/
  api/            REST route handlers
  auth/           JWT + password hashing + auth dependencies
  models/         SQLAlchemy ORM models (one file per table)
  schemas/        Pydantic request/response schemas
  database/       Async engine/session + auto DB creation
  repositories/   Generic + agent repository (data access layer)
  services/       Business logic (agent, auth, call, knowledge)
  agents/         Conversation orchestration (RAG + Gemini)
  llm/            Gemini client (replies, summaries, extraction)
  speech/         faster-whisper STT, ElevenLabs TTS
  telephony/      Twilio client, TwiML builder
  knowledge/      Chunking + ChromaDB client
  extraction/     Post-call summary/extraction processor
  websocket/      Twilio Media Streams handler
  workers/        Celery app + background tasks
  middleware/     Exception handling, request logging
  utils/          Logger
alembic/          Migrations
scripts/          Admin seed script
tests/            Pytest suite
```

## Security notes

- All secrets load from `.env` only — nothing is hardcoded.
- Twilio webhooks are signature-verified (`X-Twilio-Signature`).
- Passwords are bcrypt-hashed; JWTs are HS256-signed with a configurable expiry.
- Login is rate-limited (10/min per IP); all routes are rate-limited globally (120/min per IP).
- **If you ever paste real API keys into a chat, treat them as compromised and rotate them immediately.**

## Roadmap (suggested next iterations)

1. Real-time media-stream audio loop (VAD, transcoding, streaming STT/TTS)
2. React + Vite + Tailwind frontend (login, dashboard, agent/campaign/knowledge management, call history, analytics)
3. Analytics/dashboard aggregation endpoints
4. Full Alembic initial migration generated against a live MySQL instance
5. CI test run against a real MySQL test DB
