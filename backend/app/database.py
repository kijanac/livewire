import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

# Ensure the data directory exists for SQLite
db_path = settings.DATABASE_URL.replace("sqlite:///", "")
db_dir = os.path.dirname(db_path)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Create all tables defined by SQLAlchemy models."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Safe column additions for schema evolution (SQLite has no migrations)
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    existing_bill_cols = {col["name"] for col in inspector.get_columns("bills")}
    with engine.begin() as conn:
        if "topics" not in existing_bill_cols:
            conn.execute(text("ALTER TABLE bills ADD COLUMN topics TEXT"))

    if "bill_briefings" in inspector.get_table_names():
        existing_briefing_cols = {col["name"] for col in inspector.get_columns("bill_briefings")}
        with engine.begin() as conn:
            if "organizing" not in existing_briefing_cols:
                conn.execute(text("ALTER TABLE bill_briefings ADD COLUMN organizing TEXT"))
            if "reception" not in existing_briefing_cols:
                conn.execute(text("ALTER TABLE bill_briefings ADD COLUMN reception TEXT"))


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
