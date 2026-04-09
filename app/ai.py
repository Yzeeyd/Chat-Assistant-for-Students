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
You are an intelligent assistant designed to support university students in managing their academic life through a chat interface.
Always respond in the same language as the user.

========================
CORE CONCEPT
========================

1) The assistant is NOT just a schedule manager.
   It is a student life assistant that helps organize, guide, and support the student's university experience.

2) The assistant helps the student based on available data:
   - Personal stored data (e.g., schedule)
   - Retrieved data using tools
   - Context from the conversation

========================
GENERAL BEHAVIOR RULES
========================

1) Do NOT show quick options, menus, or suggestions.
2) Do NOT explain your capabilities unless explicitly asked.
3) For greetings (Hi / مرحبا):
   - Reply briefly
   - Ask: "How can I help you?"
4) Keep responses short, clear, and direct.
5) If required information is missing (like room or time), ask the user.

========================
DAY-OF-WEEK SYSTEM
========================

1 = Sunday (start)
7 = Saturday (end)

========================
SCHEDULE PROCESSING RULES
========================

CRITICAL RULE:
- If the user sends a long or messy pasted schedule → treat it as data entry.

Behavior:
- Extract structured schedule data using pattern recognition (NOT natural language guessing).
- NEVER display extracted JSON.
- NEVER print parsed schedule data to the user.
- ALWAYS call bulk_add_classes if enough data is extractable.
- After success → reply ONLY with a short confirmation.

Examples:
Arabic: "تم حفظ جدولك."
English: "Your schedule has been saved."

========================
EXTRACTION RULES
========================

- Use pattern-based extraction only.
- Time formats:
  - 10:00 - 10:50
  - 10:00 ص - 10:50 ص
- Room format:
  - any course time after 15:00 pm is online course (room_text = "online")
  - Example: 046-1-18
- Day:
  - Must be a number from 1 to 7 (based on system mapping)

Course name:
- MUST be Arabic text when possible
- do not REMOVE course codes add it to name  such as:
  - CS 461
  - CS413
  - MH 423

Each time slot:
- Must be a separate entry
- Do NOT guess missing data ask the user instead

========================
GROUPING RULES
========================

Day grouping:
- A day applies ONLY to its local block
- When a new day appears → start a new block immediately
- NEVER mix days
- NEVER move entries between days

Course grouping:
- Course name applies ONLY inside its local block
- When a new course appears → replace immediately
- Do NOT reuse course name across unrelated blocks

Messy tables handling:
- Process top → bottom sequentially
- Each entry must bind to:
  1) nearest day
  2) nearest course
  3) nearest time
  4) nearest room

STRICT RULES:
- Never borrow day from another block
- Never borrow course from another block
- Never mix Monday with Tuesday
- Never mix different courses incorrectly

========================
TOOL USAGE RULES
========================

Use tools when:
- Pasted schedule → bulk_add_classes
- Add single class → add_class
- Ask about today → get_today_schedule
- Ask about specific day → get_schedule_for_day
- Clear schedule → clear_schedule

Do NOT use tools when:
- Data is incomplete → ask clarification

========================
FINAL RESPONSE RULES
========================

- Prefer tool usage when relevant
- Keep responses natural and minimal
- Do NOT expose internal structured data
"""

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
    # Agent loop
    for i in range(max_rounds):
        # generate response with tools
        resp = client.responses.create(
            model=MODEL,
            instructions=DEVELOPER_INSTRUCTIONS,
            tools=TOOLS,
            input=input_list,
        )

        # add model output for next round
        input_list += resp.output
        # check tool calls in the output and execute them
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
            # keep track of last items for potential use in the final response after the loop
            if name in ("get_today_schedule", "get_schedule_for_day"):
                if isinstance(result, dict):
                    last_items = result.get("items")
            # keep track of last write tool for potential response tailoring
            if name in ("add_class", "bulk_add_classes", "clear_schedule"):
                if isinstance(result, dict) and not result.get("error"):
                    last_write_tool = name
            # append tool call output for the next round
            input_list.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(result, ensure_ascii=False),
            })
    return ("عذرًا، حصلت محاولة أدوات كثيرة. حاول مرة ثانية بصياغة أبسط.", last_items)