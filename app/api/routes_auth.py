from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import LoginRequest, SignupRequest, TokenResponse
from app.core.security import create_access_token, hash_password, verify_password
from app.db import crud
from app.db.session import get_db

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/signup')
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> dict[str, str | int]:
    email = payload.email.strip().lower()
    if crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail='Email already exists')
    user = crud.create_user(
        db, payload.name, email, hash_password(payload.password),
        college=payload.college,
        major=payload.major,
        track=payload.track,
    )
    return {'id': user.id, 'name': user.name, 'email': user.email, 'major': user.major}


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Wrong email or password')
    return TokenResponse(access_token=create_access_token(user.id))
