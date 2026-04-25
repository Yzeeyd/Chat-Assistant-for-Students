import json
from typing import Any
import os
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.db import models
from app.services.tools import TOOL_DEFINITIONS, execute_tool
from app.db import models


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

DEVELOPER_INSTRUCTIONS = """
You are an AI-powered Student Assistant System.
Always answer in the same language used by the student.

Product vision:
- Support students through a simple chat interface.
- Main domains: schedule management, reminders, academic plan tracking, course recommendations, and university rules.
- Keep the experience conversational and lightweight.

Style rules:
- Be concise, practical, and student-friendly.
- Do not show menus or capability lists unless the student asks.
- For greetings, answer briefly and ask how you can help.
- Ask for missing required information instead of guessing.

Schedule rules:
- Day mapping is fixed: 1=Sunday, 2=Monday, 3=Tuesday, 4=Wednesday, 5=Thursday, 6=Friday, 7=Saturday.
- If the user pastes a large Arabic or English schedule, or uploads a schedule image/PDF, treat it as data entry.
- Prefer bulk_add_classes when multiple entries can be extracted.
- Never expose raw JSON, tool payloads, or internal parsing logic.
- Each time slot must be stored separately.
- Keep room values normalized.
- When reading attachments, first decide whether the attachment is a weekly class schedule, an academic plan/study plan, or neither.
- If it is a schedule, extract classes and save them with schedule tools.
- If it is an academic plan, save its courses with academic plan tools.
- If the attachment is unclear, ask one short clarifying question.

Reminder rules:
- For homework, deadlines, exams, and personal tasks, prefer reminders instead of file uploads.
- Use create_reminder for deadlines, exams, classes, or personal study reminders.
- If the time is unclear, ask a short follow-up question.

Academic plan rules:
- Use add_academic_plan_item when the student wants to track planned or completed courses.
- Use recommend_courses when the user asks what to take next or asks for suggestions based on saved data.
- Recommendations must be grounded in saved academic plan items and current schedule only.

University rules:
- Use search_university_rules for regulations, attendance, withdrawals, grading, or academic warnings.
- If nothing is found, say that the rule database needs to be filled with the university's official policy documents.

Final response rules:
- After successful write actions, respond with a short confirmation.
- When tools return structured results, summarize them naturally.
- Avoid repeating unnecessary details.
""".strip()

def run_agent(
    history_messages: list[dict[str, str]],
    db: Session,
    user: models.User,
    max_rounds: int = 6,
) -> tuple[str, dict[str, Any]]:
    if not client:
        return ('OpenAI API key is missing. Add OPENAI_API_KEY in .env.', {})

    conversation_input: list[Any] = list(history_messages)
    last_payload: dict[str, Any] = {}

    for _ in range(max_rounds):
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=DEVELOPER_INSTRUCTIONS,
            tools=TOOL_DEFINITIONS,
            input=conversation_input,
        )
        conversation_input += response.output
        tool_calls = [item for item in response.output if getattr(item, 'type', None) == 'function_call']
        # If the model didn't call any tools, return its text response as the final answer
        if not tool_calls:
            return ((response.output_text or '').strip(), last_payload)
        # If there are tool calls, execute them and feed the results back into the conversation
        for tool_call in tool_calls:
            try:
                # The model's tool call arguments should be a JSON string. Parse it into a dict.
                arguments = json.loads(tool_call.arguments or '{}')
            except json.JSONDecodeError:
                # If parsing fails, return an error message as the tool output
                result = {'ok': False, 'error': 'Invalid JSON arguments from model'}
            else:
                try:
                    # Execute the tool and get the result. The result can be any JSON-serializable data.
                    result = execute_tool(tool_call.name, arguments, db=db, user=user)
                except Exception as exc:
                    # If tool execution raises an exception, capture it and return an error message as the tool output
                    result = {'ok': False, 'error': str(exc)}
            # If the result is a dict and contains any of the expected keys, save them to last_payload for returning at the end
            if isinstance(result, dict):
                for key in ('items', 'reminders', 'academic_plan', 'assignments', 'rules'):
                    if key in result:
                        last_payload[key] = result.get(key) or []

            conversation_input.append(
                {
                    'type': 'function_call_output',
                    'call_id': tool_call.call_id,
                    'output': json.dumps(result, ensure_ascii=False),
                }
            )

    return ('عذرًا، صار عدد محاولات الأدوات كبير. حاول مرة ثانية برسالة أبسط.', last_payload)
