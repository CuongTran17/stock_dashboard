from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserAccount(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    avatar_data = Column(LONGTEXT, nullable=True)
    password_hash = Column(String(255), nullable=False)
    password_salt = Column(String(255), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DailyOHLCV(Base):
    __tablename__ = "daily_ohlcv"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_daily_ohlcv_symbol_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False, default=0.0)
    high = Column(Float, nullable=False, default=0.0)
    low = Column(Float, nullable=False, default=0.0)
    close = Column(Float, nullable=False, default=0.0)
    volume = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TechnicalCache(Base):
    __tablename__ = "technical_cache"
    __table_args__ = (
        UniqueConstraint("symbol", "start_date", "end_date", "limit_value", name="uq_technical_cache_signature"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    limit_value = Column(Integer, nullable=False, default=365)
    history_count = Column(Integer, nullable=False, default=0)
    history_last_time = Column(String(32), nullable=True)
    payload_json = Column(LONGTEXT, nullable=False)
    source = Column(String(64), nullable=False, default="mysql")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)


class CompanyOverviewCache(Base):
    __tablename__ = "company_overview_cache"

    symbol = Column(String(50), primary_key=True)
    payload_json = Column(LONGTEXT, nullable=False)
    source = Column(String(64), nullable=False, default="vnstock")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)


class FinancialReportCache(Base):
    __tablename__ = "financial_report_cache"
    __table_args__ = (
        UniqueConstraint("symbol", "report_type", name="uq_financial_report_cache_symbol_type"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    report_type = Column(String(20), nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    payload_json = Column(LONGTEXT, nullable=False)
    source = Column(String(64), nullable=False, default="vnstock")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)


class NewsCache(Base):
    __tablename__ = "news_cache"

    symbol = Column(String(50), primary_key=True)
    item_count = Column(Integer, nullable=False, default=0)
    payload_json = Column(LONGTEXT, nullable=False)
    source = Column(String(64), nullable=False, default="vnstock")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)


class EventsCache(Base):
    __tablename__ = "events_cache"

    symbol = Column(String(50), primary_key=True)
    item_count = Column(Integer, nullable=False, default=0)
    payload_json = Column(LONGTEXT, nullable=False)
    source = Column(String(64), nullable=False, default="vnstock")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
