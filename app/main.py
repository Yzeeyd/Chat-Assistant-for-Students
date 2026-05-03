from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.api.routes_dashboard import router as dashboard_router
from app.core.config import APP_NAME, CORS_ORIGINS, ENABLE_DOCS, UPLOADS_DIR, BASE_DIR
from app.db.session import Base, engine


def _run_migrations() -> None:
    """Add new columns/tables to existing databases without dropping data."""
    migrations = [
        "ALTER TABLE reminders ADD COLUMN remind_at DATETIME",
        "ALTER TABLE assignments ADD COLUMN status VARCHAR(40) NOT NULL DEFAULT 'pending'",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # column already exists or table doesn't exist yet


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    yield


app = FastAPI(
    title=APP_NAME,
    lifespan=lifespan,
    docs_url='/docs' if ENABLE_DOCS else None,
    redoc_url='/redoc' if ENABLE_DOCS else None,
    openapi_url='/openapi.json' if ENABLE_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] if '*' in CORS_ORIGINS else CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(dashboard_router)


@app.get('/health', tags=['system'])
def health() -> dict[str, str]:
    return {'status': 'ok'}


app.mount('/static', StaticFiles(directory=str(UPLOADS_DIR)), name='static')

WEB_DIR = BASE_DIR / 'web'
if WEB_DIR.exists():
    app.mount('/', StaticFiles(directory=str(WEB_DIR), html=True), name='web')
