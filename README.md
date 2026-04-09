# 🎓 Student Assistant Chatbot

An AI-powered chat assistant designed to help students manage their academic schedules using a simple conversational interface.

---

## 🚀 Features

* 🔐 User Authentication (JWT-based login system)
* 💬 Chat-based interface (like ChatGPT)
* 📅 Save and manage student schedules
* 📸 Room image retrieval (based on room number)
* 🧠 AI-powered schedule understanding (Arabic & English)
* ⚡ FastAPI backend for high performance

---

## 🧱 Tech Stack

* **Backend:** FastAPI
* **Database:** MySQL
* **Authentication:** JWT (OAuth2)
* **AI Integration:** OpenAI API (Function Calling)
* **Environment:** Python (venv)

---

## 📂 Project Structure

```
student_bot/
│
├── app/
│   ├── main.py          # Entry point (FastAPI app)
│   ├── models.py        # Database models
│   ├── db.py            # Database connection
│   ├── auth.py          # Authentication logic
│   ├── crud.py          # Database operations
│   ├── schemas.py       # Pydantic schemas
│   ├── utils.py         # Helper functions
│   ├── ai.py            # AI logic & tool calling
│
├── uploads/             # Uploaded schedules/images
├── .env                 # Environment variables
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

```bash
git clone https://github.com/Yzeeyd/Chat-Assistant-for-Students.git
cd Student_bot
```

### Create virtual environment

```bash
python -m venv .venv
```

### Activate it

```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Project

```bash
python -m uvicorn app.main:app --reload
```

Then open:
👉 http://127.0.0.1:8000/docs

---

## 🔐 Authentication Flow

1. Register a user
2. Login → get access token
3. Use token for protected endpoints

---

## 🤖 AI Capabilities

The chatbot can:

* Understand schedule text (Arabic/English)
* Extract:

  * Course name
  * Time
  * Day
  * Room
* Save data automatically
* Answer:

  * "What do I have today?"
  * "What do I have tomorrow?"

---

## 📸 Room Images

Room images are stored locally and returned when:

* User asks about a class
* Room is available in database

---

## 🧠 Smart Parsing

Custom normalization handles:

* Arabic text
* Mixed formatting
* Irregular tables

---

## 👥 Team Work Distribution

| Member    | Responsibility            |
| --------- | ------------------------- |
| Student 1 | Authentication (JWT)      |
| Student 2 | Database (MySQL + Models) |
| Student 3 | CRUD Operations           |
| Student 4 | AI Integration            |
| Student 5 | Schedule Parsing          |
| Student 6 | API Integration & Testing |

---

## 📌 Future Improvements

* Frontend UI (React)
* Mobile app
* Notifications
* Calendar integration

---

## 💡 Notes

This project is designed with scalability in mind and can be extended into a production-level student assistant system.

---

## 🏁 Author

Developed by CS-AI Students 🎓
