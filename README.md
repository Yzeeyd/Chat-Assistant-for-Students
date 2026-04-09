# 🎓 Student Assistant System (AI-Powered)

An intelligent AI-powered assistant designed to support students throughout their academic journey — from schedule management to academic planning and smart recommendations.

---

## 🚀 Project Vision

This system is not فقط لإدارة الجداول، بل منصة ذكية تساعد الطالب في:

* 📅 إدارة الجدول الدراسي
* 🔔 التذكير بالمحاضرات والواجبات
* 📚 متابعة الخطة الدراسية
* 🤖 تقديم توصيات ذكية للتسجيل
* 📝 رفع وتسليم الواجبات
* 📖 فهم الأنظمة واللوائح الجامعية

---

## 🧠 Core Features

### ✅ Current Features

* 🔐 Authentication system (JWT)
* 💬 Chat-based AI interface
* 📅 Schedule parsing (Arabic & English)
* 🗂️ Save and retrieve student schedules
* 📸 Display classroom images

---

### 🔥 Upcoming Features (Next Phase)

#### 1️⃣ Academic Plan & Notifications

* 📊 Student academic plan tracking
* 🔔 Smart reminders (classes, assignments)
* 📤 Assignment upload system

#### 2️⃣ Smart Course Recommendation

* 🤖 Suggest courses for next semester
* 📈 Analyze student progress
* 🎯 Recommend optimal study plan

---

### 📅 Future Expansion (After 2 Weeks)

* 📚 Academic plan integration
* 🔔 Notifications system
* 📖 University rules & regulations assistant

---

## 🗓️ Important Timeline

* 📌 Next Development Phase: After 2 weeks
* 📅 Team Meeting: **22-04-2026**

---

## 🧱 Tech Stack

* **Backend:** FastAPI
* **Database:** MySQL
* **Authentication:** JWT (OAuth2)
* **AI:** OpenAI API (Function Calling)
* **Language:** Python

---

## 📂 Project Structure

```id="tree1"
app/
│
├── main.py                # Entry point
│
├── core/                 # Config & security
│   ├── config.py
│   └── security.py
│
├── db/                   # Database
│   ├── database.py
│   └── models.py
│
├── api/                  # Endpoints
│   ├── auth.py
│   ├── chat.py
│   └── schedule.py
│
├── services/             # Business logic
│   ├── ai_service.py
│   └── schedule_service.py
│
├── schemas/              # Validation
│   ├── user.py
│   └── schedule.py
│
├── utils/                # Helpers
│   └── helpers.py
```

---

## ⚙️ Installation

```bash id="install1"
git clone https://github.com/Yzeeyd/Chat-Assistant-for-Students.git
cd Student_bot
```

### Create virtual environment

```bash id="install2"
python -m venv .venv
```

### Activate

```bash id="install3"
.venv\Scripts\activate
```

### Install dependencies

```bash id="install4"
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create `.env` from example:

```bash id="env1"
cp .env.example .env
```

Fill in your values.

---

## ▶️ Run the Project

```bash id="run1"
python -m uvicorn app.main:app --reload
```

Swagger Docs:
👉 http://127.0.0.1:8000/docs

---

## 🔐 Authentication Flow

1. Register
2. Login → get token
3. Use token for protected routes

---

## 🤖 AI Capabilities

The system uses AI to:

* Understand messy schedules (Arabic/English)
* Extract structured data
* Automatically store schedules
* Answer student queries:

  * "What do I have today?"
  * "What should I register next semester?"

---

## 👥 Team Distribution

| Member    | Responsibility   |
| --------- | ---------------- |
| Student 1 | Authentication   |
| Student 2 | Database         |
| Student 3 | CRUD             |
| Student 4 | AI Integration   |
| Student 5 | Schedule Parsing |
| Student 6 | API & Testing    |

---

## 💡 Architecture

We designed the system using layered architecture:

* API Layer (Endpoints)
* Service Layer (Logic)
* Database Layer

This ensures:

* Scalability ✅
* Maintainability ✅
* Clean code structure ✅

---

## 🔥 Future Vision

The system can evolve into:

* 🎓 Full student assistant platform
* 📱 Mobile application
* 🧠 AI academic advisor
* 🔗 Integration with university systems

---

## 🏁 Authors

Developed by Computer Science (AI) Students 🎓
