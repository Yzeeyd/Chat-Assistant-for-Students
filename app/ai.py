import os
import json
from openai import OpenAI
from sqlalchemy.orm import Session
from fastapi import Depends
from datetime import datetime

from .db import Base, engine, get_db
from . import models, schemas, crud
from .auth import hash_password, verify_password, create_access_token, get_current_user
from .utils import today_dow_1_to_7, normalize_room_text,find_room_image

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

DEVELOPER_INSTRUCTIONS = """
You are an intelligent assistant for university students to manage schedules via chat.
Always respond in the same language as the user.

Important behavior rules:
1) Do NOT show quick options, menus, or suggestions.
2) Do NOT explain your capabilities unless explicitly asked.
3) For greetings (Hi / مرحبا): reply briefly and ask "How can I help you?"
4) Keep responses short and direct.
5) If required information is missing (like room), ask the user.

Day-of-week mapping used in this system:
1 = Sunday
2 = Monday
3 = Tuesday
4 = Wednesday
5 = Thursday
6 = Friday
7 = Saturday

CRITICAL RULE FOR PASTED SCHEDULES:
- If the user sends a long or messy pasted schedule, treat it as schedule data entry.
- Extract the classes using patterns.
- DO NOT show the extracted JSON to the user.
- DO NOT print the parsed schedule in chat.
- You MUST call bulk_add_classes for pasted schedules whenever enough data can be extracted.
- After the tool call succeeds, reply only with a short confirmation in the user's language.
  Example Arabic: "تم حفظ جدولك."
  Example English: "Your schedule has been saved."

Extraction rules for pasted schedules:
- Use pattern extraction, not sentence meaning.
- Time looks like: 10:00 - 10:50 or 10:00 ص - 10:50 ص
- Room looks like: 046-1-18
- Day is a number from 1 to 7 using the mapping above
- Course name should be the Arabic course name only if possible
- Do not include course codes like CS 461 inside course_name unless no clean course name can be found
- Each time slot should become a separate item
- Do not merge different courses together
- Do not guess missing required values

COURSE NAME EXTRACTION RULES:
- Course names MUST be Arabic text only when possible
- REMOVE any course codes like:
  - CS 461
  - CS413
  - MH 423
- If a line contains both English code and Arabic text:
  - Ignore the English part
  - Keep only the Arabic course name
- NEVER include course codes in course_name unless the Arabic name cannot be isolated safely

DAY AND ENTRY GROUPING RULES:
- A day number applies only to the time slots that belong to that local block
- When a new day number appears, start a new day block immediately
- Do not move entries from one day to another
- Do not attach a class from Monday to Tuesday or vice versa
- Keep entries grouped by the exact detected day_of_week
- If there is any ambiguity, preserve the detected day number exactly as it appears nearest to the time entry

COURSE GROUPING RULES:
- A course name applies only within the same local day block until a new course name appears
- If a new Arabic course name appears, replace the current course immediately
- Do not keep using the previous course name across unrelated blocks
- Reuse the current course name only inside its local block

IMPORTANT FOR MIXED MESSY TABLES:
- Process the schedule sequentially from top to bottom
- For each extracted entry, bind:
  1) the nearest valid day number
  2) the nearest course name in the same local block
  3) the nearest time
  4) the nearest room
- Never borrow a day from the next block
- Never borrow a course from a previous unrelated block
- Never carry a Monday class into Tuesday
- Never carry a Tuesday class into Monday

When to use tools:
- User pasted a schedule -> use bulk_add_classes
- User wants to add one class manually -> use add_class
- User asks about today's schedule -> use get_today_schedule
- User asks about a specific day -> use get_schedule_for_day
- User wants to clear all schedule -> use clear_schedule

When NOT to use tools:
- If the data is incomplete and cannot be safely extracted, ask a short clarification question
- Never dump raw structured data to the user unless they explicitly asked to see raw JSON

Important:
- Prefer tool use over normal text whenever the request is about schedule storage or retrieval
- For successful tool execution, keep the final response short and natural
""".strip()

TOOLS = [
    {
        "type": "function",
        "name": "add_class",
        "description": "Add one class session to the student's schedule.",
        "parameters": {
            "type": "object",
            "properties": {
                "course_name": {"type": "string"},
                "day_of_week": {"type": "integer", "minimum": 1, "maximum": 7},
                "start_time": {"type": "string", "description": "HH:MM 24-hour"},
                "end_time": {"type": "string", "description": "HH:MM 24-hour"},
                "room_text": {"type": "string", "description": "e.g. 046-1-518"},
            },
            "required": ["course_name", "day_of_week", "start_time", "end_time", "room_text"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "bulk_add_classes",
        "description": "Add multiple class sessions at once for pasted schedules.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "course_name": {"type": "string"},
                            "day_of_week": {"type": "integer", "minimum": 1, "maximum": 7},
                            "start_time": {"type": "string", "description": "HH:MM 24-hour"},
                            "end_time": {"type": "string", "description": "HH:MM 24-hour"},
                            "room_text": {"type": "string"},
                        },
                        "required": ["course_name", "day_of_week", "start_time", "end_time", "room_text"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["items"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_today_schedule",
        "description": "Get today's schedule for the student, including room image URL if available.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_schedule_for_day",
        "description": "Get schedule for a specific weekday using 1=Sunday, 2=Monday, 3=Tuesday, 4=Wednesday, 5=Thursday, 6=Friday, 7=Saturday.",
        "parameters": {
            "type": "object",
            "properties": {
                "day_of_week": {"type": "integer", "minimum": 1, "maximum": 7}
            },
            "required": ["day_of_week"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "clear_schedule",
        "description": "Delete all schedule items for the student.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        "strict": True,
    },
]

def run_agent(history_messages: list[dict], max_rounds: int = 6, db: Session = None, user: models.User = None):
    if not os.getenv("OPENAI_API_KEY"):
        return ("OpenAI API key not set (OPENAI_API_KEY).", None)

    input_list = list(history_messages)
    last_items = None
    last_write_tool = None
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
    
    for i in range(max_rounds):
        resp = client.responses.create(
            model=MODEL,
            instructions=DEVELOPER_INSTRUCTIONS,
            tools=TOOLS,
            input=input_list,
        )

        # add model output for next round
        input_list += resp.output

        tool_calls = [x for x in resp.output if getattr(x, "type", None) == "function_call"]

        # no tool call -> normal assistant reply
        if not tool_calls:
            text = (resp.output_text or "").strip()
            return (text, last_items)
        # tool call -> function execution and next round
        for call in tool_calls:
            name = call.name
            args = json.loads(call.arguments or "{}")
            # function execution and error handling
            if name not in tool_handlers:
                result = {"error": f"Unknown tool: {name}"}
            else:
                try:
                    result = tool_handlers[name](**args) or {"ok": True}
                except Exception as e:
                    result = {"error": str(e)}
            #
            if name in ("get_today_schedule", "get_schedule_for_day"):
                if isinstance(result, dict):
                    last_items = result.get("items")

            if name in ("add_class", "bulk_add_classes", "clear_schedule"):
                if isinstance(result, dict) and not result.get("error"):
                    last_write_tool = name

            input_list.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(result, ensure_ascii=False),
            })
    return ("عذرًا، حصلت محاولة أدوات كثيرة. حاول مرة ثانية بصياغة أبسط.", last_items)