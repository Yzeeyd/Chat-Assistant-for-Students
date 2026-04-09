import os
import json
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from . import models, schemas, crud
from .auth import hash_password, verify_password, create_access_token, get_current_user
from .utils import today_dow_1_to_7, normalize_room_text
from .ai import run_agent  

Base.metadata.create_all(bind=engine)

# نخفي /docs و /openapi للمستخدم
app = FastAPI(
    title="Student Chat",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = os.path.join(os.getcwd(), "uploads")
ROOMS_DIR = os.path.join(UPLOADS_DIR, "rooms")

os.makedirs(ROOMS_DIR, exist_ok=True) #ينشاء ملف للصور ويتاكد انه موجود
app.mount("/static", StaticFiles(directory=UPLOADS_DIR), name="static")

CHAT_MEMORY = int(os.getenv("CHAT_MEMORY_MESSAGES", "20"))
#دالة ايجاد الصور
def find_room_image(room_text: str) -> str | None:
    room_text = normalize_room_text(room_text)

    for ext in (".png", ".jpg", ".jpeg"):
        filename = f"{room_text}{ext}"
        path = os.path.join(ROOMS_DIR, filename)
        if os.path.exists(path):
            return f"/static/rooms/{filename}"
    return None

# -------- AUTH --------
@app.post("/auth/signup")
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already exists")

    user = crud.create_user(
        db=db,
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )
    return {"id": user.id, "name": user.name, "email": user.email}

@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = crud.get_user_by_email(db, email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    token = create_access_token(user.id)
    return schemas.TokenResponse(access_token=token)

# -------- HISTORY (يعرض الشات السابق) --------
@app.get("/chat/history")
def chat_history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    msgs = crud.get_last_chat_messages(db, user_id=user.id, limit=CHAT_MEMORY)
    out = []
    for m in msgs:
        out.append({
            "role": m.role,
            "content": m.content,
            "meta_json": m.meta_json,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    return out

# -------- CHAT --------
@app.post("/chat", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    user_text = (payload.message or "").strip()
    if not user_text:
        return schemas.ChatResponse(text="اكتب رسالتك 🙂", items=[])

    # خزن رسالة المستخدم
    crud.add_chat_message(db, user_id=user.id, role="user", content=user_text)

    # جيب آخر N رسائل
    msgs = crud.get_last_chat_messages(db, user_id=user.id, limit=CHAT_MEMORY)
    history = [{"role": m.role, "content": m.content} for m in msgs]

    # أدوات الجدول
    def tool_add_class(course_name: str, day_of_week: int, start_time: str, end_time: str, room_text: str):
        st = datetime.strptime(start_time, "%H:%M").time()
        et = datetime.strptime(end_time, "%H:%M").time()
        room = normalize_room_text(room_text)
        crud.add_schedule_item(db, user_id=user.id, course_name=course_name.strip(),
                              day_of_week=int(day_of_week), start_time=st, end_time=et, room_text=room)
        return {"ok": True}

    def tool_bulk_add_classes(items: list[dict]):
        added = 0
        for it in items:
            try:
                tool_add_class(
                    course_name=str(it["course_name"]),
                    day_of_week=int(it["day_of_week"]),
                    start_time=str(it["start_time"]),
                    end_time=str(it["end_time"]),
                    room_text=str(it["room_text"]),
                )
                added += 1
            except Exception:
                continue
        return {"ok": True, "added": added}

    def tool_get_today_schedule():
        dow = today_dow_1_to_7()
        sessions = crud.get_schedule_for_day(db, user_id=user.id, day_of_week=dow)
        items = []
        for s in sessions:
            img = find_room_image(s.room_text)
            items.append({
                "course_name": s.course_name,
                "start_time": str(s.start_time)[:5],
                "end_time": str(s.end_time)[:5],
                "room_text": s.room_text,
                "image_url": img,
            })
        return {"ok": True, "items": items}

    def tool_get_schedule_for_day(day_of_week: int):
        sessions = crud.get_schedule_for_day(db, user_id=user.id, day_of_week=int(day_of_week))
        items = []
        for s in sessions:
            img = find_room_image(s.room_text)
            items.append({
                "course_name": s.course_name,
                "start_time": str(s.start_time)[:5],
                "end_time": str(s.end_time)[:5],
                "room_text": s.room_text,
                "image_url": img,
            })
        return {"ok": True, "items": items}

    def tool_clear_schedule():
        deleted = crud.delete_all_schedule(db, user_id=user.id)
        return {"ok": True, "deleted": deleted}

    tool_handlers = {
        "add_class": tool_add_class,
        "bulk_add_classes": tool_bulk_add_classes,
        "get_today_schedule": tool_get_today_schedule,
        "get_schedule_for_day": tool_get_schedule_for_day,
        "clear_schedule": tool_clear_schedule,
    }

    assistant_text, last_items = run_agent(history, tool_handlers)

    # جهّز items للواجهة + خزّنها في meta_json عشان تظهر في history
    items_out = []
    meta = None
    if isinstance(last_items, list):
        meta = {"items": last_items}
        for it in last_items:
            items_out.append(schemas.ScheduleItemOut(
                course_name=it.get("course_name", ""),
                start_time=it.get("start_time", ""),
                end_time=it.get("end_time", ""),
                room_text=it.get("room_text", ""),
                image_url=it.get("image_url"),
            ))

    crud.add_chat_message(db, user_id=user.id, role="assistant", content=assistant_text, meta=meta)
    crud.trim_chat_messages(db, user_id=user.id, keep_limit=CHAT_MEMORY)

    return schemas.ChatResponse(text=assistant_text, items=items_out)


WEB_DIR = os.path.join(os.getcwd(), "web")
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")