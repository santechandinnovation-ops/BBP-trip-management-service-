from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from app.config.database import db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        db.return_connection(conn)
        
        return {
            "message": "healthy",
            "service": "BBP Trip Management Service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "message": "unhealthy",
                "service": "BBP Trip Management Service",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )
