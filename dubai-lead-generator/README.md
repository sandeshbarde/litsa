# LITSA Lead Generator — Production Architecture & Operating Guide

[![Tests](https://img.shields.io/badge/tests-66%20passed-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)]()
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)]()
[![Celery](https://img.shields.io/badge/Celery-5.4+-37814A.svg)]()
[![Security](https://img.shields.io/badge/Security-SSRF%20Guard%20%2B%20JWT-blue.svg)]()

A high-throughput, fault-tolerant B2B Lead Generation, Business Intelligence, and AI Outreach platform designed to discover high-value businesses, diagnose revenue-leaking digital loopholes, generate custom interactive prototypes, and orchestrate automated outreach campaigns.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [End-to-End Pipeline Workflow](#end-to-end-pipeline-workflow)
3. [Production Security Hardening](#production-security-hardening)
4. [Technology Stack](#technology-stack)
5. [Directory Layout](#directory-layout)
6. [Quick Start & Local Setup](#quick-start--local-setup)
7. [Docker Compose Deployment](#docker-compose-deployment)
8. [Database Pooling & Alembic Migrations](#database-pooling--alembic-migrations)
9. [Asynchronous Celery Task Execution](#asynchronous-celery-task-execution)
10. [Configuration & Environment Variables](#configuration--environment-variables)
11. [API Endpoint Reference](#api-endpoint-reference)
12. [Pre-Flight Smoke Test](#pre-flight-smoke-test)
13. [Verification & Test Suite](#verification--test-suite)
14. [Developer Credentials & Contacts](#developer-credentials--contacts)

---

## System Architecture

```
                                  [ Browser / Client Dashboard ]
                                               │
                                      (HTTPS / Dynamic CORS)
                                               │
                                               ▼
                                 ┌───────────────────────────┐
                                 │      FastAPI Gateway      │
                                 │  • JWT Auth & Bcrypt      │
                                 │  • Security Headers       │
                                 │  • SSRF Shield Middleware │
                                 └─────────────┬─────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
         ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
         │ Discovery Engine    │    │ Intelligence & LLM  │    │ Email State Machine │
         │ • Resilient Engine  │    │ • Gemini 1.5/2.0    │    │ • ZeroBounce Audit  │
         │ • SerpApi Maps      │    │ • Anthropic Claude  │    │ • Suppression List  │
         │ • Apify Scraper     │    │ • Hot-Training Loop │    │ • Resend / SMTP     │
         │ • E.164 Normalizer  │    │ • Custom Prototypes │    │ • Webhooks Idemp.   │
         └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
                    │                          │                          │
                    └──────────────────────────┼──────────────────────────┘
                                               │
                    ┌──────────────────────────┴──────────────────────────┐
                    ▼                                                     ▼
         ┌─────────────────────────┐                           ┌─────────────────────┐
         │  PostgreSQL 16 Database │                           │   Redis 7 & Celery  │
         │  • Connection Pooling   │                           │   • Task Queues     │
         │  • Alembic Migrations   │                           │   • Discovery / Run │
         │  • Audit Logs & Events  │                           │   • Batch Outreach  │
         └─────────────────────────┘                           └─────────────────────┘
```

---

## End-to-End Pipeline Workflow

1. **Business Discovery**: Area × category search matrix executed via `ResilientDiscoveryEngine` with automatic failover across Apify and SerpApi with quota awareness.
2. **Contact & Deduplication**: Multi-attribute deduplication by Place ID, normalized E.164 phone numbers, and high-confidence name/area similarity.
3. **Website Presence Verification**: Multi-stage probe checking DNS, SSL, HTTP status, parked domain indicators, and redirect hops.
4. **SSRF Guard Protection**: All outbound checks routed through safe request validation blocking loopback, RFC 1918 private subnets, and cloud instance metadata (`169.254.169.254`).
5. **Decision Maker Intelligence**: Identifies CEO, Owner, or Managing Director names, direct email, and executive LinkedIn titles using Snov and Apollo.
6. **ZeroBounce Email Verification**: Strict fail-closed policy (`VALID` only allowed for dispatch; `INVALID`, `SPAMTRAP`, `ABUSE`, `DO_NOT_MAIL` quarantined).
7. **Forensic Loophole Diagnostics**: Diagnoses annual turnover, estimated revenue leak, and missing digital infrastructure.
8. **Live Prototype & Mockup**: Generates full interactive, branded prototype website on dynamic `PUBLIC_BASE_URL` with visitor interaction tracking (`/demo/{lead_id}`).
9. **Personalized Outreach Sequence**: Generates contextual, sequence-based cold email addressing the CEO with embed live prototype link and developer portfolio credentials.
10. **Delivery & Compliance Tracking**: Full audit tracking via `EmailLog`, automatic bounce/complaint suppression, and 1-click unsubscribe (`/api/v1/outreach/unsubscribe`).

---

## Production Security Hardening

- **JWT Authentication & Bcrypt**: Sensitive administrative endpoints (`/purge-existing-websites`, `/automation/credentials`, `/automation/dispatch-all`, `/jobs/start`, `/jobs/cancel`) require cryptographically signed Bearer tokens issued via `/api/v1/auth/login`.
- **Dynamic CORS**: Disallows wildcard `*` with credentials in production. Restricts allowed origins strictly to `FRONTEND_ORIGIN`.
- **SSRF Network Filter**: Validates all client and external URLs before network dispatch, resolving hostnames to IPs and rejecting loopback, link-local, private networks, and cloud instance metadata addresses (`169.254.169.254`).
- **Security Headers**: Standard ASGI middleware injecting `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Strict-Transport-Security` in production.
- **Fail-Closed Verification**: ZeroBounce integration prevents cold dispatch unless email is explicitly certified `VALID`. Missing keys, credit exhaustion, or network failures fail closed (`send_allowed=False`).
- **Zero Hardcoded Secrets**: Secrets and tokens are managed strictly via environment variables.

---

## Technology Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn, Pydantic v2
- **Database & ORM**: PostgreSQL 16, SQLite (local fallback), SQLAlchemy 2.0, Alembic
- **Task Queue & Caching**: Celery 5.4+, Redis 7
- **AI & LLM Services**: Google Gemini 1.5/2.0 (`google-generativeai`), Anthropic Claude 3 (`anthropic`)
- **Discovery & Data Providers**: SerpApi Google Maps, Apify Actor (`compass/crawler-google-places`), Snov.io, Apollo.io
- **Deliverability & Verification**: ZeroBounce API v2, Resend API, Gmail SMTP (TLS)
- **Phone Number Parsing**: Google `phonenumbers` library (E.164 compliance)
- **Frontend Dashboard**: Responsive Tailwind CSS Single-Page Application

---

## Directory Layout

```
dubai-lead-generator/
├── alembic/                    # Database migrations
│   ├── versions/               # Versioned migration files
│   └── env.py                  # Alembic runtime config
├── app/
│   ├── main.py                 # FastAPI application & middleware
│   ├── config.py               # Pydantic Settings & dynamic URL helpers
│   ├── models.py               # SQLAlchemy ORM models
│   ├── api/                    # SerpApi clients (maps, search, reviews)
│   ├── database/               # Database engine, session, repositories
│   ├── routes/                 # API route handlers
│   │   ├── auth.py             # JWT login, me, logout
│   │   ├── jobs.py             # Discovery job lifecycle
│   │   ├── leads.py            # Lead collection, diagnosis, pitches, demo
│   │   ├── webhooks.py         # Resend webhooks & unsubscribe
│   │   └── sync.py             # Sheets sync
│   ├── services/               # Core business services
│   │   ├── discovery.py        # Pipeline orchestrator
│   │   ├── discovery_provider.py # Resilient provider abstraction
│   │   ├── contact_provider.py # Apollo & Snov provider abstraction
│   │   ├── email_automation.py # Outreach state machine & audit log
│   │   ├── zerobounce_service.py # Deliverability verification
│   │   ├── location_config.py  # Global multi-city locale registry
│   │   ├── loophole_service.py # Commercial diagnosis
│   │   └── pitch_generator.py  # CEO pitch & mockup HTML builder
│   ├── tasks/                  # Celery worker configuration
│   │   ├── celery_app.py       # Celery application instance
│   │   └── worker.py           # Background async tasks
│   └── utils/                  # Security & formatting utilities
│       ├── auth.py             # JWT tokens & password hashing
│       ├── ssrf.py             # SSRF network shield
│       └── normalization.py    # E.164 and text normalization
├── dashboard/                  # Production Single-Page Application
├── scripts/
│   └── smoke_test.py           # Pre-flight production check
├── tests/                      # Pytest unit & integration test suite
├── Dockerfile                  # Multi-stage production container build
├── docker-compose.yml          # FastAPI, PostgreSQL, Redis, Celery stack
├── requirements.txt            # Python dependencies
└── .env.example                # Clean production variable template
```

---

## Quick Start & Local Setup

### 1. Prerequisites
- Python 3.11+ (Python 3.12 recommended)
- Git

### 2. Clone & Setup Virtual Environment
```bash
cd dubai-lead-generator
python -m venv .venv

# Activate on Windows:
.\.venv\Scripts\activate

# Activate on macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials (API keys, admin password, database URL)
```

### 5. Run Database Migrations
```bash
alembic upgrade head
```

### 6. Start Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Access the Dashboard at `http://localhost:8000/dashboard` or API documentation at `http://localhost:8000/docs`.

---

## Docker Compose Deployment

The entire production stack can be launched with one command:

```bash
docker compose up --build -d
```

This provisions:
- **`db`**: PostgreSQL 16 on port `5432` with persistent Docker volume
- **`redis`**: Redis 7 on port `6379` with AOF persistence
- **`web`**: FastAPI application on port `8000` with non-root security container
- **`celery_worker`**: Celery worker executing background discovery and outreach

### View Container Logs
```bash
docker compose logs -f web
docker compose logs -f celery_worker
```

### Stop Containers
```bash
docker compose down
```

---

## Database Pooling & Alembic Migrations

The database configuration in `app/database/db.py` automatically detects PostgreSQL vs SQLite. For PostgreSQL:
- `pool_size=10`
- `max_overflow=20`
- `pool_pre_ping=True` (auto-reconnects dropped connections)
- `pool_recycle=300` (refreshes stale connections)

### Generating Migrations
```bash
alembic revision --autogenerate -m "description_of_change"
alembic upgrade head
```

---

## Asynchronous Celery Task Execution

Start Celery worker locally:
```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info -c 2
```

Available Task Queues:
- `discovery`: Asynchronous lead searches across area × category matrices
- `outreach`: Controlled throttle-rate email dispatches
- `verification`: Background ZeroBounce email deliverability validation

---

## Configuration & Environment Variables

| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | Application environment (`development` / `production`) | `production` |
| `PUBLIC_BASE_URL` | Public domain for recipient demo links | `http://127.0.0.1:8000` |
| `FRONTEND_ORIGIN` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |
| `DATABASE_URL` | PostgreSQL or SQLite connection URI | `sqlite:///./dubai_leads.db` |
| `REDIS_URL` | Redis URI for Celery broker and cache | `redis://localhost:6379/0` |
| `ADMIN_EMAIL` | Administrative login username | `admin@litsa.io` |
| `ADMIN_PASSWORD_HASH` | Bcrypt hash for admin password | Auto-generated |
| `JWT_SECRET` | Secret key for JWT signing | 64-char random hex |
| `SERPAPI_API_KEY` | SerpApi Google Maps API Key | Optional (if Apify used) |
| `APIFY_API_TOKEN` | Apify Actor API Token | Optional (if SerpApi used) |
| `ZEROBOUNCE_API_KEY` | ZeroBounce validation key | Optional |
| `GEMINI_API_KEY` | Google Gemini AI key | Optional |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Optional |
| `RESEND_API_KEY` | Resend API key for transactional emails | Optional |
| `SMTP_HOST` / `SMTP_PORT` | SMTP server host and port | `smtp.gmail.com:587` |
| `SMTP_USERNAME` | SMTP account email | Optional |
| `SMTP_PASSWORD` | SMTP 16-letter Gmail App Password | Optional |

---

## API Endpoint Reference

### Authentication
- `POST /api/v1/auth/login`: Authenticate admin and receive JWT access token.
- `GET /api/v1/auth/me`: Retrieve current admin profile.
- `POST /api/v1/auth/logout`: Invalidate session.

### Lead Management & Intelligence
- `GET /leads`: Query leads with filters (`lead_priority`, `website_status`, `city`, `category`, pagination).
- `GET /leads/{lead_id}`: Retrieve detailed lead record.
- `GET /leads/{lead_id}/loophole-research`: Commercial forensic diagnosis.
- `POST /leads/{lead_id}/generate-pitch`: Generate tailored CEO cold proposal with demo link.
- `GET /leads/{lead_id}/demo`: Serve full interactive live prototype website.
- `GET /leads/{lead_id}/deep-proposal`: Generate executive investment and ROI deliverables proposal.

### Prototype Interaction Tracking
- `POST /leads/{lead_id}/demo-interaction`: Track visitor telemetry (page views, scroll depth, time on prototype).
- `POST /leads/{lead_id}/demo-form-submit`: Record prospective client inquiries submitted through the demo mockup.

### Automated Outreach & Webhooks
- `POST /leads/{lead_id}/send-email`: Send audited outreach email.
- `POST /leads/automation/dispatch-all`: Autopilot batch outreach to uncontacted leads.
- `POST /api/v1/webhooks/resend`: Resend email delivery/bounce webhook handler (idempotent).
- `GET /api/v1/outreach/unsubscribe`: 1-Click unsubscribe handler.

### Job Orchestration
- `POST /jobs/start`: Launch background discovery run.
- `GET /jobs`: List historical search jobs.
- `POST /jobs/{job_id}/pause`: Pause active search job.
- `POST /jobs/{job_id}/resume`: Resume paused search job.
- `POST /jobs/{job_id}/cancel`: Cancel active search job.

---

## Pre-Flight Smoke Test

Run the automated pre-flight checklist before production traffic:

```bash
python scripts/smoke_test.py
```

Validates:
1. Database connectivity
2. Redis cache and Celery broker reachability
3. API credentials and provider status (with safe key masking)
4. SSRF shield network security
5. Phone number normalization and E.164 engine
6. Public demo URL resolution

---

## Verification & Test Suite

Run the full automated test suite with pytest:

```bash
pytest tests/ -v
```

Test Coverage Includes:
- `test_auth.py`: JWT token signing, bcrypt verification, authentication routes
- `test_ssrf.py`: Cloud metadata blocking, loopback prevention, public URL access
- `test_normalization.py`: E.164 phone formats, address and business name cleaning
- `test_webhooks_and_suppression.py`: Bounces, suppression list checks, 1-click unsubscribe, webhook idempotency
- `test_demo_interactions.py`: Prototype interactions and demo inquiry submissions
- `test_leads_api.py`: Lead filtering, pagination, automation status
- `test_zerobounce.py`: Deliverability validation and fail-closed security
- `test_claude.py`: Claude pitch generation and fallback mechanics
- `test_deduplication.py`: Duplicate detection across Place ID, phone, and name/area pairs
- `test_lead_scoring.py`: Transparent lead qualification scoring algorithm
- `test_verification.py`: Website health and status determination

---

## Developer Credentials & Contacts

**Lead Architect & Full-Stack Developer:**
- **Name**: Sandesh Barde
- **Location**: India
- **Portfolio**: [https://sandeshbarde.netlify.app/](https://sandeshbarde.netlify.app/)
- **GitHub**: [https://github.com/sandeshbarde](https://github.com/sandeshbarde)
- **LinkedIn**: [https://www.linkedin.com/in/sandesh-barde-26ba3839b/](https://www.linkedin.com/in/sandesh-barde-26ba3839b/)
