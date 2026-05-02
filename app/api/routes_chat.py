from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import ChatRequest, ChatResponse
from app.core.config import CHAT_MEMORY_MESSAGES
from app.core.security import get_current_user
from app.db import crud, models
from app.db.session import get_db
from app.services.ai.runtime import (
    run_academic_plan_image_agent,
    run_agent,
    run_agent_with_image,
    run_schedule_image_agent,
    run_university_rules_agent,
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

    crud.add_chat_message(db, user.id, 'user', f'رفع صورة جدول: {file.filename}')
    assistant_text, meta = run_schedule_image_agent(
        image_bytes=image_bytes,
        content_type=(file.content_type or '').lower().strip(),
        filename=file.filename,
        db=db,
        user=user,
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
    assistant_text, meta = run_academic_plan_image_agent(
        image_bytes=image_bytes,
        content_type=(file.content_type or '').lower().strip(),
        filename=file.filename,
        db=db,
        user=user,
        replace_existing=True,
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

    if _is_schedule_import_prompt(user_text):
        assistant_text, meta = run_schedule_image_agent(
            prompt=user_text,
            replace_existing=_should_replace_schedule(user_text),
            image_bytes=image_bytes,
            content_type=content_type,
            filename=file.filename,
            db=db,
            user=user,
        )
    elif _is_academic_plan_import_prompt(user_text):
        assistant_text, meta = run_academic_plan_image_agent(
            prompt=user_text,
            replace_existing=_should_replace_academic_plan(user_text),
            image_bytes=image_bytes,
            content_type=content_type,
            filename=file.filename,
            db=db,
            user=user,
        )
    else:
        assistant_text, meta = run_agent_with_image(
            prompt=user_text,
            image_bytes=image_bytes,
            content_type=content_type,
            filename=file.filename,
            db=db,
            user=user,
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

    assistant_text, meta = run_agent(history_messages=history, db=db, user=user)

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

    assistant_text, meta = run_university_rules_agent(history_messages=history, db=db, user=user)

    crud.add_chat_message(db, user.id, 'assistant', assistant_text, meta=meta)
    crud.trim_chat_messages(db, user.id, CHAT_MEMORY_MESSAGES)
    return ChatResponse(text=assistant_text, meta=meta or None)
