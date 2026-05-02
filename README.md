<p align="center">
  <a href="./README.md">🇬🇧 English</a> | <a href="./README_ar.md">🇸🇦 العربية</a>
</p>

<h1 align="center">Student Assistant System</h1>

<p align="center">
  AI-powered assistant for students: schedules, academic planning, reminders, course recommendations, and university rules.
</p>

---

## Project Vision

An AI-powered Student Assistant that supports students throughout their academic journey via a simple conversational chat interface. The system manages personal academic data and answers questions grounded in saved information and official university documents.

---

## Current Features

- **Authentication** — JWT-based signup and login
- **Schedule Management** — Add, view, update, and delete weekly class schedule; supports Arabic and English; bulk import from text or image
- **Reminders** — Create, list, and complete reminders for homework, exams, deadlines, and personal tasks
- **Academic Plan Tracking** — Import and manage degree plan courses with status (planned / in_progress / completed); bulk import from image
- **Course Recommendations** — Suggest next courses based on the student's saved academic plan
- **University Rules** — Answer questions about regulations using the official university PDF documents in the `doc/` folder
- **Classroom Image Display** — Show room photos when viewing the schedule
- **Image Upload Support** — Import schedule or degree plan directly from a photo

---

## API Routes

| Method | Route | Agent / Purpose |
|--------|-------|-----------------|
| `POST` | `/auth/signup` | User registration |
| `POST` | `/auth/login` | Login, returns JWT |
| `GET` | `/chat/history` | Fetch conversation history |
| `POST` | `/chat` | General-purpose assistant agent |
| `POST` | `/chat/with-image` | Image-aware agent (auto-routes to schedule or plan agent) |
| `POST` | `/chat/upload-schedule-image` | Schedule import agent — extracts and saves classes from image |
| `POST` | `/chat/upload-plan-image` | Academic plan import agent — extracts degree plan from image |
| `POST` | `/chat/university-rules` | University rules agent — searches official `doc/` PDFs |
| `GET` | `/dashboard/summary` | Student data summary (schedule, reminders, plan stats) |
| `GET` | `/health` | Health check |

---

## Agent Architecture

The system uses specialized agents, each with focused instructions and tool access:

- **General Agent** (`run_agent`) — handles all chat messages; routes to the right tool (schedule, reminders, plan, rules search)
- **Schedule Image Agent** (`run_schedule_image_agent`) — dedicated to extracting class schedules from uploaded images
- **Academic Plan Image Agent** (`run_academic_plan_image_agent`) — dedicated to extracting degree plans from uploaded images
- **Image Chat Agent** (`run_agent_with_image`) — answers questions about arbitrary uploaded images
- **University Rules Agent** (`run_university_rules_agent`) — answers regulation questions using `search_university_rules`, which searches the PDF files in `doc/`

The university rules tool searches the SQLite `university_rules` table first, then falls back to keyword search across the PDF documents in `doc/`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI |
| Database | SQLite (default) / MySQL (optional) |
| Authentication | JWT / OAuth2 |
| AI | OpenAI API (`gpt-4o-mini` default) |
| Language | Python 3.11+ |
| PDF parsing | pypdf |

---

## Project Structure

```
Chat-Assistant-for-Students/
├── app/
│   ├── main.py                        # FastAPI app entry point
│   ├── api/
│   │   ├── routes_auth.py             # /auth routes
│   │   ├── routes_chat.py             # /chat routes (all agents)
│   │   ├── routes_dashboard.py        # /dashboard route
│   │   └── schemas.py                 # Pydantic schemas
│   ├── core/
│   │   ├── config.py                  # Environment config
│   │   └── security.py                # JWT & password hashing
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy models
│   │   ├── crud.py                    # Database operations
│   │   └── session.py                 # DB connection
│   ├── services/
│   │   ├── ai/
│   │   │   └── runtime.py             # All agent functions
│   │   ├── tools/
│   │   │   └── registry.py            # Tool definitions & execution
│   │   └── docs.py                    # PDF loader for doc/ folder
│   └── utils/
│       └── schedule.py                # Room image matching, time helpers
├── doc/                               # University PDF documents (base knowledge)
├── uploads/
│   └── rooms/                         # Classroom photos
├── web/                               # Frontend (optional)
├── .env.example
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone and set up

```bash
git clone <your-repo>
cd Chat-Assistant-for-Students
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env
```

### 2. Configure `.env`

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite+pysqlite:///./student_assistant.db
```

### 3. Run

```bash
python -m uvicorn app.main:app --reload
```

- App: http://127.0.0.1:8000/
- API Docs: http://127.0.0.1:8000/docs

---

## University Documents

Place PDF files (regulations, student charter, code of conduct) inside the `doc/` folder. The university rules agent reads and searches them automatically — no database seeding required.