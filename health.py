from fastapi import HTTPException, status, APIRouter
from sqlalchemy import text
from sqlmodel import Session, create_engine, select
import os
from dotenv import load_dotenv
from config import logger

load_dotenv()

router = APIRouter()

engine = create_engine(os.getenv("DB_URL"), echo=True)


@router.get("/health/db")
async def db_health_check():
    """
    Health endpoint to verify database connectivity.
    Attempts a basic query to ensure the DB is responsive.
    """
    # Create a new session instance
    
    try:
        # Execute a simple, lightweight query to test the connection
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
            return {
                "status": "healthy", 
                "database": "connected"
            }
    except Exception as e:
        # Log the exact error internally if needed (e.g., print(e) or logger.error(e))
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )