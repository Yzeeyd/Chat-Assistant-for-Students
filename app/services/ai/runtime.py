import base64
import json
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.db import models
from app.services.tools.registry import TOOL_DEFINITIONS, execute_tool

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_INSTRUCTIONS = """
You are the Student Assistant System.
Answer in the same language as the student.

Your main rule is grounding:
- Never invent schedule items, reminders, academic plan items, or rules.
- Use tools whenever the answer depends on saved student data.
- If a requested fact is not in the database, say so clearly.
- For course recommendations, use only academic plan items and current schedule.
- For university rules, use only the rules tool results.
- Treat homework, exams, quizzes, projects, and deadlines as reminders.
- Do not ask to upload assignment files unless the user explicitly asks for file storage.

Routing policy:
- Schedule questions -> schedule tools.
- Deadline, task, exam, homework reminders -> reminder tools.
- What should I take next / academic progress -> academic plan tools.
- Regulations, withdrawals, attendance, warnings -> university rules search.

Response style:
- Friendly, brief, practical.
- After write actions, confirm clearly what was saved.
- Do not expose raw JSON or internal tool payloads.
""".strip()

IMAGE_IMPORT_INSTRUCTIONS = """
You are importing a student weekly schedule from a single uploaded image.

Rules:
- Read the schedule carefully from the image.
- Extract only classes you can see clearly.
- Use bulk_add_classes when you can identify one or more classes.
- If one row is unclear, skip only that row instead of failing everything.
- Prefer Arabic day names mapped as: الأحد=1, الاثنين=2, الثلاثاء=3, الأربعاء=4, الخميس=5, الجمعة=6, السبت=7.
- Normalize times into HH:MM 24-hour format.
- Keep room text as visible in the image.
- If no readable schedule exists, explain that the image needs to be clearer.
- After using tools, answer briefly in Arabic and mention what was added.
""".strip()

ACADEMIC_PLAN_IMAGE_IMPORT_INSTRUCTIONS = """
You are importing a student's academic degree plan from a single uploaded image.

Rules:
- The image is usually a roadmap / study plan / plan map, not a weekly timetable.
- Extract only course cells you can read clearly.
- Use bulk_add_academic_plan_items when you can identify one or more courses.
- If the image represents the student's full plan, you may clear the old academic plan first when the prompt says to replace/update/save the new plan.
- The orange side labels such as الأول, الثاني, الثالث and optional blocks are semester/group labels, not courses. Use them as the semester field when clear.
- The totals at the bottom are summary numbers, not courses. Do not save them as courses.
- Interpret status from colors when clear:
  * green => completed
  * dark red / maroon => planned
  * light blue / pale blue / student schedule marker => in_progress
- Keep course_code exactly as visible when possible, like CS 461 or MH 423.
- Keep course_name exactly as visible when possible.
- Use notes for extra context such as source color or "from student current schedule" when helpful.
- Skip any cell that is too blurry or uncertain.
- If no readable plan items exist, explain that the image needs to be clearer.
- After using tools, answer briefly in Arabic and mention what was saved.
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


def _run_with_tools(conversation_input: list[Any], instructions: str, db: Session, user: models.User, max_rounds: int, force_tools: bool = False) -> tuple[str, dict[str, Any]]:
    last_payload: dict[str, Any] = {}

    for round_idx in range(max_rounds):
        extra: dict[str, Any] = {}
        if force_tools and round_idx == 0:
            extra['tool_choice'] = 'required'

        response = client.responses.create(
            model=OPENAI_MODEL,
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
    return _run_with_tools(conversation_input, SYSTEM_INSTRUCTIONS, db=db, user=user, max_rounds=max_rounds)



def run_schedule_image_agent(
    image_bytes: bytes,
    content_type: str,
    filename: str,
    db: Session,
    user: models.User,
    prompt: str | None = None,
    replace_existing: bool = False,
    max_rounds: int = 6,
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
    return _run_with_tools(conversation_input, IMAGE_IMPORT_INSTRUCTIONS, db=db, user=user, max_rounds=max_rounds, force_tools=True)



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
    return _run_with_tools(conversation_input, ACADEMIC_PLAN_IMAGE_IMPORT_INSTRUCTIONS, db=db, user=user, max_rounds=max_rounds, force_tools=True)



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
    return _run_with_tools(conversation_input, IMAGE_CHAT_INSTRUCTIONS, db=db, user=user, max_rounds=max_rounds)
