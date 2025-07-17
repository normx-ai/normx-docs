from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=getattr(settings, 'DATABASE_POOL_SIZE', 5),
    max_overflow=getattr(settings, 'DATABASE_MAX_OVERFLOW', 10),
    poolclass=NullPool if settings.ENV == "test" else None,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()