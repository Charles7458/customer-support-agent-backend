from fastapi import HTTPException, status, APIRouter
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession
from database import get_session  # Import your SessionLocal class

router = APIRouter()

@router.get("/health/db")
async def db_health_check():
    """
    Health endpoint to verify database connectivity.
    Attempts a basic query to ensure the DB is responsive.
    """
    # Create a new session instance
    db: AsyncSession = await get_session()
    try:
        # Execute a simple, lightweight query to test the connection
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy", 
            "database": "connected"
        }
    except Exception as e:
        # Log the exact error internally if needed (e.g., print(e) or logger.error(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
    finally:
        # Always close the session to prevent connection leaks
        await db.close()