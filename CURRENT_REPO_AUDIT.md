# Current Repo Audit

This file summarizes the most important problems found in the uploaded project.

## Critical issues

1. **Database config conflict**
   - `app/core/config.py` supports SQLite fallback.
   - `app/db/session.py` ignores that and always builds a MySQL URL from env pieces.
   - Result: local startup can break even when fallback logic exists.

2. **Models and tool layer do not match**
   - `tools.py` expects `course_code`, `credits`, and `instructor` on schedule items.
   - `models.py` schedule table does not define those fields.
   - Result: serialization and writes can fail.

3. **CRUD functions are missing**
   - `tools.py` calls functions such as `get_all_schedule`, `update_schedule_item`, `delete_one_schedule_item`, `create_reminder`, `list_reminders`, `add_academic_plan_item`, `search_university_rules`, and more.
   - `crud.py` only defines user, schedule add/get/delete-all, and chat-memory helpers.
   - Result: many tool calls will crash.

4. **Dead code in tool execution**
   - In `tools.py`, reminder / academic plan / rules / assignment branches are commented out as `#if name == ...`.
   - The indented code below them is unreachable because `clear_schedule` returns before those lines.
   - Result: those features are effectively disabled.

5. **Chat route drops returned payload**
   - `run_agent()` returns `(text, dict)`.
   - `routes_chat.py` treats the second value as a list and therefore does not expose tool payload to the frontend.
   - Result: schedule cards and structured results may not appear.

6. **README and runtime behavior conflict**
   - README says `/docs` is available.
   - `main.py` disables docs, redoc, and openapi.
   - Result: documentation instructions do not match real behavior.

7. **Sensitive file hygiene issue**
   - The uploaded zip includes `.env`.
   - Result: secrets may be unintentionally shared if the project is uploaded publicly.

## Architectural gap

The repository description promises:
- reminders
- academic planning
- course recommendations
- university rules
- assignment upload support

But the actual repo is still mostly a **schedule chatbot with auth**. The product vision is broader than the implemented code.
