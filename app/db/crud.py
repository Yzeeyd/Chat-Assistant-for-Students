import json
from datetime import datetime, time
from typing import Iterable

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db import models


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(func.lower(models.User.email) == email.strip().lower()).first()


def create_user(
    db: Session,
    name: str,
    email: str,
    password_hash: str,
    college: str | None = None,
    major: str | None = None,
    track: str | None = None,
) -> models.User:
    user = models.User(
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=password_hash,
        college=college.strip() if college else None,
        major=major.upper().strip() if major else None,
        track=track.strip() if track else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# chat memory
# ---------------------------------------------------------------------------

def add_chat_message(db: Session, user_id: int, role: str, content: str, meta: dict | None = None) -> models.ChatMessage:
    msg = models.ChatMessage(
        user_id=user_id,
        role=role,
        content=content,
        meta_json=json.dumps(meta, ensure_ascii=False) if meta else None,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_last_chat_messages(db: Session, user_id: int, limit: int) -> list[models.ChatMessage]:
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == user_id)
        .order_by(models.ChatMessage.id.desc())
        .limit(limit)
        .all()[::-1]
    )


def trim_chat_messages(db: Session, user_id: int, keep_limit: int) -> None:
    rows = get_last_chat_messages(db, user_id, keep_limit)
    keep_ids = [r.id for r in rows]
    q = db.query(models.ChatMessage).filter(models.ChatMessage.user_id == user_id)
    if keep_ids:
        q = q.filter(~models.ChatMessage.id.in_(keep_ids))
    q.delete(synchronize_session=False)
    db.commit()


# ---------------------------------------------------------------------------
# schedule
# ---------------------------------------------------------------------------

