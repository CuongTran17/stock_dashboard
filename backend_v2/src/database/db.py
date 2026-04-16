import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
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


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    database_name = engine.url.database
    if not database_name:
        return False

    query = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = :db
          AND table_name = :table
          AND column_name = :column
        LIMIT 1
        """
    )
    return connection.execute(query, {"db": database_name, "table": table_name, "column": column_name}).first() is not None


def _index_exists(connection, table_name: str, index_name: str) -> bool:
    database_name = engine.url.database
    if not database_name:
        return False

    query = text(
        """
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = :db
          AND table_name = :table
          AND index_name = :index
        LIMIT 1
        """
    )
    return connection.execute(query, {"db": database_name, "table": table_name, "index": index_name}).first() is not None


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


def _ensure_user_profile_columns() -> None:
    column_statements = [
        ("first_name", "ALTER TABLE users ADD COLUMN first_name VARCHAR(120) NULL"),
        ("last_name", "ALTER TABLE users ADD COLUMN last_name VARCHAR(120) NULL"),
        ("avatar_data", "ALTER TABLE users ADD COLUMN avatar_data LONGTEXT NULL"),
        ("phone", "ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL"),
        ("fullname", "ALTER TABLE users ADD COLUMN fullname VARCHAR(255) NULL"),
        ("password_salt", "ALTER TABLE users ADD COLUMN password_salt VARCHAR(255) NULL"),
        ("is_active", "ALTER TABLE users ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1"),
        ("last_login_at", "ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL"),
        ("role", "ALTER TABLE users ADD COLUMN role ENUM('user','premium','admin') NOT NULL DEFAULT 'user'"),
        ("is_locked", "ALTER TABLE users ADD COLUMN is_locked TINYINT(1) NOT NULL DEFAULT 0"),
        ("locked_reason", "ALTER TABLE users ADD COLUMN locked_reason VARCHAR(500) NULL"),
    ]

    with engine.begin() as connection:
        for column_name, statement in column_statements:
            if _column_exists(connection, "users", column_name):
                continue
            try:
                connection.execute(text(statement))
            except Exception as exc:
                logger.warning("Schema update skipped for statement '%s': %s", statement, exc)

        try:
            if _column_exists(connection, "users", "phone") and not _index_exists(connection, "users", "uq_users_phone"):
                connection.execute(text("ALTER TABLE users ADD UNIQUE KEY uq_users_phone (phone)"))
        except Exception as exc:
            logger.warning("Schema update skipped for statement '%s': %s", "ALTER TABLE users ADD UNIQUE KEY uq_users_phone (phone)", exc)

        try:
            if _column_exists(connection, "users", "role"):
                connection.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''"))
        except Exception as exc:
            logger.warning("Schema update skipped for statement '%s': %s", "UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''", exc)

        try:
            if _column_exists(connection, "users", "is_active"):
                connection.execute(text("UPDATE users SET is_active = 1 WHERE is_active IS NULL"))
        except Exception as exc:
            logger.warning("Schema update skipped for statement '%s': %s", "UPDATE users SET is_active = 1 WHERE is_active IS NULL", exc)


def _ensure_subscription_columns() -> None:
    column_statements = [
        ("original_amount", "ALTER TABLE user_subscriptions ADD COLUMN original_amount DECIMAL(12,2) NULL"),
        ("discount_amount", "ALTER TABLE user_subscriptions ADD COLUMN discount_amount DECIMAL(12,2) NOT NULL DEFAULT 0"),
        ("promo_code", "ALTER TABLE user_subscriptions ADD COLUMN promo_code VARCHAR(50) NULL"),
        ("flash_sale_id", "ALTER TABLE user_subscriptions ADD COLUMN flash_sale_id INT NULL"),
    ]

    with engine.begin() as connection:
        for column_name, statement in column_statements:
            if _column_exists(connection, "user_subscriptions", column_name):
                continue
            try:
                connection.execute(text(statement))
            except Exception as exc:
                logger.warning("Schema update skipped for statement '%s': %s", statement, exc)


def _ensure_user_portfolio_columns() -> None:
    column_statements = [
        ("tp_price", "ALTER TABLE user_portfolios ADD COLUMN tp_price FLOAT NULL"),
        ("sl_price", "ALTER TABLE user_portfolios ADD COLUMN sl_price FLOAT NULL"),
    ]

    with engine.begin() as connection:
        for column_name, statement in column_statements:
            if _column_exists(connection, "user_portfolios", column_name):
                continue
            try:
                connection.execute(text(statement))
            except Exception as exc:
                logger.warning("Schema update skipped for statement '%s': %s", statement, exc)


def _is_transient_concurrent_ddl_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return "concurrent ddl" in message or "being modified by concurrent ddl" in message


def _create_all_with_retry(max_attempts: int = 5) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except DBAPIError as exc:
            if not _is_transient_concurrent_ddl_error(exc) or attempt >= max_attempts:
                raise

            # MySQL may briefly lock metadata while another DDL finishes.
            wait_seconds = min(0.6 * attempt, 3.0)
            logger.warning(
                "DB schema create_all retry %s/%s after transient concurrent DDL error: %s",
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(wait_seconds)


def init_db():
    _create_all_with_retry()
    _ensure_payload_columns_longtext()
    _ensure_user_profile_columns()
    _ensure_subscription_columns()
    _ensure_user_portfolio_columns()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db
