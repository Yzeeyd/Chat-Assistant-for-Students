from pydantic import BaseModel
from typing import List, Optional

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChatRequest(BaseModel):
    message: str

class ScheduleItemOut(BaseModel):
    course_name: str
    start_time: str
    end_time: str
    room_text: str
    image_url: Optional[str] = None

class ChatResponse(BaseModel):
    text: str
    items: List[ScheduleItemOut] = []