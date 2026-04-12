import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]

# Load backend_v2/.env first so local backend settings win over root defaults.
load_dotenv(BASE_DIR / ".env")
load_dotenv()

# MySQL Database Connection String
# Example: mysql+mysqlconnector://user:password@localhost/dbname
DB_URL = os.getenv("MYSQL_URL", "mysql+mysqlconnector://root:@localhost/vnstock_data")
ASYNC_DB_URL = os.getenv(
    "MYSQL_ASYNC_URL",
    DB_URL.replace("mysql+mysqlconnector://", "mysql+aiomysql://"),
)

engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
    future=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_engine = create_async_engine(
    ASYNC_DB_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
    future=True,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def _ensure_payload_columns_longtext() -> None:
    statements = [
        "ALTER TABLE company_overview_cache MODIFY COLUMN payload_json LONGTEXT NOT NULL",
        "ALTER TABLE financial_report_cache MODIFY COLUMN payload_json LONGTEXT NOT NULL",
        "ALTER TABLE technical_cache MODIFY COLUMN payload_json LONGTEXT NOT NULL",
        "ALTER TABLE news_cache MODIFY COLUMN payload_json LONGTEXT NOT NULL",
        "ALTER TABLE events_cache MODIFY COLUMN payload_json LONGTEXT NOT NULL",
    ]

    with engine.begin() as connection:
        for statement in statements:
            try:
                connection.execute(text(statement))
            except Exception as exc:
                logger.warning("Schema update skipped for statement '%s': %s", statement, exc)


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_payload_columns_longtext()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db
