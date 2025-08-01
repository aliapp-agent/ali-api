"""This file contains the main application entry point."""

import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.shared.constants.http import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
    SECURITY_HEADERS,
)
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.core.metrics import setup_metrics
from app.core.middleware import MetricsMiddleware
from app.shared.exceptions import (
    APIError,
    AuthenticationError,
    DatabaseError,
    ValidationError,
)
from app.services.database import database_service

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Set startup time for health check uptime calculation
    app.state.start_time = datetime.now()

    logger.info(
        "application_startup",
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        api_prefix=settings.API_V1_STR,
        startup_time=app.state.start_time.isoformat(),
    )
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up Prometheus metrics
setup_metrics(app)

# Add custom metrics middleware
app.add_middleware(MetricsMiddleware)

# Set up rate limiter exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Handle validation errors from request data.

    Args:
        request: The request that caused the validation error
        exc: The validation error

    Returns:
        JSONResponse: A formatted error response
    """
    error_id = str(uuid.uuid4())

    # Log the validation error
    logger.error(
        "validation_error",
        error_id=error_id,
        client_host=request.client.host if request.client else "unknown",
        path=request.url.path,
        method=request.method,
        errors=str(exc.errors()),
    )

    # Format the errors to be more user-friendly
    formatted_errors = []
    for error in exc.errors():
        loc = " -> ".join(
            [str(loc_part) for loc_part in error["loc"] if loc_part != "body"]
        )
        formatted_errors.append(
            {
                "field": loc,
                "message": error["msg"],
                "type": error.get("type", "validation_error"),
            }
        )

    response = JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": {
                "errors": formatted_errors,
                "error_id": error_id,
            },
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )

    # Add security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


@app.exception_handler(APIError)
async def api_exception_handler(request: Request, exc: APIError):
    """Handle custom API exceptions.

    Args:
        request: The request that caused the error
        exc: The API exception

    Returns:
        JSONResponse: A formatted error response
    """
    error_id = str(uuid.uuid4())

    logger.error(
        "api_error",
        error_id=error_id,
        error_type=type(exc).__name__,
        message=str(exc),
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
        client_host=request.client.host if request.client else "unknown",
    )

    response_data = {
        "error": type(exc).__name__,
        "message": str(exc),
        "status_code": exc.status_code,
        "error_id": error_id,
        "timestamp": datetime.now().isoformat(),
        "path": request.url.path,
    }

    if exc.details:
        response_data["details"] = exc.details

    response = JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )

    # Add security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(
    request: Request, exc: AuthenticationError
):
    """Handle authentication errors.

    Args:
        request: The request that caused the error
        exc: The authentication exception

    Returns:
        JSONResponse: A formatted error response
    """
    error_id = str(uuid.uuid4())

    logger.warning(
        "authentication_error",
        error_id=error_id,
        error_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        client_host=request.client.host if request.client else "unknown",
    )

    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "AuthenticationError",
            "message": str(exc),
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Add security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors.

    Args:
        request: The request that caused the error
        exc: The database exception

    Returns:
        JSONResponse: A formatted error response
    """
    error_id = str(uuid.uuid4())

    logger.error(
        "database_error",
        error_id=error_id,
        error_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        client_host=request.client.host if request.client else "unknown",
        exc_info=True,
    )

    response = JSONResponse(
        status_code=HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "DatabaseError",
            "message": "A database error occurred. Please try again later.",
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )

    # Add security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle custom validation errors.

    Args:
        request: The request that caused the error
        exc: The validation exception

    Returns:
        JSONResponse: A formatted error response
    """
    error_id = str(uuid.uuid4())

    logger.warning(
        "custom_validation_error",
        error_id=error_id,
        error_type=type(exc).__name__,
        message=str(exc),
        field=getattr(exc, "field", None),
        path=request.url.path,
        method=request.method,
        client_host=request.client.host if request.client else "unknown",
    )

    response_data = {
        "error": "ValidationError",
        "message": str(exc),
        "error_id": error_id,
        "timestamp": datetime.now().isoformat(),
        "path": request.url.path,
    }

    if hasattr(exc, "field") and exc.field:
        response_data["field"] = exc.field

    if hasattr(exc, "value") and exc.value is not None:
        response_data["value"] = str(exc.value)

    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
    )

    # Add security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions.

    Args:
        request: The request that caused the error
        exc: The HTTP exception

    Returns:
        JSONResponse: A formatted error response
    """
    error_id = str(uuid.uuid4())

    logger.warning(
        "http_exception",
        error_id=error_id,
        status_code=exc.status_code,
        detail=str(exc.detail),
        path=request.url.path,
        method=request.method,
        client_host=request.client.host if request.client else "unknown",
    )

    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )

    # Add security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions.

    Args:
        request: The request that caused the error
        exc: The unexpected exception

    Returns:
        JSONResponse: A formatted error response
    """
    error_id = str(uuid.uuid4())

    logger.error(
        "unexpected_error",
        error_id=error_id,
        error_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        client_host=request.client.host if request.client else "unknown",
        traceback=traceback.format_exc(),
        exc_info=True,
    )

    # Don't expose internal error details in production
    if settings.APP_ENV.value == "production":
        message = "An internal server error occurred. Please try again later."
    else:
        message = f"Internal server error: {str(exc)}"

    response = JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": message,
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )

    # Add security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-API-Key",
        "Cache-Control"
    ],
    expose_headers=["X-Total-Count", "X-Rate-Limit-Remaining"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Import deep health check endpoints
from app import deep_health  # noqa: E402, F401


@app.get("/")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["root"][0])
async def root(request: Request):
    """Root endpoint returning basic API information."""
    logger.info("root_endpoint_called")
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "environment": settings.APP_ENV.value,
        "swagger_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["health"][0])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint with environment-specific information.

    Returns:
        JSONResponse: Health status information
    """
    logger.info("health_check_called")

    try:
        # Check database connectivity
        db_healthy = await database_service.health_check()

        # Check RAG service health
        rag_health = {}
        try:
            from app.services.rag import rag_service
            rag_health = await rag_service.health_check()
            rag_healthy = rag_health.get("status") == "healthy"
        except Exception as e:
            logger.warning("rag_health_check_failed", error=str(e))
            rag_healthy = False
            rag_health = {"status": "unhealthy", "error": str(e)}

        # Check Agno agent health (if available)
        agno_healthy = True
        agno_health = {}
        try:
            from app.core.agno.graph import AgnoAgent
            agent = AgnoAgent()
            agno_health = await agent.health_check()
            agno_healthy = agno_health.get("status") == "healthy"
        except Exception as e:
            logger.warning("agno_health_check_failed", error=str(e))
            agno_healthy = False
            agno_health = {"status": "unhealthy", "error": str(e)}

        # Detailed component status
        components = {
            "api": "healthy",
            "database": "healthy" if db_healthy else "unhealthy",
            "rag_service": "healthy" if rag_healthy else "unhealthy",
            "agno_agent": "healthy" if agno_healthy else "unhealthy",
        }

        # Add detailed component information
        component_details = {
            "database": {"connected": db_healthy},
            "rag_service": rag_health,
            "agno_agent": agno_health,
        }

        # Calculate overall health status
        critical_components = ["api", "database"]

        critical_healthy = all(
            components[comp] == "healthy" for comp in critical_components
        )
        all_healthy = all(status == "healthy" for status in components.values())

        if all_healthy:
            overall_status = "healthy"
        elif critical_healthy:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        response_data = {
            "status": overall_status,
            "version": settings.VERSION,
            "environment": settings.APP_ENV.value,
            "components": components,
            "component_details": component_details,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - app.state.start_time).total_seconds() if hasattr(app.state, 'start_time') else None,
        }

        # Set appropriate status code based on health
        if overall_status == "healthy":
            status_code = status.HTTP_200_OK
        elif overall_status == "degraded":
            status_code = status.HTTP_200_OK  # Still functional, just degraded
        else:  # unhealthy
            status_code = HTTP_503_SERVICE_UNAVAILABLE

        response = JSONResponse(content=response_data, status_code=status_code)

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response

    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(
            "health_check_error",
            error_id=error_id,
            error=str(e),
            exc_info=True,
        )

        response = JSONResponse(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": "Health check failed",
                "error_id": error_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response
