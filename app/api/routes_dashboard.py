import re as _re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

_GROUP_PATTERN = _re.compile(r'اختياري\s+(\d+)\s*[-–]\s*(\d+)')

from app.core.security import get_current_user
from app.db import crud, models
from app.db.session import get_db
from app.services.schedule_parser import find_room_image

router = APIRouter(prefix='/dashboard', tags=['dashboard'])

DAY_NAMES_AR = {
    1: 'الأحد',
    2: 'الاثنين',
    3: 'الثلاثاء',
    4: 'الأربعاء',
    5: 'الخميس',
    6: 'الجمعة',
    7: 'السبت',
}

STUDY_WEEK_DAYS = [1, 2, 3, 4, 5]


def _serialize_schedule(items: list[models.ScheduleItem]) -> list[dict]:
    ordered = sorted(items, key=lambda item: ((item.start_time.strftime('%H:%M') if item.start_time else '99:99'), item.course_name or ''))
    return [
        {
            'course_id': item.id,
            'course_code': item.course_code,
            'course_name': item.course_name,
            'day_of_week': item.day_of_week,
            'day_name_ar': DAY_NAMES_AR.get(item.day_of_week, str(item.day_of_week)),
            'start_time': item.start_time.strftime('%H:%M') if item.start_time else None,
            'end_time': item.end_time.strftime('%H:%M') if item.end_time else None,
            'room_text': item.room_text,
            'credits': item.credits,
            'instructor': item.instructor,
            'image_url': find_room_image(item.room_text),
        }
        for item in ordered
    ]


@router.get('/reminders/due')
def due_reminders(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    items = crud.list_due_reminders(db, user.id)
    return {
        'reminders': [
            {
                'reminder_id': r.id,
                'title': r.title,
                'remind_at_text': r.remind_at_text,
                'remind_at': r.remind_at.isoformat() if r.remind_at else None,
                'notes': r.notes,
            }
            for r in items
        ]
    }


@router.post('/reminders/{reminder_id}/done')
def mark_done(reminder_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    reminder = crud.mark_reminder_done(db, reminder_id=reminder_id, user_id=user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail='Reminder not found')
    return {'ok': True}


@router.get('/summary')
def summary(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    all_items = crud.get_all_schedule(db, user.id)
    reminders = crud.list_reminders(db, user.id, include_done=False)
    plan_items = crud.list_academic_plan_items(db, user.id)

    completed  = [x for x in plan_items if (x.status or '').strip().lower() == 'completed']
    in_progress = [x for x in plan_items if (x.status or '').strip().lower() == 'in_progress']
    remaining  = [x for x in plan_items if (x.status or '').strip().lower() not in ('completed', 'in_progress')]

    week_days = []
    week_classes_count = 0
    online_items = [item for item in all_items if item.day_of_week is None]
    for day_num in STUDY_WEEK_DAYS:
        day_items = [item for item in all_items if item.day_of_week == day_num]
        week_classes_count += len(day_items)
        week_days.append(
            {
                'day_of_week': day_num,
                'day_name_ar': DAY_NAMES_AR.get(day_num, str(day_num)),
                'items': _serialize_schedule(day_items),
            }
        )

    return {
        'student': {
            'name': user.name,
            'email': user.email,
            'college': user.college,
            'major': user.major,
            'track': user.track,
        },
        'counts': {
            'week_classes': week_classes_count,
            'all_classes': len(all_items),
            'active_reminders': len(reminders),
            'plan_items': len(plan_items),
            'completed_courses': len(completed),
            'active_courses': len(in_progress),
            'remaining_courses': len(remaining),
        },
        'week_schedule': {
            'days': week_days,
            'online_items': _serialize_schedule(online_items),
        },
        'recent_reminders': [
            {
                'reminder_id': r.id,
                'title': r.title,
                'remind_at_text': r.remind_at_text,
                'notes': r.notes,
                'is_done': bool(r.is_done),
            }
            for r in reminders[:6]
        ],
        'academic_plan_active': [
            {
                'item_id': x.id,
                'course_code': x.course_code,
                'course_name': x.course_name,
                'credits': x.credits,
                'semester': x.semester,
                'status': x.status,
            }
            for x in in_progress[:6]
        ],
        'academic_plan_remaining': [
            {
                'item_id': x.id,
                'course_code': x.course_code,
                'course_name': x.course_name,
                'credits': x.credits,
                'semester': x.semester,
                'status': x.status,
            }
            for x in remaining
        ],
        'requirement_groups': _build_requirement_groups(plan_items),
    }


def _build_requirement_groups(plan_items: list) -> list[dict]:
    groups: dict[str, list] = {}
    for item in plan_items:
        if item.semester and _GROUP_PATTERN.search(item.semester):
            groups.setdefault(item.semester, []).append(item)

    result = []
    for label, items in groups.items():
        m = _GROUP_PATTERN.search(label)
        required = int(m.group(1)) if m else 0
        available = int(m.group(2)) if m else 0
        completed_credits = sum((x.credits or 0) for x in items if (x.status or '') == 'completed')
        in_progress_credits = sum((x.credits or 0) for x in items if (x.status or '') == 'in_progress')
        result.append({
            'label': label,
            'required_credits': required,
            'available_credits': available,
            'completed_credits': completed_credits,
            'in_progress_credits': in_progress_credits,
            'satisfied': completed_credits >= required,
            'courses': [
                {
                    'item_id': x.id,
                    'course_code': x.course_code,
                    'course_name': x.course_name,
                    'credits': x.credits,
                    'status': x.status,
                }
                for x in items
            ],
        })
    return result
