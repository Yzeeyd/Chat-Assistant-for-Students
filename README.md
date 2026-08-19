```markdown
# Student Assistant System

An AI-powered university assistant built with **Python, FastAPI, OpenAI models, and tool calling** to help students manage schedules, academic plans, reminders, grades, and university information through a conversational interface.

The system uses a **modular AI architecture with specialized operating modes** for text conversations, image understanding, timetable extraction, academic-plan processing, and university policy questions.

---

## Overview

The Student Assistant System allows university students to interact with academic services using natural language.

Students can:

- Ask questions about their schedule
- Upload timetable images
- Extract and save class schedules from images
- Upload academic-plan images
- Track completed and remaining courses
- Add reminders and assignments
- Track grades and absences
- Ask questions about university rules and regulations
- Interact with the system in Arabic or English

The backend is built using **FastAPI**, while AI tasks are handled through the **OpenAI API** with structured tool calling.

---

## Architecture

```text
                        User
                          |
                          v
                     FastAPI API
                          |
                          v
                  Request Classification
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
      Text Chat       Image Input     University Rules
          |               |                |
          v               v                v
     Chat Mode       Vision Modes       Rules Mode
                          |
                 +--------+--------+
                 |                 |
                 v                 v
           Schedule Import    Academic Plan Import

                          |
                          v
                    AI Runtime
                          |
                          v
                    Tool Calling
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
       Schedule        Reminders       Academic Plan
       Database          Grades           Rules
       Absences        Assignments       Documents
```

The project uses a **single AI runtime** with multiple specialized modes rather than independent agents.

Each mode uses different system instructions and behavior depending on the requested task.

---

## AI Modes

The AI runtime supports several specialized modes:

| Mode | Purpose |
|---|---|
| `MODE_CHAT` | General student assistant |
| `MODE_IMAGE_CHAT` | General image understanding |
| `MODE_SCHEDULE_IMPORT` | Extract timetable information from images |
| `MODE_PLAN_IMPORT_IMAGE` | Extract academic plans from images |
| `MODE_PLAN_IMPORT_TEXT` | Import academic plans from text/PDF content |
| `MODE_RULES` | Answer questions using university documents |

The system selects the appropriate mode depending on the user's request.

---

## Tool Calling

The language model can call application tools to interact with student data.

Examples include:

- Retrieve student schedule
- Save schedule sessions
- Clear an existing schedule
- Add reminders
- Track assignments
- Record grades
- Record absences
- Retrieve academic-plan information
- Search university rules
- Update student information

The AI runtime executes tool calls and returns their results back to the model before generating the final response.

```text
User Request
     |
     v
Language Model
     |
     v
Tool Call
     |
     v
Application Logic
     |
     v
Database / Documents
     |
     v
Tool Result
     |
     v
Language Model
     |
     v
Final Response
```

---

## Vision and Image Processing

The project supports multimodal image inputs.

Images are sent to a vision-capable AI model for tasks such as:

### Timetable Extraction

Students can upload an image of their university timetable.

The system extracts information such as:

- Course code
- Course name
- Day
- Start time
- End time
- Classroom
- Instructor
- Credit hours

The extracted sessions can then be saved to the student's account.

### Academic Plan Extraction

Students can also upload an image of their academic degree plan.

The system extracts:

- Course codes
- Course names
- Semester information
- Credit hours
- Course status

The extracted academic plan is stored and can later be queried conversationally.

### General Image Understanding

Users can upload other images and ask questions about their contents without saving the information.

---

## University Rules

The system can answer university policy questions using available university documents.

Examples include:

- Attendance policies
- Absence limits
- Academic warnings
- Registration rules
- Withdrawal policies
- Student rights
- Grading regulations

The AI is instructed to search the available university documents before answering policy-related questions.

This reduces unsupported answers and helps ground responses in university information.

---

## Backend

The backend is built using **FastAPI**.

Main API functionality includes:

```text
POST   /auth/signup
POST   /auth/login

