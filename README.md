# Student Assistant System — Same Project Version

This version keeps everything in **one project**:
- FastAPI backend
- Web interface served by FastAPI
- JWT authentication
- Agentic AI orchestration with tool calls
- SQLite by default, easy to switch later

## What is included
- Signup / login
- Chat interface
- Dashboard summary
- Schedule tools
- Reminder tools
- Academic plan tools
- University rules search tools
- Assignments listing tool
- Room images support from `/uploads/rooms`

## Why this version
This is the best starting point for a graduation or course project when you want:
- one codebase
- easy local setup
- less integration complexity
- a visible UI for demos

Later, you can split the frontend into React or mobile if needed.

## Run
```bash
git clone <your-repo>
cd Student_bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Open:
- App: http://127.0.0.1:8000/
- Docs: http://127.0.0.1:8000/docs

## Default database
By default, this version uses SQLite:
```env
DATABASE_URL=sqlite+pysqlite:///./student_assistant.db
```

You can move to MySQL later without changing the project structure.

## Notes
- Add your OpenAI API key in `.env`
- Put classroom photos inside `uploads/rooms`
- The chat is grounded through tools to reduce hallucination for saved student data