def add_schedule_item(
    db: Session,
    user_id: int,
    course_code: str | None,
    course_name: str,
    day_of_week: int | None,
    start_time: time | None,
    end_time: time | None,
    room_text: str,
    instructor: str | None,
    credits: int | None,
) -> models.ScheduleItem:
    q = (
        db.query(models.ScheduleItem)
        .filter(
            models.ScheduleItem.user_id == user_id,
            models.ScheduleItem.course_name == course_name,
            models.ScheduleItem.room_text == room_text,
        )
    )
    if day_of_week is None:
        q = q.filter(models.ScheduleItem.day_of_week.is_(None))
    else:
        q = q.filter(models.ScheduleItem.day_of_week == day_of_week)
    if start_time is None:
        q = q.filter(models.ScheduleItem.start_time.is_(None))
    else:
        q = q.filter(models.ScheduleItem.start_time == start_time)
    exists = q.first()
    if exists:
        return exists

    item = models.ScheduleItem(
        user_id=user_id,
        course_code=course_code or None,
        course_name=course_name,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room_text=room_text,
        instructor=instructor,
        credits=credits,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_schedule_for_day(db: Session, user_id: int, day_of_week: int) -> list[models.ScheduleItem]:
    return (
        db.query(models.ScheduleItem)
        .filter(models.ScheduleItem.user_id == user_id, models.ScheduleItem.day_of_week == day_of_week)
        .order_by(models.ScheduleItem.start_time)
        .all()
    )


def get_all_schedule(db: Session, user_id: int) -> list[models.ScheduleItem]:
    return (
        db.query(models.ScheduleItem)
        .filter(models.ScheduleItem.user_id == user_id)
        .order_by(models.ScheduleItem.day_of_week, models.ScheduleItem.start_time)
        .all()
    )


def update_schedule_item(db: Session, course_id: int, user_id: int, **kwargs) -> models.ScheduleItem | None:
    item = (
        db.query(models.ScheduleItem)
        .filter(models.ScheduleItem.id == course_id, models.ScheduleItem.user_id == user_id)
        .first()
    )
    if not item:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(item, key):
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_one_schedule_item(db: Session, course_id: int, user_id: int) -> bool:
    item = (
        db.query(models.ScheduleItem)
        .filter(models.ScheduleItem.id == course_id, models.ScheduleItem.user_id == user_id)
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def delete_all_schedule(db: Session, user_id: int) -> int:
    count = db.query(models.ScheduleItem).filter(models.ScheduleItem.user_id == user_id).delete()
    db.commit()
    return count


# ---------------------------------------------------------------------------
# reminders
# ---------------------------------------------------------------------------

def create_reminder(
    db: Session,
    user_id: int,
    title: str,
    remind_at_text: str,
    notes: str | None,
    remind_at: datetime | None = None,
) -> models.Reminder:
    item = models.Reminder(user_id=user_id, title=title, remind_at_text=remind_at_text, notes=notes, remind_at=remind_at)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_reminders(db: Session, user_id: int, include_done: bool = False) -> list[models.Reminder]:
    q = db.query(models.Reminder).filter(models.Reminder.user_id == user_id)
    if not include_done:
        q = q.filter(models.Reminder.is_done.is_(False))
    return q.order_by(models.Reminder.id.desc()).all()


def list_due_reminders(db: Session, user_id: int) -> list[models.Reminder]:
    now = datetime.now()
    candidates = (
        db.query(models.Reminder)
        .filter(
            models.Reminder.user_id == user_id,
            models.Reminder.is_done.is_(False),
            models.Reminder.remind_at.isnot(None),
        )
        .all()
    )
    return [r for r in candidates if r.remind_at <= now]


def mark_reminder_done(db: Session, reminder_id: int, user_id: int) -> models.Reminder | None:
    item = (
        db.query(models.Reminder)
        .filter(models.Reminder.id == reminder_id, models.Reminder.user_id == user_id)
        .first()
    )
    if not item:
        return None
    item.is_done = True
    db.commit()
    db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# academic plan
# ---------------------------------------------------------------------------

def add_academic_plan_item(
    db: Session,
    user_id: int,
    course_code: str | None,
    course_name: str,
    credits: int | None,
    semester: str | None,
    status: str | None,
    notes: str | None,
) -> models.AcademicPlanItem:
    normalized_code = (course_code or '').strip() or None
    normalized_name = (course_name or '').strip()

    item: models.AcademicPlanItem | None = None
    if normalized_code:
        item = (
            db.query(models.AcademicPlanItem)
            .filter(
                models.AcademicPlanItem.user_id == user_id,
                models.AcademicPlanItem.course_code == normalized_code,
            )
            .first()
        )
    if not item and normalized_name:
        item = (
            db.query(models.AcademicPlanItem)
            .filter(
                models.AcademicPlanItem.user_id == user_id,
                models.AcademicPlanItem.course_name == normalized_name,
            )
            .first()
        )

    _PRIORITY: dict[str, int] = {'completed': 2, 'in_progress': 1, 'planned': 0}
    if item:
        item.course_code = normalized_code or item.course_code
        item.course_name = normalized_name or item.course_name
        item.credits = credits if credits is not None else item.credits
        item.semester = semester or item.semester
        new_s = (status or 'planned').strip().lower()
        old_s = (item.status or 'planned').strip().lower()
        item.status = new_s if _PRIORITY.get(new_s, 0) >= _PRIORITY.get(old_s, 0) else old_s
        item.notes = notes if notes is not None else item.notes
    else:
        item = models.AcademicPlanItem(
            user_id=user_id,
            course_code=normalized_code,
            course_name=normalized_name,
            credits=credits,
            semester=semester,
            status=(status or 'planned').strip(),
            notes=notes,
        )
        db.add(item)

    db.commit()
    db.refresh(item)
    return item


def clear_academic_plan(db: Session, user_id: int) -> int:
    deleted = db.query(models.AcademicPlanItem).filter(models.AcademicPlanItem.user_id == user_id).delete()
    db.commit()
    return int(deleted or 0)


def list_academic_plan_items(db: Session, user_id: int) -> list[models.AcademicPlanItem]:
    return (
        db.query(models.AcademicPlanItem)
        .filter(models.AcademicPlanItem.user_id == user_id)
        .order_by(models.AcademicPlanItem.semester, models.AcademicPlanItem.course_code)
        .all()
    )


def auto_close_requirement_groups(db: Session, user_id: int) -> int:
    """Auto-close only mandatory groups (اختياري X-X where required==pool).
    Elective pools (اختياري X-Y where X!=Y) are left alone so remaining planned
    courses continue to appear in the student's remaining course list."""
    import re
    items = list_academic_plan_items(db, user_id)
    group_pattern = re.compile(r'اختياري\s+(\d+)\s*[-–]\s*(\d+)')

    groups: dict[str, list[models.AcademicPlanItem]] = {}
    for item in items:
        if item.semester and group_pattern.search(item.semester):
            groups.setdefault(item.semester, []).append(item)

    closed = 0
    for semester, group_items in groups.items():
        match = group_pattern.search(semester)
        if not match:
            continue
        required_credits = int(match.group(1))
        available_credits = int(match.group(2))
        if required_credits != available_credits:
            continue
        completed_credits = sum(
            (item.credits or 0) for item in group_items if item.status == 'completed'
        )
        if completed_credits >= required_credits:
            for item in group_items:
                if item.status == 'planned':
                    item.status = 'completed'
                    closed += 1

    if closed:
        db.commit()
    return closed


def recommend_courses_from_plan(db: Session, user_id: int, limit: int = 3) -> list[models.AcademicPlanItem]:
    items = list_academic_plan_items(db, user_id)
    completed_codes = {i.course_code for i in items if i.course_code and i.status == 'completed'}
    planned = [i for i in items if i.status in {'planned', 'in_progress'} and i.course_code not in completed_codes]
    return planned[:max(limit, 1)]


# ---------------------------------------------------------------------------
# university rules
# ---------------------------------------------------------------------------

def _escape_like(value: str) -> str:
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def search_university_rules(db: Session, query: str) -> list[models.UniversityRule]:
    q = (query or '').strip()
    if not q:
        return []
    like = f'%{_escape_like(q)}%'
    return (
        db.query(models.UniversityRule)
        .filter(
            or_(
                models.UniversityRule.title.ilike(like),
                models.UniversityRule.body.ilike(like),
                models.UniversityRule.category.ilike(like),
            )
        )
        .order_by(models.UniversityRule.id.desc())
        .limit(10)
        .all()
    )


# ---------------------------------------------------------------------------
# assignments
# ---------------------------------------------------------------------------

def list_assignments(db: Session, user_id: int) -> list[models.Assignment]:
    return (
        db.query(models.Assignment)
        .filter(models.Assignment.user_id == user_id)
        .order_by(models.Assignment.id.desc())
        .all()
    )
