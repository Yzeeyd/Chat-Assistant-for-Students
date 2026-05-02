from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

APP_NAME = os.getenv('APP_NAME', 'Student Assistant System v2')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
JWT_SECRET = os.getenv('JWT_SECRET', 'change_me')
JWT_ALG = os.getenv('JWT_ALG', 'HS256')
JWT_EXPIRE_MIN = int(os.getenv('JWT_EXPIRE_MIN', '1440'))
CHAT_MEMORY_MESSAGES = int(os.getenv('CHAT_MEMORY_MESSAGES', '20'))
ENABLE_DOCS = os.getenv('ENABLE_DOCS', 'true').lower() == 'true'
CORS_ORIGINS = [x.strip() for x in os.getenv('CORS_ORIGINS', '*').split(',') if x.strip()]
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+pysqlite:///./student_assistant_v2.db').strip()

UPLOADS_DIR = BASE_DIR / 'uploads'
ROOMS_DIR = UPLOADS_DIR / 'rooms'
ASSIGNMENTS_DIR = UPLOADS_DIR / 'assignments'
for path in (UPLOADS_DIR, ROOMS_DIR, ASSIGNMENTS_DIR):
    path.mkdir(parents=True, exist_ok=True)
