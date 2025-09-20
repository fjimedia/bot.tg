from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config.settings import settings
from .models import Base
import logging
import sqlite3
logger = logging.getLogger(__name__)

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except SQLAlchemyError as e:
    logger.critical(f"Database connection error: {e}")
    raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.critical(f"Database initialization failed: {e}")
        raise

def get_db():
    conn = sqlite3.connect('database.db')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    if "sqlite" in settings.DATABASE_URL:
        from pathlib import Path
        db_path = Path("./database.db")
        if not db_path.exists():
            db_path.touch()