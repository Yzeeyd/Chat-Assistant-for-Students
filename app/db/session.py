from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL

connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}

pool_kwargs: dict = {}
if DATABASE_URL.startswith('mysql'):
    pool_kwargs = {'pool_size': 5, 'max_overflow': 10, 'pool_recycle': 1800}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args, **pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
