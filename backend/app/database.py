import logging
import os
from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

db_path = settings.DATABASE_URL.replace("sqlite:///", "")
db_dir = os.path.dirname(db_path)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Enable WAL mode for concurrent reads during writes, and set busy timeout
from sqlalchemy import event

@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"
_ALEMBIC_DIR = _BACKEND_DIR / "alembic"


def _alembic_config() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


def init_db() -> None:
    """Bring the database schema up to head via Alembic.

    Pre-Alembic legacy DBs are stamped at head so we don't try to recreate tables
    that already exist; fresh DBs and partially-migrated DBs run upgrade head.
    """
    from app import models  # noqa: F401

    inspector = inspect(engine)
    has_alembic_version = inspector.has_table("alembic_version")
    existing_tables = set(inspector.get_table_names())
    has_legacy_tables = "bills" in existing_tables

    cfg = _alembic_config()

    if not has_alembic_version and has_legacy_tables:
        # Legacy DB: stamp at head so Alembic knows the initial state,
        # then let upgrade handle adding any missing tables/columns.
        command.stamp(cfg, "head")
        logger.info("alembic_stamped_head")

    command.upgrade(cfg, "head")
    logger.info(
        "alembic_upgrade_completed",
        extra={"event": "alembic_upgrade_completed"},
    )


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