POST   /chat
POST   /chat/with-image
POST   /chat/upload-schedule-image
POST   /chat/upload-plan-image
POST   /chat/university-rules

GET    /chat/history
DELETE /chat/history

GET    /dashboard/summary
GET    /dashboard/reminders/due
POST   /dashboard/reminders/{id}/done
DELETE /dashboard/reminders/{id}

GET    /health
```

FastAPI also provides interactive API documentation through Swagger.

```text
/docs
```

---

## Authentication

The application supports user authentication using:

- JWT access tokens
- Password hashing
- Authenticated API routes

Each student's academic data is associated with their own account.

---

## Database

The system uses **SQLAlchemy** for database operations.

Supported data includes:

- Users
- Schedules
- Academic plans
- Reminders
- Assignments
- Grades
- Absences
- Conversation history

The application supports SQLite by default and can also be configured to use MySQL.

---

## Conversation Memory

Recent conversation messages are stored and provided back to the AI model to maintain conversational context.

The number of stored messages can be configured through an environment variable.

```env
CHAT_MEMORY_MESSAGES=20
```

---

## Project Structure

```text
Chat-Assistant-for-Students/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes_auth.py
│   │   ├── routes_chat.py
│   │   ├── routes_dashboard.py
│   │   └── schemas.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── models.py
│   │   ├── crud.py
│   │   └── session.py
│   │
│   ├── services/
│   │   ├── ai/
│   │   │   └── runtime.py
│   │   │
│   │   ├── tools/
│   │   │   └── registry.py
│   │   │
│   │   ├── docs.py
│   │   └── schedule_parser.py
│   │
│   └── utils/
│       └── schedule.py
│
├── doc/
│   └── plans/
│
├── uploads/
│   └── rooms/
│
├── web/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

### Artificial Intelligence

- OpenAI API
- LLM applications
- Vision-capable models
- Tool calling
- Prompt engineering
- Structured AI workflows

### Database

- SQLAlchemy
- SQLite
- MySQL

### Security

- JWT Authentication
- Password hashing

### Document Processing

- PyMuPDF
- pypdf

### Deployment

- Docker
- Docker Compose

### Frontend

- HTML
- CSS
- JavaScript

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Yzeeyd/Chat-Assistant-for-Students.git
cd Chat-Assistant-for-Students
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Copy the example environment file:

```bash
copy .env.example .env
```

Configure the required variables:

```env
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_secret_key
```

Optional configuration:

```env
DATABASE_URL=
OPENAI_MODEL=
OPENAI_VISION_MODEL=
CHAT_MEMORY_MESSAGES=20
ENABLE_DOCS=true
```

---

## Run Locally

Start the FastAPI server:

```bash
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Run with Docker

Build and start the application:

```bash
docker-compose up --build
```

Stop the containers:

```bash
docker-compose down
```

---

## What This Project Demonstrates

This project demonstrates practical experience with:

- Building LLM-powered applications
- FastAPI backend development
- OpenAI API integration
- AI tool calling
- Multimodal image input
- Vision-based information extraction
- Prompt-based task specialization
- Request routing
- Database-backed AI applications
- Authentication
- Document-grounded responses
- Docker containerization
- Conversational application design

---

## Current Architecture Limitation

The current AI system uses a **shared runtime with specialized modes**.

It should not be considered a fully independent multi-agent system because the modes share:

- The same AI runtime
- The same tool execution loop
- A common tool registry

A future version may separate these responsibilities into independent agents with explicit orchestration and handoffs.

---

## Future Improvements

Possible future improvements include:

- Separate specialized AI agents
- Router agent with explicit agent handoffs
- Retrieval-Augmented Generation (RAG)
- Vector database integration
- Automated AI evaluation
- Unit and integration testing
- Improved observability and logging
- CI/CD pipeline
- Production cloud deployment
- Response quality monitoring

---

## Author

**Yazeed Mohammed Alanazi**

Computer Science student specializing in Artificial Intelligence.

GitHub:  
https://github.com/Yzeeyd
```
