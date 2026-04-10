import json
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from . import models

# -------- USERS --------
def get_user_by_email(db: Session, email: str):
    email = email.strip().lower()
    return db.query(models.User).filter(func.lower(models.User.email) == email).first()

def create_user(db: Session, name: str, email: str, password_hash: str):
    user = models.User(name=name, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# -------- SCHEDULE --------
# إضافة عنصر جديد إلى الجدول مع منع التكرار
def add_schedule_item(db: Session, user_id: int, course_code: str, course_name: str, day_of_week: int, start_time, end_time, room_text: str, instructor: str | None ,credits: int):
    # منع التكرار
    exists = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.user_id == user_id,
            models.Schedule.course_code == course_code,
            models.Schedule.course_name == course_name,
            models.Schedule.day_of_week == day_of_week,
            models.Schedule.start_time == start_time,
            models.Schedule.end_time == end_time,
            models.Schedule.room_text == room_text,
            models.Schedule.credits == credits,
            models.Schedule.instructor == instructor,
        )
        .first()
    )
    if exists:
        return exists
    # إضافة العنصر الجديد
    item = models.Schedule(
        user_id=user_id,
        course_code=course_code,
        course_name=course_name,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room_text=room_text,
        instructor=instructor,
        credits=credits
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
# جلب جميع العناصر لليوم المحدد
def get_schedule_for_day(db: Session, user_id: int, day_of_week: int):
    return (
        db.query(models.Schedule)
        .filter(models.Schedule.user_id == user_id, models.Schedule.day_of_week == day_of_week)
        .order_by(models.Schedule.start_time)
        .all()
    )
# جلب جميع العناصر للمستخدم
def get_all_schedule(db: Session, user_id: int):
    return (
        db.query(models.Schedule)
        .filter(models.Schedule.user_id == user_id)
        .order_by(models.Schedule.day_of_week, models.Schedule.start_time)
        .all()
    )
# تحديث عنصر في الجدول بناءً على معرف الدورة التدريبية
def update_schedule_item(
    db: Session,
    course_id: int,
    user_id: int,
    **kwargs
):
    item = db.query(models.Schedule).filter(
        models.Schedule.id == course_id,
        models.Schedule.user_id == user_id
    ).first()

    if not item:
        return None

    for key, value in kwargs.items():
        if hasattr(item, key):
            setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item
# حذف عنصر واحد من الجدول بناءً على معرف الدورة التدريبية
def delete_one_schedule_item(db: Session, course_id: int, user_id: int) -> bool:
    item = db.query(models.Schedule).filter(models.Schedule.id == course_id, models.Schedule.user_id == user_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
# حذف جميع العناصر في الجدول للمستخدم
def delete_all_schedule(db: Session, user_id: int) -> int:
    count = db.query(models.Schedule).filter(models.Schedule.user_id == user_id).delete()
    db.commit()
    return count

# -------- CHAT MEMORY --------
def add_chat_message(db: Session, user_id: int, role: str, content: str, meta: dict | None = None):
    meta_json = json.dumps(meta, ensure_ascii=False) if meta else None
    msg = models.ChatMessage(user_id=user_id, role=role, content=content, meta_json=meta_json)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_last_chat_messages(db: Session, user_id: int, limit: int):
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == user_id)
        .order_by(models.ChatMessage.id.desc())
        .limit(limit)
        .all()[::-1]
    )

def trim_chat_messages(db: Session, user_id: int, keep_limit: int):
    db.execute(text("""
        DELETE FROM chat_messages
        WHERE user_id = :uid
          AND id NOT IN (
            SELECT id FROM (
              SELECT id
              FROM chat_messages
              WHERE user_id = :uid
              ORDER BY id DESC
              LIMIT :keep
            ) t
          )
    """), {"uid": user_id, "keep": keep_limit})
    db.commit()