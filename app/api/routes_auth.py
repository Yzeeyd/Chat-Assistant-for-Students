from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import LoginRequest, SignupRequest, TokenResponse
from app.core.security import create_access_token, hash_password, verify_password
from app.db import crud
from app.db.session import SessionLocal, get_db

router = APIRouter(prefix='/auth', tags=['auth'])


def _auto_populate_plan_background(user_id: int, major: str) -> None:
    """Background task: parse major's plan PDF via AI and populate the user's academic plan."""
    from app.services.docs import get_plan_text
    from app.services.ai.runtime import MODE_PLAN_IMPORT_TEXT, run_agent
    db = SessionLocal()
    try:
        user = crud.get_user_by_id(db, user_id)
        if not user:
            return
        plan_text = get_plan_text(major)
        if not plan_text:
            return
        # Check again right before the AI call — the user may have already uploaded their plan image.
        # Even if items exist, we proceed so the PDF fills gaps the image missed.
        # Status non-downgrade logic in add_academic_plan_item protects existing completed/in_progress.
        messages = [
            {
                'role': 'user',
                'content': (
                    f'استورد خطة الدراسة للتخصص {major} التالية وأضف جميع المواد لحسابي.\n\n'
                    f'{plan_text[:9000]}'
                ),
            }
        ]
        run_agent(messages=messages, db=db, user=user, mode=MODE_PLAN_IMPORT_TEXT, max_rounds=8)
    except Exception:
        pass
    finally:
        db.close()


@router.post('/signup')
def signup(payload: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict[str, str | int]:
    email = payload.email.strip().lower()
    if crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail='Email already exists')
    user = crud.create_user(
        db, payload.name, email, hash_password(payload.password),
        college=payload.college,
        major=payload.major,
        track=payload.track,
    )
    if user.major:
        background_tasks.add_task(_auto_populate_plan_background, user.id, user.major)
    return {'id': user.id, 'name': user.name, 'email': user.email, 'major': user.major}


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Wrong email or password')
    return TokenResponse(access_token=create_access_token(user.id))
