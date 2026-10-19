import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

logger = logging.getLogger("journey_tracker.database")

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "todolist")
AUTO_FALLBACK_SQLITE = os.getenv("AUTO_FALLBACK_SQLITE", "true").lower() in ("true", "1", "yes")

custom_db_url = os.getenv("DATABASE_URL")

def get_engine():
    if custom_db_url:
        return create_engine(custom_db_url, pool_pre_ping=True)

    # Try connecting to MySQL and ensure database exists
    mysql_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    try:
        import pymysql
        # Attempt to create database if it doesn't exist
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            connect_timeout=3
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()

        engine = create_engine(mysql_url, pool_pre_ping=True)
        # Test connection
        with engine.connect() as test_conn:
            pass
        logger.info(f"Connected to MySQL database '{DB_NAME}' successfully.")
        return engine
    except Exception as exc:
        if AUTO_FALLBACK_SQLITE:
            sqlite_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "journey_tracker.db"))
            sqlite_url = f"sqlite:///{sqlite_file}"
            logger.warning(
                f"Could not connect to MySQL ({exc}). Falling back to local SQLite: {sqlite_url}"
            )
            return create_engine(sqlite_url, connect_args={"check_same_thread": False})
        else:
            raise exc

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
