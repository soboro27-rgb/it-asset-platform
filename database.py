from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

# 로컬: SQLite / Render: PostgreSQL (DATABASE_URL 환경변수)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/mgit.db")

# Render PostgreSQL URL은 postgres:// → postgresql:// 로 변환 필요
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

is_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
