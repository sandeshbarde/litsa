"""
Database engine, session factory, and initialization.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from app.models import Base
from app.config import settings

logger = logging.getLogger(__name__)

import os
import tempfile

# Engine configuration
_engine_kwargs = {}
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if db_url.startswith("sqlite"):
    if os.environ.get("VERCEL") and ("dubai_leads.db" in db_url):
        tmp_db = os.path.join(tempfile.gettempdir(), "dubai_leads.db")
        db_url = f"sqlite:///{tmp_db}"
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
elif db_url.startswith("postgresql"):
    _engine_kwargs = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

engine = create_engine(
    db_url,
    echo=settings.debug,
    **_engine_kwargs,
)

# Enable WAL mode for SQLite for better concurrency
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")


# Initialize tables on import
init_db()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
