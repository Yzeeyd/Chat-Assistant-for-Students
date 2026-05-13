<p align="center">
  <a href="./README.md">🇬🇧 English</a> | <a href="./README_ar.md">🇸🇦 العربية</a>
</p>

<h1 align="center">Student Assistant System</h1>

<p align="center">
  AI-powered assistant for students: manage your schedule, academic plan, reminders, and get answers to university policy questions — all through a conversational chat interface.
</p>

---

## Overview

A multi-agent FastAPI backend paired with a bilingual (Arabic/English) single-page web app. Students can:

- **Upload a timetable photo** → AI extracts and saves the weekly schedule
- **Upload a degree-plan image** → AI parses the color-coded semester grid
- **Chat naturally** to add reminders, query the schedule, or get course recommendations
- **Ask university questions** answered from official PDF documents

---

## Prerequisites

- Python 3.11 or newer
- An [OpenAI API key](https://platform.openai.com/api-keys)
- `pip` (bundled with Python)

---

## Quickstart (local)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd Chat-Assistant-for-Students

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
# Then open .env and set OPENAI_API_KEY and JWT_SECRET

# 5. Run the server
python -m uvicorn app.main:app --reload
```

Open your browser at **http://127.0.0.1:8000/**

- Swagger API docs: http://127.0.0.1:8000/docs *(set `ENABLE_DOCS=false` in production)*

---

## Docker Quickstart

```bash
# Build and start
docker-compose up --build

# Stop
docker-compose down
```

The container runs on **port 8000** and persists data across restarts using Docker volumes:

| Volume | Contents |
|--------|----------|
| `db_data` | SQLite database |
| `uploads_data` | Uploaded classroom photos |

> **Note:** Set `DATABASE_URL` in `docker-compose.yml` or `.env` if you want MySQL instead of SQLite.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | — | Your OpenAI secret key |
| `JWT_SECRET` | **Yes** | — | Any long random string — change before deploying |
| `DATABASE_URL` | No | SQLite | See `.env.example` for MySQL format |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Text agent model |
| `OPENAI_VISION_MODEL` | No | `gpt-4o` | Vision/OCR model (higher cost) |
| `CHAT_MEMORY_MESSAGES` | No | `20` | Past messages included in each AI request |
| `JWT_EXPIRE_MIN` | No | `1440` | Token expiry in minutes (1440 = 24 h) |
| `ENABLE_DOCS` | No | `true` | Set `false` to hide `/docs` in production |
| `CORS_ORIGINS` | No | `*` | Set to your domain in production |

---

## Project Structure

```
Chat-Assistant-for-Students/
├── app/
│   ├── main.py                        # FastAPI entry point, startup, CORS
│   ├── api/
│   │   ├── routes_auth.py             # POST /auth/signup, /auth/login
│   │   ├── routes_chat.py             # POST /chat, /chat/with-image, uploads
│   │   ├── routes_dashboard.py        # GET /dashboard/summary, reminders
│   │   └── schemas.py                 # Pydantic request/response schemas
│   ├── core/
│   │   ├── config.py                  # Loads .env, exposes typed settings
│   │   └── security.py                # JWT creation/verification, password hashing
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy ORM models
│   │   ├── crud.py                    # Database CRUD operations
│   │   └── session.py                 # Engine and session factory
│   ├── services/
│   │   ├── ai/runtime.py              # 5 agent modes + tool-calling loop
│   │   ├── tools/registry.py          # 19 tool definitions and executors
│   │   ├── docs.py                    # PDF/text loader for doc/ folder
│   │   └── schedule_parser.py         # Arabic day/time parsing utilities
│   └── utils/schedule.py              # Room image lookup, day-of-week helpers
├── doc/                               # University PDFs (regulations, FAQ, etc.)
│   └── plans/                         # Degree plan PDFs per major (CS_plan.pdf, etc.)
├── uploads/
│   └── rooms/                         # Classroom photos (matched by room code)
├── web/                               # Frontend SPA (index.html, style.css, app.js)
├── .env.example                       # Template — copy to .env and fill in values
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/auth/signup` | Register a new user account |
| `POST` | `/auth/login` | Log in, returns a JWT access token |
| `GET` | `/chat/history` | Fetch recent conversation messages |
| `DELETE` | `/chat/history` | Clear conversation history |
| `POST` | `/chat` | General-purpose AI assistant |
| `POST` | `/chat/with-image` | Image-aware assistant (auto-routes to schedule/plan agent) |
| `POST` | `/chat/upload-schedule-image` | Extract and save a weekly schedule from a photo |
| `POST` | `/chat/upload-plan-image` | Extract and save a degree plan from a photo |
| `POST` | `/chat/university-rules` | Answer policy questions from official PDF documents |
| `GET` | `/dashboard/summary` | Student data summary (schedule, reminders, plan stats) |
| `GET` | `/dashboard/reminders/due` | Due reminders (remind_at ≤ now) |
| `POST` | `/dashboard/reminders/{id}/done` | Mark a reminder as complete |
| `DELETE` | `/dashboard/reminders/{id}` | Delete a reminder |
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |

---

## Agent Architecture

The system uses **5 specialized AI agent modes**, all sharing the same tool set:

| Mode | Model | Forced Tools | Purpose |
|------|-------|:------------:|---------|
| `MODE_CHAT` | gpt-4o-mini | No | General assistant: schedule, reminders, plan |
| `MODE_IMAGE_CHAT` | gpt-4o | No | Answer questions about arbitrary images |
| `MODE_SCHEDULE_IMPORT` | gpt-4o | Yes | Extract class sessions from timetable photos |
| `MODE_PLAN_IMPORT_IMAGE` | gpt-4o | Yes | Extract degree plan from color-coded grid photos |
| `MODE_RULES` | gpt-4o-mini | Yes | Answer university policy questions from PDFs |

Each agent runs a tool-calling loop (max 6–8 rounds) until the model stops calling tools.

---

## Adding University Documents

Drop PDF files into the `doc/` folder. The university rules agent reads and searches them automatically — no database seeding needed.

For degree plan auto-import on signup, name files `doc/plans/{MAJOR}_plan.pdf` (e.g., `CS_plan.pdf`, `IT_plan.pdf`).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `sqlite3.OperationalError: database is locked` | Another process has the DB open. Stop it and restart. |
| `openai.AuthenticationError` | Check that `OPENAI_API_KEY` is set and valid in `.env`. |
| `429 Too Many Requests` from OpenAI | You have hit your rate limit. Wait and retry, or upgrade your plan. |
| Image upload fails silently | Make sure the file is under 10 MB and is a PNG/JPG/WEBP. |
| Schedule image not parsed correctly | Try a cleaner photo with higher contrast and visible column headers. |
| Port 8000 already in use | Run `uvicorn app.main:app --reload --port 8001` and update `BASE` in `web/app.js`. |

---

## Suggested Tests

The `tests/` directory is currently empty. Recommended tests to add with `pytest` + `httpx`:

```
tests/
├── test_auth.py          # signup, login, duplicate email, bad password
├── test_chat.py          # chat endpoint returns text, history is stored
├── test_dashboard.py     # summary returns correct structure, reminders CRUD
└── test_schedule.py      # parse_day, parse_time for Arabic time strings
```

Install test dependencies:
```bash
pip install pytest httpx
pytest tests/
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Uvicorn |
| Database | SQLite (default) / MySQL (optional) |
| ORM | SQLAlchemy |
| Authentication | JWT (python-jose) + pbkdf2_sha256 (passlib) |
| AI | OpenAI API — gpt-4o-mini (text), gpt-4o (vision) |
| PDF Parsing | PyMuPDF + pypdf |
| Frontend | Vanilla HTML/CSS/JS — no build step required |
| Language | Python 3.11+ |
| Containerization | Docker + Docker Compose |
