from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import ChatRequest, ChatResponse
from app.core.config import CHAT_MEMORY_MESSAGES
from app.core.security import get_current_user
from app.db import crud, models
from app.db.session import get_db
from app.services.ai.runtime import (
    MODE_CHAT,
    MODE_IMAGE_CHAT,
    MODE_PLAN_IMPORT_IMAGE,
    MODE_RULES,
    MODE_SCHEDULE_IMPORT,
    ImageInput,
    run_agent,
)

router = APIRouter(prefix='/chat', tags=['chat'])

ALLOWED_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

SCHEDULE_HINT_WORDS = (
    'جدول', 'محاضرات', 'محاضره', 'مقررات', 'المواد', 'schedule', 'timetable', 'class', 'classes',
)
SCHEDULE_IMPORT_WORDS = (
    'اضف', 'أضف', 'احفظ', 'حفظ', 'استخرج', 'رتب', 'رتبه', 'نظم', 'حلل', 'import', 'save', 'add', 'extract',
)
SCHEDULE_REPLACE_WORDS = (
    'جديد', 'الجديد', 'استبدل', 'بدل', 'حدّث', 'حدث', 'replace', 'update',
)

PLAN_HINT_WORDS = (
    'خطة', 'الخطة', 'خطتي', 'الخطة الأكاديمية', 'اكاديمية', 'أكاديمية', 'plan', 'roadmap',
    'study plan', 'degree plan', 'مجتازة', 'المتبقية', 'المقررات المتبقية', 'المقررات المجتازة',
)
PLAN_IMPORT_WORDS = (
    'اضف', 'أضف', 'احفظ', 'حفظ', 'استخرج', 'حلل', 'رتب', 'نظم', 'import', 'save', 'add', 'extract',
)
PLAN_REPLACE_WORDS = (
    'جديد', 'الجديدة', 'الجديد', 'استبدل', 'بدل', 'حدث', 'حدّث', 'replace', 'update', 'استبدال',
)


def _contains_any(text: str, words: tuple) -> bool:
    lowered = text.strip().lower()
    return any(w.lower() in lowered for w in words)


def _is_schedule_prompt(text: str) -> bool:
    return bool(text) and _contains_any(text, SCHEDULE_HINT_WORDS)


def _is_schedule_import_prompt(text: str) -> bool:
    return _is_schedule_prompt(text) and _contains_any(text, SCHEDULE_IMPORT_WORDS)


def _should_replace_schedule(text: str) -> bool:
    return _contains_any(text, SCHEDULE_REPLACE_WORDS)


def _is_academic_plan_prompt(text: str) -> bool:
    return bool(text) and _contains_any(text, PLAN_HINT_WORDS)


def _is_academic_plan_import_prompt(text: str) -> bool:
    return _is_academic_plan_prompt(text) and _contains_any(text, PLAN_IMPORT_WORDS)


def _should_replace_academic_plan(text: str) -> bool:
    return _contains_any(text, PLAN_REPLACE_WORDS)


def _validate_image(file: UploadFile, image_bytes: bytes) -> None:
    content_type = (file.content_type or '').lower().strip()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail='الصيغة المدعومة: PNG أو JPG أو WEBP')
    if not image_bytes:
        raise HTTPException(status_code=400, detail='ملف الصورة فارغ')
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail='حجم الصورة كبير جداً، الحد الأقصى 10 ميغابايت')


def _build_schedule_request_text(prompt: str | None, replace_existing: bool, filename: str) -> str:
    base = (prompt or '').strip() or 'استخرج الجدول من هذه الصورة وأضفه إلى حساب الطالب.'
    if replace_existing:
        base += ' هذا هو الجدول الجديد للطالب. امسح الجدول القديم أولاً ثم أضف الجلسات الجديدة الواضحة.'
    else:
        base += ' احفظ الجلسات الواضحة مباشرة بدون سؤال تأكيدي إذا كانت الصورة مقروءة.'
    return f'{base} اسم الملف: {filename}'


def _build_plan_request_text(prompt: str | None, replace_existing: bool, filename: str) -> str:
    base = (prompt or '').strip() or 'استخرج الخطة الأكاديمية من هذه الصورة واحفظها في حساب الطالب.'
    if replace_existing:
        base += ' هذه هي الخطة الحالية أو الجديدة للطالب. امسح الخطة الأكاديمية القديمة أولاً ثم احفظ المواد الواضحة من الصورة.'
    else:
        base += ' احفظ المواد الواضحة مباشرة بدون سؤال تأكيدي إذا كانت الصورة مقروءة.'
    return f'{base} اسم الملف: {filename}'


