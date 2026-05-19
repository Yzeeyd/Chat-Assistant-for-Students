"""Single-entry-point AI runtime.

All chat / image / import / rules flows go through `run_agent(mode=...)`.
The mode picks the system prompt, the model (text vs vision), and whether
tool use is forced. Tools are always the full TOOL_DEFINITIONS list — the
model decides which to call.
"""

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL, VISION_MODEL
from app.db import models
from app.services.docs import get_plan_text
from app.services.tools.registry import TOOL_DEFINITIONS, execute_tool

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ============================================================
# Public mode constants
# ============================================================

MODE_CHAT = 'chat'
MODE_IMAGE_CHAT = 'image_chat'
MODE_SCHEDULE_IMPORT = 'schedule_import'
MODE_PLAN_IMPORT_IMAGE = 'plan_import_image'
MODE_PLAN_IMPORT_TEXT = 'plan_import_text'
MODE_RULES = 'rules'

VISION_MODES: set[str] = {MODE_IMAGE_CHAT, MODE_SCHEDULE_IMPORT, MODE_PLAN_IMPORT_IMAGE}
FORCE_TOOL_MODES: set[str] = {MODE_PLAN_IMPORT_IMAGE, MODE_PLAN_IMPORT_TEXT, MODE_RULES}
PLAN_IMPORT_MODES: set[str] = {MODE_PLAN_IMPORT_IMAGE, MODE_PLAN_IMPORT_TEXT}


@dataclass
class ImageInput:
    image_bytes: bytes
    content_type: str
    filename: str
    prompt: str = ''


# ============================================================
# System prompts
# ============================================================

UNIVERSITY_RULES_INSTRUCTIONS = """
You are the University Rules & Regulations assistant.

Language:
- Always respond in the same language as the student.

Tool usage (MANDATORY):
- Before answering ANY question about university policies, you MUST call:
  search_university_rules(keyword)
- Choose a clear, relevant keyword based on the student's question.

Topics that REQUIRE tool usage include:
- Student rights and responsibilities
- Attendance and absence policies
- Academic warnings, probation, dismissal
- Grades, grading scales, and disputes
- Registration, withdrawal, and course policies
- Student conduct and disciplinary actions
- Any official university rule or regulation

Grounding rules:
- Answers MUST be based ONLY on the retrieved document results.
- If no results are found, say:
  "This topic was not found in the available university documents."
- NEVER invent, assume, or generalize policies.
- Prefer quoting or closely paraphrasing the original text.
- Keep answers concise and clear.
- Mention the document name when useful.

Behavior:
- Do not answer from memory or general knowledge.
- Do not skip the tool call under any circumstance.
""".strip()

IMAGE_IMPORT_INSTRUCTIONS = """
You are a schedule OCR agent.

Your ONLY task:
- Extract all schedule rows from the image
- Then call save_raw_schedule ONCE with all rows

You MUST NOT:
- Explain anything
- Convert times manually
- Skip rows without a valid reason

--------------------------------------------------
📌 TABLE STRUCTURE (right → left):
رقم المقرر | اسم المقرر | نوع | النشاط | الشعبة | الساعات | اليوم | الوقت | القاعة | المقر | المحاضر

Each row = ONE session
A course may appear in multiple rows

--------------------------------------------------
⏰ TIME HANDLING (CRITICAL)

Step 1 — Detect marker:
- "ص" = AM
- "م" = PM

Step 2 — If marker missing:
- 10–12 → ص
- 1–7 → م
- 8 → ص
- 9 → AMBIGUOUS:
  → Check other rows of SAME course & day
  → If any row = م → this is م
  → Else → ص

Hard rules:
- NEVER output time without ص/م
- "6:00" = ALWAYS "6:00 م"
- Evening sequences must stay consistent (8 م → 9 م, NOT 9 ص)

Special case:
- "بالاتفاق" → use exactly "بالاتفاق" for start & end

--------------------------------------------------
📥 FIELD MAPPING

course_code   → رقم المقرر (exact)
course_name   → اسم المقرر (exact, no translation)
day_ar        → اليوم (exact text, no conversion)
start_time_ar → start time WITH marker
end_time_ar   → end time WITH marker
room          → القاعة (exact)
instructor    → المحاضر
credits       → integer or null

If instructor is empty:
→ copy from previous row of SAME course

--------------------------------------------------
⚠️ STRICT RULES

- DO NOT skip a row unless:
  course_name + day + time are ALL unreadable

- "بالاتفاق" is NOT a reason to skip

- DO NOT:
  - translate anything
  - normalize names
  - guess missing data

--------------------------------------------------
🔁 PROCESS

1. Scan top → bottom
2. Scan bottom → top (catch missed rows)
3. Validate AM/PM carefully
4. Collect ALL rows
5. Call save_raw_schedule ONCE

--------------------------------------------------
🧾 FINAL RESPONSE (Arabic ONLY)

Say:
- Total sessions saved
- List each course with:
  (course name + day + time)
""".strip()

