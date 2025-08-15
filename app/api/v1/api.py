"""API v1 router configuration.

This module sets up the main API router and includes all sub-routers for different
endpoints like authentication and chatbot functionality.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.auth import router as auth_router
from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.documents import router as documents_router
# from app.api.v1.firebase_auth import router as firebase_auth_router
from app.api.v1.rag import router as rag_router  # Legacy support
from app.api.v1.users import router as users_router
from app.api.v1.whatsapp import router as whatsapp_router
from app.core.logging import logger
from app.dependencies import get_agno_agent

api_router = APIRouter()

# Include routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])  # Legacy support
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        dict: Health status information.
    """
    logger.info("health_check_called")
    return {"status": "healthy", "version": "1.0.0"}


@api_router.get("/health/agno")
async def agno_health_check(agno_agent=Depends(get_agno_agent)):
    """AgnoAgent health check endpoint.
    
    This endpoint verifies that AgnoAgent is fully operational and ready to handle requests.
    If AgnoAgent is not available, this endpoint will fail with a 503 error.

    Returns:
        dict: AgnoAgent health status and configuration details.
        
    Raises:
        HTTPException: 503 if AgnoAgent is not healthy
    """
    try:
        logger.info("agno_health_check_called")
        
        if agno_agent is None:
            logger.error("agno_agent_not_available_in_health_check")
            raise HTTPException(
                status_code=503,
                detail="AgnoAgent is not available - initialization failed"
            )
        
        # Perform detailed health check
        health_result = await agno_agent.health_check()
        
        if health_result.get("status") != "healthy":
            logger.error("agno_agent_health_check_failed", result=health_result)
            raise HTTPException(
                status_code=503,
                detail=f"AgnoAgent health check failed: {health_result}"
            )
        
        logger.info("agno_agent_health_check_passed", result=health_result)
        return {
            "status": "healthy",
            "agno_status": health_result,
            "version": "1.0.0",
            "timestamp": "2025-08-15T00:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("agno_health_check_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"AgnoAgent health check error: {str(e)}"
        )
