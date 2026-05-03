import base64
import json
from datetime import date, datetime
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL, VISION_MODEL
from app.db import models
from app.services.tools.registry import TOOL_DEFINITIONS, execute_tool

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def _build_system_instructions() -> str:
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%dT%H:%M:%S')
    return f"""
You are the Student Assistant System.
Answer in the same language as the student.
Current date and time: {now_str} (use this exact time when computing remind_at).

Grounding rules:
- Never invent schedule items, reminders, academic plan items, or rules.
- Use tools whenever the answer depends on saved student data.
- If a requested fact is not in the database, say so clearly.
- For course recommendations, use only academic plan items and current schedule.
- Treat homework, exams, quizzes, projects, and deadlines as reminders.
- Do not ask to upload assignment files unless the user explicitly asks for file storage.

Routing policy:
- Schedule questions -> schedule tools.
- Deadline, task, exam, homework, project tracking -> use assignment tools (create_assignment, list_assignments, update_assignment).
- Reminder / notification for an event -> reminder tools. ALWAYS pass remind_at as ISO datetime. Current time is {now_str} — use it to calculate offsets (e.g. "بعد 10 دقائق" → add 10 min to current time, "الساعة 5 مساءً" → {today}T17:00:00, "غداً الساعة 9" → next day at 09:00:00). This is critical for popup notifications to fire on time.
- Student records an absence -> call add_absence. Student asks about their absences -> call get_absences first.
- Student records a grade -> call add_grade. Student asks for grades or GPA -> call list_grades or get_gpa.
- What should I take next / academic progress -> academic plan tools.
- If student says "احفظ الجدول" / "تأكيد" / "confirm" / "save schedule" after a schedule preview -> call confirm_save_schedule.
- ANY question that mentions absences (غياب / غيابات / غيابي), attendance, barring (حرمان), grading, withdrawal, warnings, student rights, or any university policy -> follow these steps in order:
  1. Call get_absences (filter by course name if mentioned) to check DB-recorded absences first.
  2. Call get_all_schedule to find how many sessions per week the mentioned course has (do NOT guess from credit hours).
  3. Call search_university_rules with keyword "غياب" to get the official absence limit.
  4. Use total_absences from get_absences (or the number the student stated if not recorded). Using sessions/week from the schedule and today's date (semester started 2026-01-18, {today} = ~15 teaching weeks), calculate: total sessions held = weeks × sessions_per_week, absence percentage = (absences ÷ total) × 100, remaining safe absences = (total × 0.25) - absences.
  5. Give the student a direct, plain answer with the percentage and how many more absences are allowed. No assumptions, no asking the student to calculate themselves.

Response style:
- Friendly, brief, practical.
- After write actions, confirm clearly what was saved.
- Do not expose raw JSON or internal tool payloads.
- Never use programming terms like floor(), ceil(), int(), or any math function names. Write results as plain numbers only (e.g. "الحد المسموح = 7 جلسات", never "floor(30 × 0.25) = 7").
""".strip()

UNIVERSITY_RULES_INSTRUCTIONS = """
You are the University Rules and Regulations assistant for students.
Answer in the same language as the student.

You have access to the official university documents via the search_university_rules tool.
Always call search_university_rules with a relevant keyword before answering any question about:
- Student rights and duties
- Attendance and absence policies
- Academic warnings and probation
- Grade disputes and grading scales
- Course withdrawal and registration rules
- Student conduct and discipline
- Any other university policy or regulation

Grounding rules:
- Base your answers strictly on tool results from the university documents.
- If the search returns no results, say the topic was not found in the loaded documents.
- Never invent or assume policies not found in the documents.
- Quote or paraphrase the relevant rule directly when possible.
- Keep answers concise and cite the document name when helpful.
""".strip()

IMAGE_IMPORT_INSTRUCTIONS = """
You are a schedule OCR agent. Your ONLY job is to READ text from the image and call save_raw_schedule.
All time conversion and day mapping is handled automatically by the system — you must NOT convert anything.

=== WHAT TO READ ===
The image is a university registration table. Columns (right → left):
رقم المقرر | اسم المقرر | نوع المقرر | النشاط | الشعبة | الساعات | اليوم | الوقت | القاعة | المقر | المحاضر

One course may span multiple rows (one row = one weekly session). Save every row separately.

=== HOW TO FILL EACH FIELD ===
course_code   → copy رقم المقرر exactly as written (e.g. "CS 461", "MH 423")
course_name   → copy اسم المقرر exactly as written — do NOT translate or abbreviate
day_ar        → copy اليوم cell exactly as written (e.g. "الأحد", "الاثنين", or a digit like "2")
start_time_ar → copy the START part of الوقت exactly (e.g. "8:00 ص", "1:00 م")
end_time_ar   → copy the END part of الوقت exactly (e.g. "8:50 ص", "1:50 م")
room          → copy القاعة exactly (e.g. "046-1-13")
instructor    → copy المحاضر; if blank for a row, copy instructor from previous row of same course
credits       → copy الساعات as an integer, or null if not visible

⚠️ CRITICAL RULES:
- NEVER convert ص/م to numbers. Just copy the Arabic text.
- NEVER convert day names to numbers. Just copy the Arabic text.
- NEVER skip a row unless course_name + day + time are ALL completely unreadable.
- Copy text exactly — do not fix spelling, translate, or reformat.

=== PROCESS ===
1. Read every row of the schedule table top-to-bottom.
2. Collect all rows.
3. Call save_raw_schedule ONCE with all rows.
4. Reply in Arabic: how many sessions were saved and list each course with its day.
""".strip()