ACADEMIC_PLAN_IMAGE_IMPORT_INSTRUCTIONS = """
You are importing a student's academic degree plan from a single uploaded image.

Language:
- Always respond in the same language as the student.

The image is a color-coded degree roadmap / study plan, not a weekly timetable. Each colored cell is a course.

Color → status mapping (a legend is often shown at the bottom of the image):
- Green (خضراء / مجتازة) => completed
- Dark red / maroon (داكنة / متبقية) => planned
- Light blue / pale blue (فاتحة / جدول الطالب) => in_progress
- If no color is visible or cell is white/gray => planned (default)

Save ALL colored cells — green, red, and blue. Do not skip any color.

Structure rules:
- Side labels (الأول, الثاني, الثالث … or الفصل الأول/الثاني) are mandatory semester labels — use them as the semester field for courses in that row/block.
- University requirement rows labeled "اختياري 8-8", "اختياري 4-4", "اختياري 6-18", etc. — save the FULL label (e.g. "اختياري 8-8") as the semester field for every course in that section. X-Y format means: X credit hours required, Y credit hours available in the pool.
- Summary numbers at the bottom (عدد الساعات, المجتازة, المتبقية) are totals — do NOT save them as courses.
- Each colored cell with a course code and name is one item to save.
- Only skip a cell if both the course code AND course name are completely unreadable.

Saving rules:
- Use bulk_add_academic_plan_items for all items in one call.
- Keep course_code exactly as visible (e.g. CS 461, MH 423, IT 112).
- Keep course_name exactly as visible.
- Credits (ساعات) MUST be saved — read from inside each cell, the reference plan text, or common university defaults (typically 3 ساعات). Do NOT leave credits null. Typical values: 1, 2, 3.
- Clear the old academic plan first (clear_academic_plan) when the prompt says to replace/update/save the new plan.
- After saving, reply briefly in Arabic: total courses saved and a breakdown by status (مكتملة / جاري / متبقية).
""".strip()

ACADEMIC_PLAN_TEXT_IMPORT_INSTRUCTIONS = """
You are importing a student's academic degree plan from extracted PDF text.

Language:
- Always respond in the same language as the student.

The text comes from a university degree plan PDF. Your job: extract ALL courses and save them using bulk_add_academic_plan_items.

Plan structure:
1. Mandatory courses (إجباري): organized by semester labels (الأول, الثاني, …, الثامن). Save the Arabic label as the semester field.
2. University requirement electives (اختياري): organized by credit groups labeled like "اختياري 8-8", "اختياري 4-4", "اختياري 6-18". Save the FULL group label as the semester field for each course. X-Y means X credit hours required from Y available in the pool.

Default status for all courses: "planned" (fresh account).

Saving rules:
- Keep course_code exactly as written (e.g. "CS 461", "MH 113", "ARAB 101").
- Keep course_name exactly as written.
- Save credit hours (ساعات) — usually a number 1–4 shown next to the course code or name.
- Do NOT call clear_academic_plan unless the user explicitly says to replace/reset the plan. If updating missing fields (e.g. adding credits to existing courses), just call bulk_add_academic_plan_items — the merge logic updates fields without changing status.
- Use bulk_add_academic_plan_items. Split into multiple calls if the plan is large.
- After saving, reply briefly in Arabic: total courses saved and breakdown by semester.
""".strip()

