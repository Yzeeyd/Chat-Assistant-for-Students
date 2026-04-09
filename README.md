# 🎓 Student Assistant System (AI-Powered)
# 🇬🇧 English Version
🌐 Language:
- 🇬🇧 English (Current)
- 🇸🇦 [العربية](./README_ar.md)
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

## ⚙️ Installation

### 1) Clone the repository

```bash
git clone https://github.com/Yzeeyd/Chat-Assistant-for-Students.git
cd Student_bot
```

### 2) Create a virtual environment

```bash
python -m venv .venv
```

### 3) Activate the environment

```bash
.venv\Scripts\activate
```

### 4) Install dependencies

```bash
pip install -r requirements.txt
```

### 5) Configure environment variables

Copy `.env.example` to `.env` and fill in your own values.

### 6) Run the project

```bash
python -m uvicorn app.main:app --reload
```

---

## 🌐 API Documentation

After running the project, open:

```text
http://127.0.0.1:8000/docs
```

---

## 🤖 AI Capabilities

The system can:

* Understand messy input text
* Extract:

  * Course name
  * Day
  * Lecture time
  * Room number
* Automatically save schedules
* Answer questions such as:

  * "What do I have today?"
  * "What do I have tomorrow?"
  * "What should I register next semester?"

---

## 🧠 Architecture

The project is designed using a layered architecture:

* **API Layer**
* **Service / Logic Layer**
* **Database Layer**

This ensures:

* Scalability ✅
* Maintainability ✅
* Clean code structure ✅

---

## 👥 Team Distribution

| Member    | Responsibility            |
| --------- | ------------------------- |
| Student 1 | Authentication            |
| Student 2 | Database                  |
| Student 3 | CRUD Operations           |
| Student 4 | AI Integration            |
| Student 5 | Schedule Parsing          |
| Student 6 | API Testing & Integration |

---

## 🔮 Future Vision

The system can later evolve into:

* A full student support platform
* An AI academic advisor
* A mobile application
* A system integrated with university services

---

## 🏁 Authors

Developed by Computer Science (AI) Students 🎓
