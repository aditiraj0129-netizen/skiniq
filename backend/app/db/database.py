"""
Database connection setup.

Why SQLAlchemy: it's the industry-standard Python ORM. Using it (instead of raw SQL)
shows you understand real backend engineering patterns, and makes it trivial to swap
Postgres for SQLite during local dev without changing any other code.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# During local development we default to SQLite (zero setup).
# In production (deployment step) we switch to Postgres via env var.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skiniq.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: gives each request its own DB session, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