@router.get('/history')
def history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> list[dict]:
    msgs = crud.get_last_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    return [
        {
            'role': m.role,
            'content': m.content,
            'meta_json': m.meta_json,
            'created_at': m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ]


@router.delete('/history')
def delete_history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    deleted = crud.delete_all_chat_messages(db, user.id)
    return {'ok': True, 'deleted': deleted}


@router.post('/upload-schedule-image', response_model=ChatResponse)
async def upload_schedule_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ChatResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail='اختر صورة للجدول أولاً')

    image_bytes = await file.read()
    _validate_image(file, image_bytes)

    existing_count = len(crud.get_all_schedule(db, user.id))

    crud.add_chat_message(db, user.id, 'user', f'رفع صورة جدول: {file.filename}')
    assistant_text, meta = run_agent(
        messages=[],
        db=db,
        user=user,
        mode=MODE_SCHEDULE_IMPORT,
        image=ImageInput(
            image_bytes=image_bytes,
            content_type=(file.content_type or '').lower().strip(),
            filename=file.filename,
            prompt=_build_schedule_request_text(prompt=None, replace_existing=False, filename=file.filename),
        ),
        max_rounds=8,
    )

    # Verification: replaces the old 2nd vision pass with a cheap DB count check.
    new_count = len(crud.get_all_schedule(db, user.id))
    delta = new_count - existing_count

    if delta == 0:
        assistant_text += (
            '\n\n⚠️ ما قدرت أستخرج جلسات واضحة من الصورة. '
            'حاول رفع صورة بجودة أعلى أو إضاءة أوضح.'
        )
    elif existing_count > 0:
        assistant_text += (
            '\n\n---\n'
            '📌 **لاحظت أن عندك جدول محفوظ مسبقاً.**\n'
            '• إذا كان هذا **تصحيح لخطأ في جدولك** — تمت إضافة أي جلسات جديدة تلقائياً ✓\n'
            '• إذا كان **جدول ترم جديد** — اكتب "احذف جدولي" ثم ارفع الصورة مرة أخرى لاستبداله بالكامل'
        )

    crud.add_chat_message(db, user.id, 'assistant', assistant_text, meta=meta)
    crud.trim_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    return ChatResponse(text=assistant_text, meta=meta or None)


@router.post('/upload-plan-image', response_model=ChatResponse)
async def upload_plan_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ChatResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail='اختر صورة للخطة أولاً')

    image_bytes = await file.read()
    _validate_image(file, image_bytes)

    crud.add_chat_message(db, user.id, 'user', f'رفع صورة خطة أكاديمية: {file.filename}')
    assistant_text, meta = run_agent(
        messages=[],
        db=db,
        user=user,
        mode=MODE_PLAN_IMPORT_IMAGE,
        image=ImageInput(
            image_bytes=image_bytes,
            content_type=(file.content_type or '').lower().strip(),
            filename=file.filename,
            prompt=_build_plan_request_text(prompt=None, replace_existing=True, filename=file.filename),
        ),
        max_rounds=8,
    )
    crud.add_chat_message(db, user.id, 'assistant', assistant_text, meta=meta)
    crud.trim_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    return ChatResponse(text=assistant_text, meta=meta or None)


@router.post('/with-image', response_model=ChatResponse)
async def chat_with_image(
    message: str = Form(''),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ChatResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail='اختر صورة أولاً')

    image_bytes = await file.read()
    _validate_image(file, image_bytes)

    content_type = (file.content_type or '').lower().strip()
    user_text = (message or '').strip() or 'حلل هذه الصورة وساعدني فيها.'
    crud.add_chat_message(db, user.id, 'user', f'{user_text}\n[image: {file.filename}]')

    # Pick the right mode based on what the user asked.
    if _is_schedule_import_prompt(user_text):
        mode = MODE_SCHEDULE_IMPORT
        prompt = _build_schedule_request_text(user_text, _should_replace_schedule(user_text), file.filename)
    elif _is_academic_plan_import_prompt(user_text):
        mode = MODE_PLAN_IMPORT_IMAGE
        prompt = _build_plan_request_text(user_text, _should_replace_academic_plan(user_text), file.filename)
    else:
        mode = MODE_IMAGE_CHAT
        prompt = user_text

    assistant_text, meta = run_agent(
        messages=[],
        db=db,
        user=user,
        mode=mode,
        image=ImageInput(
            image_bytes=image_bytes,
            content_type=content_type,
            filename=file.filename,
            prompt=prompt,
        ),
        max_rounds=8 if mode in (MODE_SCHEDULE_IMPORT, MODE_PLAN_IMPORT_IMAGE) else 6,
    )

    crud.add_chat_message(db, user.id, 'assistant', assistant_text, meta=meta)
    crud.trim_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    return ChatResponse(text=assistant_text, meta=meta or None)


@router.post('', response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ChatResponse:
    user_text = payload.message.strip()

    crud.add_chat_message(db, user.id, 'user', user_text)
    msgs = crud.get_last_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    history = [{'role': m.role, 'content': m.content} for m in msgs]

    assistant_text, meta = run_agent(messages=history, db=db, user=user, mode=MODE_CHAT)

    crud.add_chat_message(db, user.id, 'assistant', assistant_text, meta=meta)
    crud.trim_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    return ChatResponse(text=assistant_text, meta=meta or None)


@router.post('/university-rules', response_model=ChatResponse)
def chat_university_rules(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ChatResponse:
    user_text = payload.message.strip()

    crud.add_chat_message(db, user.id, 'user', user_text)
    msgs = crud.get_last_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    history = [{'role': m.role, 'content': m.content} for m in msgs]

    assistant_text, meta = run_agent(messages=history, db=db, user=user, mode=MODE_RULES, max_rounds=4)

    crud.add_chat_message(db, user.id, 'assistant', assistant_text, meta=meta)
    crud.trim_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    return ChatResponse(text=assistant_text, meta=meta or None)