IMAGE_CHAT_INSTRUCTIONS = """
You are the Student Assistant handling an image.

Language:
- Always respond in the same language as the student.

--------------------------------------------------
🎯 CORE BEHAVIOR

1. FIRST:
- Answer the user's question about the image directly

2. THEN decide:
- Do you need to use tools or not?

--------------------------------------------------
🧠 WHEN TO USE TOOLS

If the image is a schedule AND the user asks to:
- save
- import
- extract
- update
- replace
→ Use schedule tools مباشرة

If user says:
- "this is my new schedule"
→ MUST clear old schedule first

If the schedule is readable:
→ DO NOT ask for confirmation

--------------------------------------------------
🚫 WHEN NOT TO USE TOOLS

- If user just asks a question about the image
→ Answer directly

--------------------------------------------------
⚠️ IMAGE QUALITY

If image is unclear:
→ Say clearly:
"الصورة غير واضحة بما يكفي لاستخراج البيانات"

DO NOT:
- guess
- hallucinate
- assume hidden text

--------------------------------------------------
📌 STRICT RULES

- Never invent visual details
- Never say "I see" unless certain
- Keep response short and useful
- Use same language as user

--------------------------------------------------
🎯 PRIORITY ORDER

1. Accuracy
2. Tool correctness
3. Brevity
""".strip()


