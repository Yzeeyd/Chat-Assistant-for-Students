
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db import crud, models
from app.utils.schedule import find_room_image, normalize_room_text, today_dow_1_to_7


def _nullable_string(description: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {'type': ['string', 'null']}
    if description:
        item['description'] = description
    return item


def _nullable_integer() -> dict[str, Any]:
    return {'type': ['integer', 'null']}


TOOL_DEFINITIONS = [
    {
        'type': 'function',
        'name': 'add_class',
        'description': 'Add one class session to the student schedule.',
        'parameters': {
            'type': 'object',
            'properties': {
                'course_code': _nullable_string('Course code such as CS461 or MH 423.'),
                'course_name': {'type': 'string'},
                'day_of_week': {'type': 'integer', 'minimum': 1, 'maximum': 7},
                'start_time': {'type': 'string', 'description': 'HH:MM 24-hour'},
                'end_time': {'type': 'string', 'description': 'HH:MM 24-hour'},
                'room_text': {'type': 'string'},
                'credits': _nullable_integer(),
                'instructor': _nullable_string(),
            },
            'required': ['course_code', 'course_name', 'day_of_week', 'start_time', 'end_time', 'room_text', 'credits', 'instructor'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'bulk_add_classes',
        'description': 'Add multiple schedule items from pasted Arabic or English schedule text.',
        'parameters': {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'course_code': _nullable_string(),
                            'course_name': {'type': 'string'},
                            'day_of_week': {'type': 'integer', 'minimum': 1, 'maximum': 7},
                            'start_time': {'type': 'string'},
                            'end_time': {'type': 'string'},
                            'room_text': {'type': 'string'},
                            'credits': _nullable_integer(),
                            'instructor': _nullable_string(),
                        },
                        'required': ['course_code', 'course_name', 'day_of_week', 'start_time', 'end_time', 'room_text', 'credits', 'instructor'],
                        'additionalProperties': False,
                    },
                }
            },
            'required': ['items'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'get_today_schedule',
        'description': 'Get today schedule for the current user.',
        'parameters': {'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False},
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'get_schedule_for_day',
        'description': 'Get schedule for a specific day. 1=Sunday and 7=Saturday.',
        'parameters': {
            'type': 'object',
            'properties': {'day_of_week': {'type': 'integer', 'minimum': 1, 'maximum': 7}},
            'required': ['day_of_week'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'get_all_schedule',
        'description': 'Get the whole stored schedule for the current user.',
        'parameters': {'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False},
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'update_class',
        'description': 'Update one schedule item using its course_id.',
        'parameters': {
            'type': 'object',
            'properties': {
                'course_id': {'type': 'integer'},
                'course_code': _nullable_string(),
                'course_name': _nullable_string(),
                'day_of_week': {'type': ['integer', 'null'], 'minimum': 1, 'maximum': 7},
                'start_time': _nullable_string('HH:MM 24-hour'),
                'end_time': _nullable_string('HH:MM 24-hour'),
                'room_text': _nullable_string(),
                'instructor': _nullable_string(),
                'credits': _nullable_integer(),
            },
            'required': ['course_id', 'course_code', 'course_name', 'day_of_week', 'start_time', 'end_time', 'room_text', 'instructor', 'credits'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'delete_class',
        'description': 'Delete one schedule item by its course_id.',
        'parameters': {
            'type': 'object',
            'properties': {'course_id': {'type': 'integer'}},
            'required': ['course_id'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'clear_schedule',
        'description': 'Delete all schedule items for the current user.',
        'parameters': {'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False},
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'create_reminder',
        'description': 'Create a reminder for a student task, deadline, or event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'remind_at_text': {'type': 'string', 'description': 'Natural reminder time such as tomorrow 8am or 2026-04-14 09:00.'},
                'notes': _nullable_string(),
            },
            'required': ['title', 'remind_at_text', 'notes'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'list_reminders',
        'description': 'List active reminders for the current user.',
        'parameters': {
            'type': 'object',
            'properties': {'include_done': {'type': ['boolean', 'null']}},
            'required': ['include_done'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'mark_reminder_done',
        'description': 'Mark one reminder as completed.',
        'parameters': {
            'type': 'object',
            'properties': {'reminder_id': {'type': 'integer'}},
            'required': ['reminder_id'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'add_academic_plan_item',
        'description': 'Add one course to the academic plan tracker.',
        'parameters': {
            'type': 'object',
            'properties': {
                'course_code': _nullable_string(),
                'course_name': {'type': 'string'},
                'credits': _nullable_integer(),
                'semester': _nullable_string(),
                'status': _nullable_string('planned, in_progress, or completed'),
                'notes': _nullable_string(),
            },
            'required': ['course_code', 'course_name', 'credits', 'semester', 'status', 'notes'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'get_academic_plan',
        'description': 'Get the current academic plan for the student.',
        'parameters': {'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False},
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'recommend_courses',
        'description': 'Recommend courses based on the saved academic plan and current schedule.',
        'parameters': {
            'type': 'object',
            'properties': {'limit': {'type': ['integer', 'null']}},
            'required': ['limit'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'search_university_rules',
        'description': 'Search university rules and regulations by keyword, topic, or category.',
        'parameters': {
            'type': 'object',
            'properties': {'query': {'type': 'string'}},
            'required': ['query'],
            'additionalProperties': False,
        },
        'strict': True,
    },
    {
        'type': 'function',
        'name': 'list_assignments',
        'description': 'List uploaded assignments for the current user.',
        'parameters': {'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False},
        'strict': True,
    },
]


def _time_or_none(value: str | None):
    return datetime.strptime(value, '%H:%M').time() if value else None


def _serialize_schedule_items(items: list[models.Schedule]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        out.append(
            {
                'course_id': item.id,
                'course_code': item.course_code,
                'course_name': item.course_name,
                'day_of_week': item.day_of_week,
                'start_time': item.start_time.strftime('%H:%M') if item.start_time else None,
                'end_time': item.end_time.strftime('%H:%M') if item.end_time else None,
                'room_text': item.room_text,
                'credits': item.credits,
                'instructor': item.instructor,
                'image_url': find_room_image(item.room_text),
            }
        )
    return out


#def _serialize_reminders(items: list[models.Reminder]) -> list[dict[str, Any]]:
    return [
        {
            'reminder_id': item.id,
            'title': item.title,
            'remind_at_text': item.remind_at_text,
            'notes': item.notes,
            'is_done': bool(item.is_done),
        }
        for item in items
    ]


#def _serialize_plan(items: list[models.AcademicPlanItem]) -> list[dict[str, Any]]:
    return [
        {
            'item_id': item.id,
            'course_code': item.course_code,
            'course_name': item.course_name,
            'credits': item.credits,
            'semester': item.semester,
            'status': item.status,
            'notes': item.notes,
        }
        for item in items
    ]


#def _serialize_assignments(items: list[models.Assignment]) -> list[dict[str, Any]]:
    return [
        {
            'assignment_id': item.id,
            'title': item.title,
            'course_name': item.course_name,
            'due_date_text': item.due_date_text,
            'file_name': item.file_name,
            'file_url': item.file_path,
            'notes': item.notes,
        }
        for item in items
    ]


#def _serialize_rules(items: list[models.UniversityRule]) -> list[dict[str, Any]]:
    return [
        {
            'rule_id': item.id,
            'title': item.title,
            'body': item.body,
            'source': item.source,
            'category': item.category,
        }
        for item in items
    ]


def execute_tool(name: str, args: dict[str, Any], db: Session, user: models.User) -> dict[str, Any]:
    if name == 'add_class':
        item = crud.add_schedule_item(
            db=db,
            user_id=user.id,
            course_code=str(args.get('course_code') or '').strip(),
            course_name=str(args['course_name']).strip(),
            day_of_week=int(args['day_of_week']),
            start_time=_time_or_none(args.get('start_time')),
            end_time=_time_or_none(args.get('end_time')),
            room_text=normalize_room_text(str(args['room_text'])),
            instructor=args.get('instructor'),
            credits=int(args.get('credits') or 0),
        )
        return {'ok': True, 'items': _serialize_schedule_items([item])}

    if name == 'bulk_add_classes':
        added_items = []
        skipped = []
        for index, raw_item in enumerate(args.get('items', []), start=1):
            try:
                result = execute_tool('add_class', raw_item, db, user)
                added_items.extend(result['items'])
            except Exception as exc:
                skipped.append({'index': index, 'error': str(exc)})
        return {'ok': True, 'added': len(added_items), 'items': added_items, 'skipped': skipped}

    if name == 'get_today_schedule':
        day_of_week = today_dow_1_to_7()
        items = crud.get_schedule_for_day(db, user.id, day_of_week)
        return {'ok': True, 'day_of_week': day_of_week, 'items': _serialize_schedule_items(items)}

    if name == 'get_schedule_for_day':
        items = crud.get_schedule_for_day(db, user.id, int(args['day_of_week']))
        return {'ok': True, 'items': _serialize_schedule_items(items)}

    if name == 'get_all_schedule':
        items = crud.get_all_schedule(db, user.id)
        return {'ok': True, 'items': _serialize_schedule_items(items)}

    if name == 'update_class':
        update_data = {
            'course_code': args.get('course_code'),
            'course_name': str(args['course_name']).strip() if args.get('course_name') else None,
            'day_of_week': int(args['day_of_week']) if args.get('day_of_week') is not None else None,
            'start_time': _time_or_none(args.get('start_time')),
            'end_time': _time_or_none(args.get('end_time')),
            'room_text': normalize_room_text(str(args['room_text'])) if args.get('room_text') else None,
            'instructor': args.get('instructor'),
            'credits': int(args['credits']) if args.get('credits') is not None else None,
        }
        item = crud.update_schedule_item(db, course_id=int(args['course_id']), user_id=user.id, **update_data)
        if not item:
            return {'ok': False, 'error': 'Class not found'}
        return {'ok': True, 'items': _serialize_schedule_items([item])}

    if name == 'delete_class':
        return {'ok': crud.delete_one_schedule_item(db, course_id=int(args['course_id']), user_id=user.id)}

    if name == 'clear_schedule':
        return {'ok': True, 'deleted': crud.delete_all_schedule(db, user.id)}

    #if name == 'create_reminder':
        reminder = crud.create_reminder(
            db,
            user_id=user.id,
            title=str(args['title']).strip(),
            remind_at_text=str(args['remind_at_text']).strip(),
            notes=args.get('notes'),
        )
        return {'ok': True, 'reminders': _serialize_reminders([reminder])}

    #if name == 'list_reminders':
        reminders = crud.list_reminders(db, user.id, include_done=bool(args.get('include_done')))
        return {'ok': True, 'reminders': _serialize_reminders(reminders)}

    #if name == 'mark_reminder_done':
        reminder = crud.mark_reminder_done(db, reminder_id=int(args['reminder_id']), user_id=user.id)
        if not reminder:
            return {'ok': False, 'error': 'Reminder not found'}
        return {'ok': True, 'reminders': _serialize_reminders([reminder])}

    #if name == 'add_academic_plan_item':
        item = crud.add_academic_plan_item(
            db,
            user_id=user.id,
            course_code=str(args.get('course_code') or '').strip(),
            course_name=str(args['course_name']).strip(),
            credits=int(args.get('credits') or 0),
            semester=args.get('semester'),
            status=str(args.get('status') or 'planned').strip(),
            notes=args.get('notes'),
        )
        return {'ok': True, 'academic_plan': _serialize_plan([item])}

    #if name == 'get_academic_plan':
        items = crud.list_academic_plan_items(db, user.id)
        return {'ok': True, 'academic_plan': _serialize_plan(items)}

    #if name == 'recommend_courses':
        items = crud.recommend_courses_from_plan(db, user.id, limit=int(args.get('limit') or 3))
        return {'ok': True, 'academic_plan': _serialize_plan(items)}

    #if name == 'search_university_rules':
        items = crud.search_university_rules(db, str(args['query']))
        return {'ok': True, 'rules': _serialize_rules(items)}

    #if name == 'list_assignments':
        items = crud.list_assignments(db, user.id)
        return {'ok': True, 'assignments': _serialize_assignments(items)}

    return {'ok': False, 'error': f'Unknown tool: {name}'}
