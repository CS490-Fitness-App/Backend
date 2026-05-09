# Creates the SQLAlchemy engine and session factory for the MySQL database.
# Exposes get_db(), a FastAPI dependency that yields a database session per request.

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH, override=True)

DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_NAME     = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# TiDB Cloud (and other cloud MySQL) requires SSL
connect_args = {"ssl": {"ssl_mode": "VERIFY_IDENTITY"}} if os.getenv("DB_SSL") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