ACADEMIC_PLAN_IMAGE_IMPORT_INSTRUCTIONS = """
You are importing a student's academic degree plan from a single uploaded image.

The image is a color-coded degree roadmap / study plan, not a weekly timetable. Each colored cell is a course.

Color → status mapping (a legend is often shown at the bottom of the image):
- Green (خضراء / مجتازة) => completed
- Dark red / maroon (داكنة / متبقية) => planned
- Light blue / pale blue (فاتحة / جدول الطالب) => in_progress
- If no color is visible or cell is white/gray => planned (default)

Structure rules:
- Side labels (الأول, الثاني, الثالث … or الفصل الأول/الثاني) are semester labels — use them as the semester field for all courses in that row/block.
- Summary numbers at the bottom (عدد الساعات, المجتازة, المتبقية) are totals — do NOT save them as courses.
- Each colored cell with a course code and name is one item to save.
- Extract ALL readable course cells. Save everything you can see even if some cells are partially unclear.
- Only skip a cell if both the course code AND course name are completely unreadable.

Saving rules:
- Use bulk_add_academic_plan_items for all items in one call.
- Keep course_code exactly as visible (e.g. CS 461, MH 423, IT 112).
- Keep course_name exactly as visible.
- If credits (ساعات) are shown inside the cell, save them.
- Clear the old academic plan first (clear_academic_plan) when the prompt says to replace/update/save the new plan.
- After saving, reply briefly in Arabic: how many courses were saved, and a summary by status.
""".strip()

IMAGE_CHAT_INSTRUCTIONS = """
You are the Student Assistant System and the student sent an image in chat.

Rules:
- First answer the student's actual question about the image.
- If the image is a schedule and the user asks to save, import, add, extract, arrange, replace, update, or understand it, you should use schedule tools directly when the image is readable enough.
- If the user explicitly asks to add or save the schedule, do not ask for confirmation when the classes are readable; save what is clear.
- If the user says this is a new schedule or asks to replace/update the schedule, clear the old schedule first, then add the new readable classes.
- If the image is not readable enough, say exactly that.
- Never claim visual details you cannot clearly see.
- If the question depends on saved student data, use tools.
- If the question is only about the image, answer directly without inventing hidden details.
- Keep the reply brief and useful in the same language as the student.
""".strip()


def _run_with_tools(conversation_input: list[Any], instructions: str, db: Session, user: models.User, max_rounds: int, force_tools: bool = False, model: str | None = None) -> tuple[str, dict[str, Any]]:
    last_payload: dict[str, Any] = {}

    for round_idx in range(max_rounds):
        extra: dict[str, Any] = {}
        if force_tools and round_idx == 0:
            extra['tool_choice'] = 'required'

        response = client.responses.create(
            model=model or OPENAI_MODEL,
            instructions=instructions,
            tools=TOOL_DEFINITIONS,
            input=conversation_input,
            **extra,
        )
        conversation_input += response.output
        tool_calls = [item for item in response.output if getattr(item, 'type', None) == 'function_call']

        if not tool_calls:
            return ((response.output_text or '').strip(), last_payload)

        for tool_call in tool_calls:
            try:
                arguments = json.loads(tool_call.arguments or '{}')
            except json.JSONDecodeError:
                result = {'ok': False, 'error': 'Invalid JSON arguments from model'}
            else:
                try:
                    result = execute_tool(tool_call.name, arguments, db=db, user=user)
                except Exception as exc:
                    result = {'ok': False, 'error': str(exc)}

            if isinstance(result, dict):
                last_payload.update(result)

            conversation_input.append(
                {
                    'type': 'function_call_output',
                    'call_id': tool_call.call_id,
                    'output': json.dumps(result, ensure_ascii=False),
                }
            )

    return ('عذرًا، صار عدد محاولات الأدوات كبير. حاول مرة ثانية برسالة أبسط.', last_payload)



