"""Deep health check endpoint for comprehensive system diagnostics.

This module provides detailed health checking functionality
that goes beyond basic connectivity tests.
"""

import os
import uuid
from datetime import datetime

import psutil
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.main import (
    SECURITY_HEADERS,
    app,
)
from app.services.database import database_service


@app.get("/health/deep")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["health"][0])
async def deep_health_check(request: Request) -> JSONResponse:
    """Deep health check endpoint with comprehensive system diagnostics.

    This endpoint performs more thorough health checks including:
    - Database connection and query performance
    - Elasticsearch connectivity and index status
    - Agno agent functionality
    - Memory and resource usage
    - Service dependencies

    Returns:
        JSONResponse: Detailed health status information
    """
    logger.info("deep_health_check_called")

    try:
        start_time = datetime.now()

        # Database deep health check
        db_details = {"connected": False, "response_time_ms": None, "error": None}
        try:
            db_start = datetime.now()
            db_healthy = await database_service.health_check()
            db_response_time = (datetime.now() - db_start).total_seconds() * 1000

            db_details.update(
                {
                    "connected": db_healthy,
                    "response_time_ms": round(db_response_time, 2),
                }
            )
        except Exception as e:
            db_details["error"] = str(e)

        # RAG service deep health check
        rag_details = {
            "status": "unknown",
            "elasticsearch": "unknown",
            "index": "unknown",
            "error": None,
        }
        try:
            from app.services.rag import rag_service

            rag_health = await rag_service.health_check()
            rag_details.update(rag_health)
        except Exception as e:
            rag_details["error"] = str(e)

        # Agno agent deep health check
        agno_details = {
            "status": "unknown",
            "agent_ready": False,
            "tools_count": 0,
            "error": None,
        }
        try:
            from app.core.agno.graph import AgnoAgent

            agent = AgnoAgent()
            agno_health = await agent.health_check()
            agno_details.update(agno_health)
        except Exception as e:
            agno_details["error"] = str(e)

        # System resource information
        try:
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage("/")
            cpu_percent = psutil.cpu_percent(interval=0.1)

            system_details = {
                "memory": {
                    "total_mb": round(memory_info.total / 1024 / 1024, 2),
                    "available_mb": round(memory_info.available / 1024 / 1024, 2),
                    "used_percent": memory_info.percent,
                },
                "disk": {
                    "total_gb": round(disk_info.total / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk_info.free / 1024 / 1024 / 1024, 2),
                    "used_percent": round((disk_info.used / disk_info.total) * 100, 2),
                },
                "cpu": {
                    "usage_percent": cpu_percent,
                    "load_average": (
                        os.getloadavg() if hasattr(os, "getloadavg") else None
                    ),
                },
                "process": {
                    "pid": os.getpid(),
                    "threads": psutil.Process().num_threads(),
                },
            }
        except Exception as e:
            system_details = {"error": str(e)}

        # Calculate overall health
        components = {
            "api": "healthy",
            "database": "healthy" if db_details["connected"] else "unhealthy",
            "rag_service": (
                "healthy" if rag_details["status"] == "healthy" else "unhealthy"
            ),
            "agno_agent": (
                "healthy" if agno_details["status"] == "healthy" else "unhealthy"
            ),
        }

        critical_healthy = (
            components["api"] == "healthy" and components["database"] == "healthy"
        )
        all_healthy = all(status == "healthy" for status in components.values())

        if all_healthy:
            overall_status = "healthy"
        elif critical_healthy:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        # Response time calculation
        total_response_time = (datetime.now() - start_time).total_seconds() * 1000

        response_data = {
            "status": overall_status,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT.value,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (
                (datetime.now() - app.state.start_time).total_seconds()
                if hasattr(app.state, "start_time")
                else None
            ),
            "health_check_duration_ms": round(total_response_time, 2),
            "components": components,
            "component_details": {
                "database": db_details,
                "rag_service": rag_details,
                "agno_agent": agno_details,
                "system": system_details,
            },
        }

        # Set status code
        if overall_status == "healthy":
            status_code = status.HTTP_200_OK
        elif overall_status == "degraded":
            status_code = status.HTTP_200_OK
        else:
            status_code = HTTP_503_SERVICE_UNAVAILABLE

        response = JSONResponse(content=response_data, status_code=status_code)

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response

    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(
            "deep_health_check_error",
            error_id=error_id,
            error=str(e),
            exc_info=True,
        )

        response = JSONResponse(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": "Deep health check failed",
                "error_id": error_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response
