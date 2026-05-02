from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.api.routes_dashboard import router as dashboard_router
from app.core.config import APP_NAME, CORS_ORIGINS, ENABLE_DOCS, UPLOADS_DIR, BASE_DIR
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    docs_url='/docs' if ENABLE_DOCS else None,
    redoc_url='/redoc' if ENABLE_DOCS else None,
    openapi_url='/openapi.json' if ENABLE_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ['*'] else ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.mount('/static', StaticFiles(directory=str(UPLOADS_DIR)), name='static')

WEB_DIR = BASE_DIR / 'web'
if WEB_DIR.exists():
    app.mount('/', StaticFiles(directory=str(WEB_DIR), html=True), name='web')


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