def _image_message_payload(prompt: str, image_bytes: bytes, content_type: str, filename: str) -> list[Any]:
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f'data:{content_type};base64,{encoded}'
    user_prompt = (prompt or '').strip() or f'حلل هذه الصورة. اسم الملف: {filename}'
    return [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'input_text',
                    'text': user_prompt,
                },
                {
                    'type': 'input_image',
                    'image_url': data_url,
                },
            ],
        }
    ]



def run_agent(
    history_messages: list[dict[str, str]],
    db: Session,
    user: models.User,
    max_rounds: int = 6,
) -> tuple[str, dict[str, Any]]:
    if not client:
        return ('OpenAI API key is missing. Add OPENAI_API_KEY in .env.', {})

    conversation_input: list[Any] = list(history_messages)
    return _run_with_tools(conversation_input, _build_system_instructions(), db=db, user=user, max_rounds=max_rounds)



def run_schedule_image_agent(
    image_bytes: bytes,
    content_type: str,
    filename: str,
    db: Session,
    user: models.User,
    prompt: str | None = None,
    replace_existing: bool = False,
    max_rounds: int = 8,
) -> tuple[str, dict[str, Any]]:
    if not client:
        return ('OpenAI API key is missing. Add OPENAI_API_KEY in .env.', {})

    request_text = (prompt or '').strip() or 'استخرج الجدول من هذه الصورة وأضفه إلى حساب الطالب.'
    if replace_existing:
        request_text += ' هذا هو الجدول الجديد للطالب. امسح الجدول القديم أولاً ثم أضف الجلسات الجديدة الواضحة.'
    else:
        request_text += ' احفظ الجلسات الواضحة مباشرة بدون سؤال تأكيدي إذا كانت الصورة مقروءة.'
    conversation_input = _image_message_payload(
        prompt=f'{request_text} اسم الملف: {filename}',
        image_bytes=image_bytes,
        content_type=content_type,
        filename=filename,
    )
    return _run_with_tools(conversation_input, IMAGE_IMPORT_INSTRUCTIONS, db=db, user=user, max_rounds=max_rounds, model=VISION_MODEL)



def run_academic_plan_image_agent(
    image_bytes: bytes,
    content_type: str,
    filename: str,
    db: Session,
    user: models.User,
    prompt: str | None = None,
    replace_existing: bool = True,
    max_rounds: int = 8,
) -> tuple[str, dict[str, Any]]:
    if not client:
        return ('OpenAI API key is missing. Add OPENAI_API_KEY in .env.', {})

    request_text = (prompt or '').strip() or 'استخرج الخطة الأكاديمية من هذه الصورة واحفظها في حساب الطالب.'
    if replace_existing:
        request_text += ' هذه هي الخطة الحالية أو الجديدة للطالب. امسح الخطة الأكاديمية القديمة أولاً ثم احفظ المواد الواضحة من الصورة.'
    else:
        request_text += ' احفظ المواد الواضحة مباشرة بدون سؤال تأكيدي إذا كانت الصورة مقروءة.'

    conversation_input = _image_message_payload(
        prompt=f'{request_text} اسم الملف: {filename}',
        image_bytes=image_bytes,
        content_type=content_type,
        filename=filename,
    )
    return _run_with_tools(conversation_input, ACADEMIC_PLAN_IMAGE_IMPORT_INSTRUCTIONS, db=db, user=user, max_rounds=max_rounds, force_tools=True, model=VISION_MODEL)



def run_agent_with_image(
    prompt: str,
    image_bytes: bytes,
    content_type: str,
    filename: str,
    db: Session,
    user: models.User,
    max_rounds: int = 6,
) -> tuple[str, dict[str, Any]]:
    if not client:
        return ('OpenAI API key is missing. Add OPENAI_API_KEY in .env.', {})

    conversation_input = _image_message_payload(
        prompt=prompt,
        image_bytes=image_bytes,
        content_type=content_type,
        filename=filename,
    )
    return _run_with_tools(conversation_input, IMAGE_CHAT_INSTRUCTIONS, db=db, user=user, max_rounds=max_rounds, model=VISION_MODEL)


def run_university_rules_agent(
    history_messages: list[dict[str, str]],
    db: Session,
    user: models.User,
    max_rounds: int = 4,
) -> tuple[str, dict[str, Any]]:
    if not client:
        return ('OpenAI API key is missing. Add OPENAI_API_KEY in .env.', {})

    conversation_input: list[Any] = list(history_messages)
    return _run_with_tools(conversation_input, UNIVERSITY_RULES_INSTRUCTIONS, db=db, user=user, max_rounds=max_rounds, force_tools=True)