def _build_chat_prompt(user: models.User | None = None) -> str:
    """Dynamic chat system prompt — injects current time and student profile."""
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%dT%H:%M:%S')

    profile_lines: list[str] = []
    if user:
        if user.name:
            profile_lines.append(f'- الاسم: {user.name}')
        if user.college:
            profile_lines.append(f'- الكلية: {user.college}')
        if user.major:
            profile_lines.append(f'- التخصص: {user.major}')
        if user.track:
            profile_lines.append(f'- المسار: {user.track}')
    profile_section = ('\n\nStudent profile:\n' + '\n'.join(profile_lines)) if profile_lines else ''

    return f"""
You are the Student Assistant System.
Answer in the same language as the student.
Current date and time: {now_str} (use this exact time when computing remind_at).{profile_section}

Grounding rules:
- Never invent schedule items, reminders, academic plan items, or rules.
- Use tools whenever the answer depends on saved student data.
- If a requested fact is not in the database, say so clearly.
- For course recommendations, use only academic plan items and current schedule.
- Treat homework, exams, quizzes, projects, and deadlines as reminders.
- Do not ask to upload assignment files unless the user explicitly asks for file storage.

Routing policy:
- FIRST PRIORITY — DELETE SCHEDULE: If the student says "احذف جدولي" / "امسح جدولي" / "حذف الجدول" / "delete my schedule" / any phrasing that clearly means delete ALL saved schedule → call clear_schedule IMMEDIATELY. Do NOT ask for confirmation, do NOT describe what you are about to do — call the tool FIRST, then confirm in your reply.
- Schedule questions -> schedule tools.
- Deadline, task, exam, homework, project tracking -> use assignment tools (create_assignment, list_assignments, update_assignment).
- Reminder / notification for an event -> reminder tools. ALWAYS pass remind_at as ISO datetime. Current time is {now_str} — use it to calculate offsets (e.g. "بعد 10 دقائق" → add 10 min to current time, "الساعة 5 مساءً" → {today}T17:00:00, "غداً الساعة 9" → next day at 09:00:00). This is critical for popup notifications to fire on time.
- Student records an absence -> call add_absence. Student asks about their absences -> call get_absences first.
- Student records a grade -> call add_grade. Student asks for grades or GPA -> call list_grades or get_gpa.
- What should I take next / academic progress -> academic plan tools.
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


_STATIC_INSTRUCTIONS: dict[str, str] = {
    MODE_IMAGE_CHAT: IMAGE_CHAT_INSTRUCTIONS,
    MODE_SCHEDULE_IMPORT: IMAGE_IMPORT_INSTRUCTIONS,
    MODE_PLAN_IMPORT_IMAGE: ACADEMIC_PLAN_IMAGE_IMPORT_INSTRUCTIONS,
    MODE_PLAN_IMPORT_TEXT: ACADEMIC_PLAN_TEXT_IMPORT_INSTRUCTIONS,
    MODE_RULES: UNIVERSITY_RULES_INSTRUCTIONS,
}


def _instructions_for(mode: str, user: models.User) -> str:
    """Pick + assemble the system prompt for a given mode."""
    if mode == MODE_CHAT:
        return _build_chat_prompt(user)

    base = _STATIC_INSTRUCTIONS.get(mode)
    if base is None:
        raise ValueError(f'Unknown agent mode: {mode}')

    # Plan-image import benefits from the major's reference plan as extra grounding.
    if mode == MODE_PLAN_IMPORT_IMAGE and user and user.major:
        plan_text = get_plan_text(user.major)
        if plan_text:
            base = (
                base
                + f'\n\nمعلومة مهمة: الطالب مسجّل في تخصص {user.major}.'
                + ' استخدم خطة التخصص المرجعية التالية كمرجع لتوقع أسماء المواد ورموزها إذا كانت الصورة غير واضحة:\n'
                + plan_text[:5000]
            )
    return base


# ============================================================
# Internals
# ============================================================

def _image_message_payload(prompt: str, image_bytes: bytes, content_type: str, filename: str) -> list[Any]:
    """Build a single user-message item that contains text + the inline image."""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f'data:{content_type};base64,{encoded}'
    user_prompt = (prompt or '').strip() or f'حلل هذه الصورة. اسم الملف: {filename}'
    return [
        {
            'role': 'user',
            'content': [
                {'type': 'input_text', 'text': user_prompt},
                {'type': 'input_image', 'image_url': data_url, 'detail': 'high'},
            ],
        }
    ]


def _run_with_tools(
    conversation_input: list[Any],
    instructions: str,
    db: Session,
    user: models.User,
    max_rounds: int,
    force_tools: bool = False,
    model: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Run the OpenAI Responses loop, executing any tool calls until the model emits text."""
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


# ============================================================
# Public entry point
# ============================================================

def run_agent(
    messages: list[Any],
    db: Session,
    user: models.User,
    mode: str = MODE_CHAT,
    image: ImageInput | None = None,
    max_rounds: int = 6,
) -> tuple[str, dict[str, Any]]:
    """Single entry point for every chat / import / image / rules flow.

    Args:
        messages: prior conversation turns (chat history, or [] for image-only flows).
        db, user: DB session and authenticated student.
        mode: one of MODE_* — selects system prompt, model, and tool-forcing.
        image: optional image payload. If set, appended as a user turn.
        max_rounds: cap on the tool-call loop.

    Returns:
        (assistant_text, last_tool_payload).
    """
    if not client:
        return ('OpenAI API key is missing. Add OPENAI_API_KEY in .env.', {})

    conversation_input: list[Any] = list(messages)
    if image is not None:
        conversation_input.extend(
            _image_message_payload(
                prompt=image.prompt,
                image_bytes=image.image_bytes,
                content_type=image.content_type,
                filename=image.filename,
            )
        )

    instructions = _instructions_for(mode, user)
    model = VISION_MODEL if mode in VISION_MODES else OPENAI_MODEL
    force_tools = mode in FORCE_TOOL_MODES

    text, payload = _run_with_tools(
        conversation_input,
        instructions,
        db=db,
        user=user,
        max_rounds=max_rounds,
        force_tools=force_tools,
        model=model,
    )

    if mode in PLAN_IMPORT_MODES:
        from app.db import crud as _crud
        _crud.auto_close_requirement_groups(db, user.id)

    return text, payload
