<p align="center">
  <a href="./README.md">🇬🇧 English</a> | <a href="./README_ar.md">🇸🇦 العربية</a>
</p>

<h1 align="center">🎓 Student Assistant System</h1>

<p align="center">
  AI-powered assistant for students: schedules, academic planning, reminders, recommendations, and university guidance.
</p>

---
## 🚀 Project Vision

This project is not only for schedule management. It is an **AI-powered Student Assistant System** designed to support students throughout their academic journey using a simple conversational interface.

The system aims to help students with:

* 📅 Schedule management
* 🔔 Smart reminders and notifications
* 📚 Academic plan tracking
* 🤖 Course recommendations
* 📤 Assignment uploads
* 📖 University rules and regulations

---

## ✅ Current Features

* 🔐 JWT-based authentication system
* 💬 Chat-based interface similar to ChatGPT
* 📅 Arabic and English schedule parsing
* 🗂️ Save and retrieve student schedules
* 📸 Classroom image display
* 🧠 Automatic extraction of structured schedule data from unorganized text

---

## 🔥 Upcoming Goals

### 1) Academic Plan + Notifications + Assignment Uploads

* Track the student's academic plan
* Send reminders for classes and tasks
* Support assignment uploads

### 2) Smart Course Recommendation

* Analyze student academic progress
* Suggest courses for the next semester
* Help students make better registration decisions

### After Two Weeks

* Academic planning
* Smart notifications
* University rules and regulations support

📅 **Meeting Date:** 22-04-2026

---

## 🧱 Tech Stack

* **Backend:** FastAPI
* **Database:** MySQL
* **Authentication:** JWT / OAuth2
* **AI Integration:** OpenAI API
* **Language:** Python

---

## 📂 Project Structure

```text
student_bot/
│
├── app/
│   ├── main.py              # Project entry point
│   ├── ai.py                # AI logic and tool calling
│   ├── auth.py              # Authentication logic
│   ├── crud.py              # Database operations
│   ├── db.py                # Database connection
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   └── utils.py             # Helper functions
│
├── uploads/                 # Uploaded files
├── web/                     # Frontend files if available
├── .env.example             # Example environment variables
├── .gitignore               # Ignored files
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

---
## ⚙️ Requierments Before Installation

### 1) Download Mysql database

```
https://www.mysql.com/
```
### 2) setup Mysql database

```
and create database in quiry using this command
```

```bash
create database name_your_dataBase_Here
```

## ⚙️ Installation

### 1) Clone the repository

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
