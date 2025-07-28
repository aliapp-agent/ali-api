"""Comprehensive dashboard API endpoints.

This module provides system-wide analytics, performance monitoring,
business intelligence, and data visualization capabilities.
"""

from typing import List, Optional
import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    BackgroundTasks,
    status,
)

from app.api.v1.auth import get_current_user
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.user import User
from app.schemas.dashboard import (
    DashboardRequest,
    DashboardResponse,
    SystemOverview,
    UserAnalytics,
    DocumentAnalytics,
    ChatAnalytics,
    SystemPerformance,
    SecurityMetrics,
    FinancialMetrics,
    CustomMetric,
    Alert,
    ChartData,
    ReportRequest,
    ReportResponse,
    ExportRequest,
    ExportResponse,
    TimeRange,
    ChartType,
    MessageResponse,
)
from app.services.dashboard_service import dashboard_service

router = APIRouter()


# ============================================================================
# Main Dashboard Data
# ============================================================================

@router.post("/", response_model=DashboardResponse)
@limiter.limit("30/minute")
async def get_dashboard_data(
    request: Request,
    dashboard_request: DashboardRequest,
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive dashboard data with all analytics.
    
    Args:
        request: FastAPI request object for rate limiting
        dashboard_request: Dashboard data request parameters
        current_user: Authenticated user
        
    Returns:
        DashboardResponse: Complete dashboard data
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        dashboard_data = await dashboard_service.get_dashboard_data(dashboard_request)
        return dashboard_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("dashboard_data_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview", response_model=SystemOverview)
@limiter.limit("60/minute")
async def get_system_overview(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get system overview metrics.
    
    Args:
        request: FastAPI request object for rate limiting
        current_user: Authenticated user
        
    Returns:
        SystemOverview: System overview metrics
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        overview = await dashboard_service._get_system_overview()
        return overview
    except HTTPException:
        raise
    except Exception as e:
        logger.error("system_overview_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Analytics Components
# ============================================================================

@router.get("/analytics/users", response_model=UserAnalytics)
@limiter.limit("60/minute")
async def get_user_analytics(
    request: Request,
    time_range: TimeRange = Query(TimeRange.MONTH, description="Time range for analytics"),
    current_user: User = Depends(get_current_user),
):
    """Get user analytics and engagement metrics.
    
    Args:
        request: FastAPI request object for rate limiting
        time_range: Time range for analytics
        current_user: Authenticated user
        
    Returns:
        UserAnalytics: User analytics metrics
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        analytics = await dashboard_service._get_user_analytics(time_range)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_analytics_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/documents", response_model=DocumentAnalytics)
@limiter.limit("60/minute")
async def get_document_analytics(
    request: Request,
    time_range: TimeRange = Query(TimeRange.MONTH, description="Time range for analytics"),
    current_user: User = Depends(get_current_user),
):
    """Get document analytics and usage metrics.
    
    Args:
        request: FastAPI request object for rate limiting
        time_range: Time range for analytics
        current_user: Authenticated user
        
    Returns:
        DocumentAnalytics: Document analytics metrics
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        analytics = await dashboard_service._get_document_analytics(time_range)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_analytics_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/chat", response_model=ChatAnalytics)
@limiter.limit("60/minute")
async def get_chat_analytics(
    request: Request,
    time_range: TimeRange = Query(TimeRange.MONTH, description="Time range for analytics"),
    current_user: User = Depends(get_current_user),
):
    """Get chat and AI analytics metrics.
    
    Args:
        request: FastAPI request object for rate limiting
        time_range: Time range for analytics
        current_user: Authenticated user
        
    Returns:
        ChatAnalytics: Chat analytics metrics
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        analytics = await dashboard_service._get_chat_analytics(time_range)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error("chat_analytics_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Performance and Security
# ============================================================================

@router.get("/performance", response_model=SystemPerformance)
@limiter.limit("100/minute")
async def get_system_performance(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get system performance metrics.
    
    Args:
        request: FastAPI request object for rate limiting
        current_user: Authenticated user
        
    Returns:
        SystemPerformance: System performance metrics
    """
    try:
        # Check permissions
        if not current_user.has_permission("system:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        performance = await dashboard_service._get_system_performance()
        return performance
    except HTTPException:
        raise
    except Exception as e:
        logger.error("system_performance_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security", response_model=SecurityMetrics)
@limiter.limit("60/minute")
async def get_security_metrics(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get security and audit metrics.
    
    Args:
        request: FastAPI request object for rate limiting
        current_user: Authenticated user
        
    Returns:
        SecurityMetrics: Security metrics
    """
    try:
        # Check permissions - security metrics require admin access
        if not current_user.has_permission("system:admin"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        security = await dashboard_service._get_security_metrics()
        return security
    except HTTPException:
        raise
    except Exception as e:
        logger.error("security_metrics_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial", response_model=FinancialMetrics)
@limiter.limit("30/minute")
async def get_financial_metrics(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get financial and cost metrics.
    
    Args:
        request: FastAPI request object for rate limiting
        current_user: Authenticated user
        
    Returns:
        FinancialMetrics: Financial metrics
    """
    try:
        # Check permissions - financial data requires admin access
        if not current_user.has_permission("analytics:admin"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        financial = await dashboard_service._get_financial_metrics()
        return financial
    except HTTPException:
        raise
    except Exception as e:
        logger.error("financial_metrics_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Custom Metrics and Alerts
# ============================================================================

@router.get("/metrics/custom", response_model=List[CustomMetric])
@limiter.limit("60/minute")
async def get_custom_metrics(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get custom metrics.
    
    Args:
        request: FastAPI request object for rate limiting
        current_user: Authenticated user
        
    Returns:
        List[CustomMetric]: Custom metrics
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        metrics = await dashboard_service._get_custom_metrics()
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error("custom_metrics_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[Alert])
@limiter.limit("100/minute")
async def get_active_alerts(
    request: Request,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    current_user: User = Depends(get_current_user),
):
    """Get active alerts.
    
    Args:
        request: FastAPI request object for rate limiting
        severity: Filter by alert severity
        current_user: Authenticated user
        
    Returns:
        List[Alert]: Active alerts
    """
    try:
        # Check permissions
        if not current_user.has_permission("system:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        alerts = await dashboard_service._get_active_alerts()
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return alerts
    except HTTPException:
        raise
    except Exception as e:
        logger.error("alerts_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge", response_model=MessageResponse)
@limiter.limit("30/minute")
async def acknowledge_alert(
    request: Request,
    alert_id: str,
    current_user: User = Depends(get_current_user),
):
    """Acknowledge an alert.
    
    Args:
        request: FastAPI request object for rate limiting
        alert_id: Alert ID to acknowledge
        current_user: Authenticated user
        
    Returns:
        MessageResponse: Acknowledgment confirmation
    """
    try:
        # Check permissions
        if not current_user.has_permission("system:write"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Mock acknowledgment
        logger.info(
            "alert_acknowledged",
            alert_id=alert_id,
            acknowledged_by=current_user.id
        )
        
        return MessageResponse(
            message="Alert acknowledged successfully",
            success=True,
            data={"alert_id": alert_id, "acknowledged_by": current_user.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("alert_acknowledgment_failed", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Charts and Visualizations
# ============================================================================

@router.get("/charts/{chart_type}", response_model=ChartData)
@limiter.limit("60/minute")
async def get_chart_data(
    request: Request,
    chart_type: str,
    time_range: TimeRange = Query(TimeRange.WEEK, description="Time range for chart"),
    metrics: str = Query(..., description="Comma-separated metrics list"),
    current_user: User = Depends(get_current_user),
):
    """Get chart data for visualization.
    
    Args:
        request: FastAPI request object for rate limiting
        chart_type: Type of chart (line, bar, pie, etc.)
        time_range: Time range for chart data
        metrics: Comma-separated list of metrics
        current_user: Authenticated user
        
    Returns:
        ChartData: Chart data structure
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Validate chart type
        try:
            ChartType(chart_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid chart type: {chart_type}")
        
        metrics_list = [metric.strip() for metric in metrics.split(",")]
        
        chart_data = await dashboard_service.get_chart_data(
            chart_type, time_range, metrics_list
        )
        return chart_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("chart_data_endpoint_failed", chart_type=chart_type, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Reports and Exports
# ============================================================================

@router.post("/reports/generate", response_model=ReportResponse)
@limiter.limit("10/minute")
async def generate_report(
    request: Request,
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Generate analytics report.
    
    Args:
        request: FastAPI request object for rate limiting
        report_request: Report generation parameters
        background_tasks: Background task manager
        current_user: Authenticated user
        
    Returns:
        ReportResponse: Report generation result
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:admin"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Generate report (could be moved to background task for large reports)
        report = await dashboard_service.generate_report(
            report_request.report_type,
            report_request.time_range,
            report_request.format
        )
        
        # Log report generation
        logger.info(
            "report_generated",
            report_id=report.report_id,
            report_type=report_request.report_type,
            user_id=current_user.id
        )
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error("report_generation_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportResponse)
@limiter.limit("10/minute")
async def export_data(
    request: Request,
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user),
):
    """Export analytics data.
    
    Args:
        request: FastAPI request object for rate limiting
        export_request: Export parameters
        current_user: Authenticated user
        
    Returns:
        ExportResponse: Export result
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:admin"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        export = await dashboard_service.export_data(
            export_request.data_type,
            export_request.format,
            export_request.time_range
        )
        
        # Log export
        logger.info(
            "data_exported",
            export_id=export.export_id,
            data_type=export_request.data_type,
            user_id=current_user.id
        )
        
        return export
    except HTTPException:
        raise
    except Exception as e:
        logger.error("data_export_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}/download")
@limiter.limit("30/minute")
async def download_report(
    request: Request,
    report_id: str,
    current_user: User = Depends(get_current_user),
):
    """Download generated report.
    
    Args:
        request: FastAPI request object for rate limiting
        report_id: Report ID
        current_user: Authenticated user
        
    Returns:
        File download response
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Mock download - in real implementation, return actual file
        logger.info("report_downloaded", report_id=report_id, user_id=current_user.id)
        
        return MessageResponse(
            message=f"Report {report_id} download initiated",
            success=True,
            data={"report_id": report_id, "download_url": f"/downloads/reports/{report_id}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("report_download_failed", report_id=report_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exports/{export_id}/download")
@limiter.limit("30/minute")
async def download_export(
    request: Request,
    export_id: str,
    current_user: User = Depends(get_current_user),
):
    """Download exported data.
    
    Args:
        request: FastAPI request object for rate limiting
        export_id: Export ID
        current_user: Authenticated user
        
    Returns:
        File download response
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Mock download - in real implementation, return actual file
        logger.info("export_downloaded", export_id=export_id, user_id=current_user.id)
        
        return MessageResponse(
            message=f"Export {export_id} download initiated",
            success=True,
            data={"export_id": export_id, "download_url": f"/downloads/exports/{export_id}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("export_download_failed", export_id=export_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def dashboard_health():
    """Health check for dashboard service.
    
    Returns:
        dict: Health status
    """
    try:
        # Basic health check
        overview = await dashboard_service._get_system_overview()
        
        return {
            "status": "healthy",
            "total_users": overview.total_users,
            "total_documents": overview.total_documents,
            "api_calls_today": overview.api_calls_today,
            "uptime_hours": overview.uptime_hours,
            "service": "dashboard",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error("dashboard_health_check_failed", error=str(e))
        return {
            "status": "unhealthy", 
            "error": str(e),
            "service": "dashboard",
            "timestamp": time.time()
        }