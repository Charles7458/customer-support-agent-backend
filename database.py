import os
from dotenv import load_dotenv
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as SAAsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from typing import Annotated
from config import logger

load_dotenv()

db_url = os.getenv("ASYNC_DB_URL")

if not db_url:
    raise RuntimeError(
        "ASYNC_DB_URL environment variable is not set. "
        "Check your Render environment variables dashboard."
    )

# Append SSL requirement if not already present (required for Render Postgres)
if "sslmode" not in db_url and "ssl=" not in db_url:
    separator = "&" if "?" in db_url else "?"
    db_url = f"{db_url}{separator}ssl=require"

engine = create_async_engine(
    db_url,
    echo=True,
    pool_pre_ping=True,       # Validates connection before use — fixes stale connections
    pool_size=5,              # Stay within Render free tier connection limits
    max_overflow=2,           # Allow slight burst, but keep total ≤ 7
    pool_timeout=30,          # Fail fast instead of hanging indefinitely
    pool_recycle=1800,        # Recycle connections every 30 min (before Render kills them)
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
    async with async_session_factory() as session:  # context manager handles close()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("DB session error — rolled back", exc_info=True)
            raise

SessionDep = Annotated[AsyncSession, Depends(get_session)]