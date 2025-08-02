"""Dashboard service for comprehensive analytics and metrics.

This service provides system-wide analytics, performance monitoring,
business intelligence, and data visualization capabilities.
"""

import json
import random
import uuid
from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from app.core.config import settings
from app.core.logging import logger
from app.schemas.dashboard import (
    Alert,
    ChartData,
    ChartDataPoint,
    ChartType,
    ChatAnalytics,
    CustomMetric,
    DashboardRequest,
    DashboardResponse,
    DocumentAnalytics,
    ExportResponse,
    FinancialMetrics,
    MetricType,
    ReportResponse,
    SecurityMetrics,
    SystemOverview,
    SystemPerformance,
    TimeRange,
    UserAnalytics,
)
from app.services.documents_service import documents_service
from app.services.users_service import users_service


class DashboardService:
    """Service for comprehensive dashboard analytics and metrics."""

    def __init__(self):
        """Initialize the dashboard service."""
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes default cache

    async def get_dashboard_data(self, request: DashboardRequest) -> DashboardResponse:
        """Get comprehensive dashboard data.

        Args:
            request: Dashboard data request parameters

        Returns:
            DashboardResponse: Complete dashboard data
        """
        try:
            # Check cache first
            cache_key = (
                f"dashboard_{request.time_range.value}_{hash(str(request.dict()))}"
            )
            if not request.refresh_cache and cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if (datetime.utcnow() - cached_time).seconds < self.cache_ttl:
                    logger.info("dashboard_data_served_from_cache", cache_key=cache_key)
                    return cached_data

            # Generate dashboard data
            now = datetime.utcnow()

            # Get all analytics components
            overview = await self._get_system_overview()
            user_analytics = await self._get_user_analytics(request.time_range)
            document_analytics = await self._get_document_analytics(request.time_range)
            chat_analytics = await self._get_chat_analytics(request.time_range)
            performance = await self._get_system_performance()
            security = await self._get_security_metrics()
            financial = await self._get_financial_metrics()
            custom_metrics = await self._get_custom_metrics()
            alerts = await self._get_active_alerts()

            dashboard_data = DashboardResponse(
                overview=overview,
                user_analytics=user_analytics,
                document_analytics=document_analytics,
                chat_analytics=chat_analytics,
                performance=performance,
                security=security,
                financial=financial,
                custom_metrics=custom_metrics,
                alerts=alerts,
                generated_at=now,
                cache_expires_at=now + timedelta(seconds=self.cache_ttl),
            )

            # Cache the result
            self.cache[cache_key] = (dashboard_data, now)

            logger.info(
                "dashboard_data_generated",
                time_range=request.time_range.value,
                components_loaded=8,
                cache_key=cache_key,
            )

            return dashboard_data

        except Exception as e:
            logger.error(
                "dashboard_data_generation_failed",
                time_range=request.time_range.value,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Failed to generate dashboard data: {str(e)}")

    async def _get_system_overview(self) -> SystemOverview:
        """Get system overview metrics."""
        try:
            # Mock data - in real implementation, aggregate from various services
            now = datetime.utcnow()

            return SystemOverview(
                total_users=1247,
                active_users=892,
                total_documents=15673,
                total_chat_sessions=3489,
                total_messages=47829,
                storage_used_gb=156.7,
                api_calls_today=12847,
                uptime_hours=2184.5,  # ~91 days
                health_status="healthy",
                last_updated=now,
            )

        except Exception as e:
            logger.error("system_overview_failed", error=str(e))
            raise

    async def _get_user_analytics(self, time_range: TimeRange) -> UserAnalytics:
        """Get user analytics metrics."""
        try:
            # Generate time-based data points
            days = self._get_days_from_range(time_range)

            # Mock user growth trend
            growth_trend = []
            base_date = datetime.utcnow() - timedelta(days=days)
            for i in range(days):
                date = base_date + timedelta(days=i)
                growth_trend.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "new_users": random.randint(5, 25),
                        "total_users": 1000 + (i * 8),
                        "active_users": random.randint(400, 600),
                    }
                )

            return UserAnalytics(
                new_users_today=18,
                new_users_week=127,
                new_users_month=487,
                active_users_today=423,
                active_users_week=1156,
                active_users_month=2847,
                user_retention_rate=0.78,
                avg_session_duration=24.5,
                top_user_activities=[
                    {"activity": "document_search", "count": 15672, "percentage": 45.2},
                    {
                        "activity": "chat_interaction",
                        "count": 12459,
                        "percentage": 35.9,
                    },
                    {"activity": "document_upload", "count": 4382, "percentage": 12.6},
                    {"activity": "profile_update", "count": 2158, "percentage": 6.2},
                ],
                user_growth_trend=growth_trend,
                geographic_distribution={
                    "Brazil": 892,
                    "United States": 156,
                    "Argentina": 87,
                    "Mexico": 45,
                    "Others": 67,
                },
            )

        except Exception as e:
            logger.error("user_analytics_failed", error=str(e))
            raise

    async def _get_document_analytics(self, time_range: TimeRange) -> DocumentAnalytics:
        """Get document analytics metrics."""
        try:
            # Generate upload activity trend
            days = self._get_days_from_range(time_range)
            upload_activity = []
            base_date = datetime.utcnow() - timedelta(days=days)

            for i in range(days):
                date = base_date + timedelta(days=i)
                upload_activity.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "uploads": random.randint(10, 80),
                        "size_mb": random.randint(50, 500),
                        "categories": random.randint(3, 8),
                    }
                )

            return DocumentAnalytics(
                documents_created_today=67,
                documents_created_week=487,
                documents_created_month=1892,
                total_storage_size=168947256789,  # ~157 GB
                avg_document_size=1247.5,
                most_popular_categories=[
                    {"category": "lei", "count": 4567, "percentage": 29.1},
                    {"category": "decreto", "count": 3421, "percentage": 21.8},
                    {"category": "portaria", "count": 2389, "percentage": 15.2},
                    {"category": "resolucao", "count": 1876, "percentage": 12.0},
                    {"category": "outros", "count": 3420, "percentage": 21.8},
                ],
                document_types_distribution={
                    "pdf": 8945,
                    "docx": 3672,
                    "txt": 2156,
                    "html": 856,
                    "upload": 44,
                },
                search_activity={
                    "total_searches": 25674,
                    "unique_queries": 12458,
                    "avg_results_per_search": 8.4,
                    "zero_result_searches": 1247,
                },
                upload_activity=upload_activity,
                top_contributors=[
                    {"user_id": 1, "name": "João Silva", "documents": 234},
                    {"user_id": 15, "name": "Maria Santos", "documents": 189},
                    {"user_id": 23, "name": "Pedro Costa", "documents": 156},
                    {"user_id": 8, "name": "Ana Oliveira", "documents": 134},
                ],
            )

        except Exception as e:
            logger.error("document_analytics_failed", error=str(e))
            raise

    async def _get_chat_analytics(self, time_range: TimeRange) -> ChatAnalytics:
        """Get chat analytics metrics."""
        try:
            # Generate activity heatmap (24 hours)
            activity_heatmap = []
            for hour in range(24):
                activity_heatmap.append(
                    {
                        "hour": hour,
                        "messages": random.randint(50, 300),
                        "users": random.randint(20, 100),
                    }
                )

            return ChatAnalytics(
                messages_today=1247,
                messages_week=8932,
                messages_month=34567,
                avg_response_time=1.8,
                total_tokens_used=2847569,
                tokens_cost_usd=284.76,
                satisfaction_score=4.2,
                most_common_queries=[
                    {"query": "documentos legislativos", "count": 1567},
                    {"query": "busca por leis", "count": 1234},
                    {"query": "análise de contratos", "count": 987},
                    {"query": "pesquisa jurídica", "count": 876},
                    {"query": "normas municipais", "count": 654},
                ],
                chat_activity_heatmap=activity_heatmap,
                model_performance={
                    "agno-1.0": {
                        "usage_percentage": 85.2,
                        "avg_response_time": 1.6,
                        "satisfaction_score": 4.3,
                        "error_rate": 0.02,
                    },
                    "agno-0.9": {
                        "usage_percentage": 14.8,
                        "avg_response_time": 2.1,
                        "satisfaction_score": 3.9,
                        "error_rate": 0.05,
                    },
                },
            )

        except Exception as e:
            logger.error("chat_analytics_failed", error=str(e))
            raise

    async def _get_system_performance(self) -> SystemPerformance:
        """Get system performance metrics."""
        try:
            return SystemPerformance(
                cpu_usage_percent=random.uniform(15, 45),
                memory_usage_percent=random.uniform(60, 80),
                disk_usage_percent=random.uniform(25, 35),
                network_in_mbps=random.uniform(50, 150),
                network_out_mbps=random.uniform(80, 200),
                database_connections=random.randint(15, 45),
                cache_hit_rate=random.uniform(85, 95),
                average_response_time=random.uniform(120, 280),
                error_rate=random.uniform(0.1, 2.5),
                uptime_percentage=random.uniform(99.5, 99.9),
            )

        except Exception as e:
            logger.error("system_performance_failed", error=str(e))
            raise

    async def _get_security_metrics(self) -> SecurityMetrics:
        """Get security metrics."""
        try:
            return SecurityMetrics(
                failed_login_attempts=random.randint(5, 25),
                successful_logins=random.randint(200, 500),
                suspicious_activities=random.randint(0, 3),
                blocked_ips=random.randint(10, 50),
                security_alerts=[
                    {
                        "id": str(uuid.uuid4()),
                        "type": "suspicious_login",
                        "description": "Multiple failed login attempts",
                        "severity": "medium",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "type": "rate_limit_exceeded",
                        "description": "Rate limit exceeded for IP",
                        "severity": "low",
                        "timestamp": (
                            datetime.utcnow() - timedelta(hours=2)
                        ).isoformat(),
                    },
                ],
                password_strength_distribution={
                    "weak": 45,
                    "medium": 156,
                    "strong": 789,
                    "very_strong": 257,
                },
                two_factor_adoption=0.68,
                last_security_scan=datetime.utcnow() - timedelta(hours=6),
            )

        except Exception as e:
            logger.error("security_metrics_failed", error=str(e))
            raise

    async def _get_financial_metrics(self) -> FinancialMetrics:
        """Get financial metrics."""
        try:
            # Generate cost trend
            cost_trend = []
            for i in range(6):  # Last 6 months
                date = datetime.utcnow() - timedelta(days=30 * i)
                cost_trend.append(
                    {
                        "month": date.strftime("%Y-%m"),
                        "total_cost": random.uniform(800, 1200),
                        "api_costs": random.uniform(200, 400),
                        "storage_costs": random.uniform(150, 250),
                        "compute_costs": random.uniform(400, 600),
                    }
                )

            return FinancialMetrics(
                monthly_api_costs=324.67,
                storage_costs=189.45,
                compute_costs=567.89,
                total_monthly_cost=1082.01,
                cost_per_user=0.87,
                cost_per_document=0.069,
                cost_trend=cost_trend,
                budget_utilization=0.72,
            )

        except Exception as e:
            logger.error("financial_metrics_failed", error=str(e))
            raise

    async def _get_custom_metrics(self) -> List[CustomMetric]:
        """Get custom metrics."""
        try:
            now = datetime.utcnow()

            return [
                CustomMetric(
                    id="user_satisfaction",
                    name="User Satisfaction Score",
                    description="Average user satisfaction rating",
                    type=MetricType.GAUGE,
                    value=4.2,
                    unit="stars",
                    timestamp=now,
                    tags={"source": "feedback", "category": "user_experience"},
                ),
                CustomMetric(
                    id="document_processing_rate",
                    name="Document Processing Rate",
                    description="Documents processed per minute",
                    type=MetricType.GAUGE,
                    value=15.7,
                    unit="docs/min",
                    timestamp=now,
                    tags={"source": "processing", "category": "performance"},
                ),
                CustomMetric(
                    id="search_success_rate",
                    name="Search Success Rate",
                    description="Percentage of searches returning results",
                    type=MetricType.GAUGE,
                    value=95.1,
                    unit="percent",
                    timestamp=now,
                    tags={"source": "search", "category": "effectiveness"},
                ),
            ]

        except Exception as e:
            logger.error("custom_metrics_failed", error=str(e))
            raise

    async def _get_active_alerts(self) -> List[Alert]:
        """Get active alerts."""
        try:
            now = datetime.utcnow()

            return [
                Alert(
                    id=str(uuid.uuid4()),
                    rule_id="high_cpu_usage",
                    rule_name="High CPU Usage",
                    message="CPU usage is above 80% for more than 5 minutes",
                    severity="warning",
                    status="active",
                    metric_value=82.5,
                    threshold=80.0,
                    triggered_at=now - timedelta(minutes=3),
                    resolved_at=None,
                    acknowledged_by=None,
                    acknowledged_at=None,
                ),
                Alert(
                    id=str(uuid.uuid4()),
                    rule_id="low_disk_space",
                    rule_name="Low Disk Space",
                    message="Disk usage is above 90%",
                    severity="critical",
                    status="active",
                    metric_value=92.1,
                    threshold=90.0,
                    triggered_at=now - timedelta(hours=1),
                    resolved_at=None,
                    acknowledged_by=None,
                    acknowledged_at=None,
                ),
            ]

        except Exception as e:
            logger.error("active_alerts_failed", error=str(e))
            raise

    async def get_chart_data(
        self, chart_type: str, time_range: TimeRange, metrics: List[str]
    ) -> ChartData:
        """Get chart data for visualization.

        Args:
            chart_type: Type of chart to generate
            time_range: Time range for data
            metrics: List of metrics to include

        Returns:
            ChartData: Chart data structure
        """
        try:
            days = self._get_days_from_range(time_range)
            base_date = datetime.utcnow() - timedelta(days=days)

            # Generate data points
            data_points = []
            for i in range(days):
                date = base_date + timedelta(days=i)
                value = random.uniform(100, 1000) + (i * 10)  # Trending upward

                data_points.append(
                    ChartDataPoint(
                        timestamp=date,
                        value=value,
                        label=date.strftime("%Y-%m-%d"),
                        metadata={"day_of_week": date.strftime("%A")},
                    )
                )

            return ChartData(
                title=f"{', '.join(metrics)} Over Time",
                chart_type=ChartType(chart_type),
                x_axis_label="Date",
                y_axis_label="Value",
                data_points=data_points,
                series=[
                    {
                        "name": metric,
                        "data": [
                            dp.value + random.uniform(-50, 50) for dp in data_points
                        ],
                    }
                    for metric in metrics
                ],
                config={
                    "responsive": True,
                    "legend": {"position": "top"},
                    "colors": ["#007bff", "#28a745", "#ffc107", "#dc3545"],
                },
            )

        except Exception as e:
            logger.error(
                "chart_data_generation_failed",
                chart_type=chart_type,
                metrics=metrics,
                error=str(e),
            )
            raise Exception(f"Failed to generate chart data: {str(e)}")

    async def generate_report(
        self, report_type: str, time_range: TimeRange, format: str = "pdf"
    ) -> ReportResponse:
        """Generate analytics report.

        Args:
            report_type: Type of report to generate
            time_range: Time range for report
            format: Report format

        Returns:
            ReportResponse: Report generation result
        """
        try:
            report_id = str(uuid.uuid4())
            now = datetime.utcnow()

            # Mock report generation
            report_size = random.randint(500000, 2000000)  # 500KB - 2MB

            logger.info(
                "report_generated",
                report_id=report_id,
                report_type=report_type,
                time_range=time_range.value,
                format=format,
                size=report_size,
            )

            return ReportResponse(
                report_id=report_id,
                report_url=f"/api/v1/dashboard/reports/{report_id}/download",
                report_size=report_size,
                generated_at=now,
                expires_at=now + timedelta(days=7),
                status="completed",
            )

        except Exception as e:
            logger.error(
                "report_generation_failed", report_type=report_type, error=str(e)
            )
            raise Exception(f"Failed to generate report: {str(e)}")

    async def export_data(
        self,
        data_type: str,
        format: str = "json",
        time_range: TimeRange = TimeRange.MONTH,
    ) -> ExportResponse:
        """Export analytics data.

        Args:
            data_type: Type of data to export
            format: Export format
            time_range: Time range for export

        Returns:
            ExportResponse: Export result
        """
        try:
            export_id = str(uuid.uuid4())
            now = datetime.utcnow()

            # Mock export
            record_count = random.randint(1000, 50000)
            file_size = record_count * random.randint(100, 500)

            logger.info(
                "data_exported",
                export_id=export_id,
                data_type=data_type,
                format=format,
                record_count=record_count,
                file_size=file_size,
            )

            return ExportResponse(
                export_id=export_id,
                download_url=f"/api/v1/dashboard/exports/{export_id}/download",
                file_size=file_size,
                record_count=record_count,
                format=format,
                generated_at=now,
                expires_at=now + timedelta(days=3),
            )

        except Exception as e:
            logger.error("data_export_failed", data_type=data_type, error=str(e))
            raise Exception(f"Failed to export data: {str(e)}")

    def _get_days_from_range(self, time_range: TimeRange) -> int:
        """Get number of days from time range enum."""
        range_map = {
            TimeRange.HOUR: 1,
            TimeRange.DAY: 1,
            TimeRange.WEEK: 7,
            TimeRange.MONTH: 30,
            TimeRange.QUARTER: 90,
            TimeRange.YEAR: 365,
        }
        return range_map.get(time_range, 30)


# Create global instance
dashboard_service = DashboardService()
