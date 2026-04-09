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

    assistant_text, last_items = run_agent(history, max_rounds=6, db=db, user=user)

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