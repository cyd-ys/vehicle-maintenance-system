"""数据库连接与会话管理（SQLAlchemy 2.0）。"""
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


def _resolve_database_url() -> str:
    """优先使用 MySQL；若不可用且允许降级，则使用本地 SQLite。"""
    url = settings.DATABASE_URL
    if url.startswith("mysql"):
        try:
            probe = create_engine(url, pool_pre_ping=True)
            with probe.connect() as conn:
                conn.execute(text("SELECT 1"))
            probe.dispose()
            return url
        except Exception as exc:  # noqa: BLE001
            if not settings.ALLOW_SQLITE_FALLBACK:
                raise
            print(f"[database] MySQL 连接失败（{exc}），已降级为 SQLite。")
    # SQLite 相对 backend 目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sqlite_file = os.path.join(base_dir, settings.SQLITE_PATH)
    return f"sqlite:///{sqlite_file}"


DATABASE_URL = _resolve_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖：请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
