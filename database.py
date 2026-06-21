import os
from dotenv import load_dotenv
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from typing import Annotated
from config import logger

load_dotenv()

db_url = os.getenv("ASYNC_DB_URL")

engine = create_async_engine(db_url, echo=True)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session():
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error("Get db session failed")
        logger.error(e)
        await session.rollback()
        raise
    finally:
        await session.close()

SessionDep = Annotated[AsyncSession, Depends(get_session)]
