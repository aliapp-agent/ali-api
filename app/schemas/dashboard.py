"""Dashboard and analytics schemas for the API.

This module provides schemas for comprehensive system analytics, metrics,
monitoring, and dashboard data visualization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TimeRange(str, Enum):
    """Time range enumeration for analytics."""
    HOUR = "1h"
    DAY = "1d"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"


class ChartType(str, Enum):
    """Chart type enumeration."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class DashboardWidget(BaseModel):
    """Dashboard widget configuration."""
    
    id: str = Field(..., description="Widget ID")
    title: str = Field(..., description="Widget title")
    type: str = Field(..., description="Widget type")
    chart_type: ChartType = Field(..., description="Chart type")
    position: Dict[str, int] = Field(..., description="Widget position and size")
    data_source: str = Field(..., description="Data source endpoint")
    config: Dict[str, Any] = Field(default_factory=dict, description="Widget configuration")
    refresh_interval: int = Field(300, description="Refresh interval in seconds")
    is_visible: bool = Field(True, description="Widget visibility")


class SystemOverview(BaseModel):
    """System overview metrics."""
    
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    total_documents: int = Field(..., description="Total number of documents")
    total_chat_sessions: int = Field(..., description="Total chat sessions")
    total_messages: int = Field(..., description="Total chat messages")
    storage_used_gb: float = Field(..., description="Storage used in GB")
    api_calls_today: int = Field(..., description="API calls today")
    uptime_hours: float = Field(..., description="System uptime in hours")
    health_status: str = Field(..., description="Overall health status")
    last_updated: datetime = Field(..., description="Last update timestamp")


class UserAnalytics(BaseModel):
    """User analytics and engagement metrics."""
    
    new_users_today: int = Field(..., description="New users today")
    new_users_week: int = Field(..., description="New users this week")
    new_users_month: int = Field(..., description="New users this month")
    active_users_today: int = Field(..., description="Active users today")
    active_users_week: int = Field(..., description="Active users this week")
    active_users_month: int = Field(..., description="Active users this month")
    user_retention_rate: float = Field(..., description="User retention rate")
    avg_session_duration: float = Field(..., description="Average session duration in minutes")
    top_user_activities: List[Dict[str, Any]] = Field(..., description="Top user activities")
    user_growth_trend: List[Dict[str, Any]] = Field(..., description="User growth trend")
    geographic_distribution: Dict[str, int] = Field(..., description="Users by location")


class DocumentAnalytics(BaseModel):
    """Document analytics and usage metrics."""
    
    documents_created_today: int = Field(..., description="Documents created today")
    documents_created_week: int = Field(..., description="Documents created this week")
    documents_created_month: int = Field(..., description="Documents created this month")
    total_storage_size: int = Field(..., description="Total storage size in bytes")
    avg_document_size: float = Field(..., description="Average document size in KB")
    most_popular_categories: List[Dict[str, Any]] = Field(..., description="Most popular categories")
    document_types_distribution: Dict[str, int] = Field(..., description="Document types distribution")
    search_activity: Dict[str, int] = Field(..., description="Search activity metrics")
    upload_activity: List[Dict[str, Any]] = Field(..., description="Upload activity trend")
    top_contributors: List[Dict[str, Any]] = Field(..., description="Top document contributors")


class ChatAnalytics(BaseModel):
    """Chat and AI analytics metrics."""
    
    messages_today: int = Field(..., description="Messages today")
    messages_week: int = Field(..., description="Messages this week")
    messages_month: int = Field(..., description="Messages this month")
    avg_response_time: float = Field(..., description="Average AI response time in seconds")
    total_tokens_used: int = Field(..., description="Total tokens consumed")
    tokens_cost_usd: float = Field(..., description="Estimated cost in USD")
    satisfaction_score: float = Field(..., description="User satisfaction score")
    most_common_queries: List[Dict[str, Any]] = Field(..., description="Most common queries")
    chat_activity_heatmap: List[Dict[str, Any]] = Field(..., description="Chat activity by hour")
    model_performance: Dict[str, Any] = Field(..., description="AI model performance metrics")


class SystemPerformance(BaseModel):
    """System performance and infrastructure metrics."""
    
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")
    network_in_mbps: float = Field(..., description="Network input in Mbps")
    network_out_mbps: float = Field(..., description="Network output in Mbps")
    database_connections: int = Field(..., description="Active database connections")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    average_response_time: float = Field(..., description="Average API response time in ms")
    error_rate: float = Field(..., description="Error rate percentage")
    uptime_percentage: float = Field(..., description="System uptime percentage")


class SecurityMetrics(BaseModel):
    """Security and audit metrics."""
    
    failed_login_attempts: int = Field(..., description="Failed login attempts today")
    successful_logins: int = Field(..., description="Successful logins today")
    suspicious_activities: int = Field(..., description="Suspicious activities detected")
    blocked_ips: int = Field(..., description="Number of blocked IP addresses")
    security_alerts: List[Dict[str, Any]] = Field(..., description="Recent security alerts")
    password_strength_distribution: Dict[str, int] = Field(..., description="Password strength levels")
    two_factor_adoption: float = Field(..., description="Two-factor authentication adoption rate")
    last_security_scan: datetime = Field(..., description="Last security scan timestamp")


class FinancialMetrics(BaseModel):
    """Financial and cost metrics."""
    
    monthly_api_costs: float = Field(..., description="Monthly API costs in USD")
    storage_costs: float = Field(..., description="Storage costs in USD")
    compute_costs: float = Field(..., description="Compute costs in USD")
    total_monthly_cost: float = Field(..., description="Total monthly cost in USD")
    cost_per_user: float = Field(..., description="Cost per active user")
    cost_per_document: float = Field(..., description="Cost per document")
    cost_trend: List[Dict[str, Any]] = Field(..., description="Cost trend over time")
    budget_utilization: float = Field(..., description="Budget utilization percentage")


class CustomMetric(BaseModel):
    """Custom metric definition."""
    
    id: str = Field(..., description="Metric ID")
    name: str = Field(..., description="Metric name")
    description: str = Field(..., description="Metric description")
    type: MetricType = Field(..., description="Metric type")
    value: float = Field(..., description="Current metric value")
    unit: str = Field(..., description="Metric unit")
    timestamp: datetime = Field(..., description="Metric timestamp")
    tags: Dict[str, str] = Field(default_factory=dict, description="Metric tags")


class AlertRule(BaseModel):
    """Alert rule configuration."""
    
    id: str = Field(..., description="Alert rule ID")
    name: str = Field(..., description="Alert rule name")
    description: str = Field(..., description="Alert rule description")
    metric: str = Field(..., description="Metric to monitor")
    condition: str = Field(..., description="Alert condition")
    threshold: float = Field(..., description="Alert threshold")
    severity: str = Field(..., description="Alert severity")
    is_enabled: bool = Field(True, description="Whether alert is enabled")
    notification_channels: List[str] = Field(..., description="Notification channels")
    created_by: int = Field(..., description="User who created the alert")
    created_at: datetime = Field(..., description="Creation timestamp")


class Alert(BaseModel):
    """Alert instance."""
    
    id: str = Field(..., description="Alert ID")
    rule_id: str = Field(..., description="Alert rule ID")
    rule_name: str = Field(..., description="Alert rule name")
    message: str = Field(..., description="Alert message")
    severity: str = Field(..., description="Alert severity")
    status: str = Field(..., description="Alert status")
    metric_value: float = Field(..., description="Metric value that triggered alert")
    threshold: float = Field(..., description="Alert threshold")
    triggered_at: datetime = Field(..., description="Alert trigger timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Alert resolution timestamp")
    acknowledged_by: Optional[int] = Field(None, description="User who acknowledged alert")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")


class DashboardRequest(BaseModel):
    """Dashboard data request parameters."""
    
    time_range: TimeRange = Field(TimeRange.DAY, description="Time range for data")
    include_predictions: bool = Field(False, description="Include predictive analytics")
    include_comparisons: bool = Field(True, description="Include period comparisons")
    refresh_cache: bool = Field(False, description="Force refresh cached data")
    widgets: Optional[List[str]] = Field(None, description="Specific widgets to load")


class DashboardResponse(BaseModel):
    """Comprehensive dashboard response."""
    
    overview: SystemOverview = Field(..., description="System overview")
    user_analytics: UserAnalytics = Field(..., description="User analytics")
    document_analytics: DocumentAnalytics = Field(..., description="Document analytics")
    chat_analytics: ChatAnalytics = Field(..., description="Chat analytics")
    performance: SystemPerformance = Field(..., description="System performance")
    security: SecurityMetrics = Field(..., description="Security metrics")
    financial: FinancialMetrics = Field(..., description="Financial metrics")
    custom_metrics: List[CustomMetric] = Field(..., description="Custom metrics")
    alerts: List[Alert] = Field(..., description="Active alerts")
    generated_at: datetime = Field(..., description="Response generation timestamp")
    cache_expires_at: datetime = Field(..., description="Cache expiration timestamp")


class ChartDataPoint(BaseModel):
    """Chart data point."""
    
    timestamp: datetime = Field(..., description="Data point timestamp")
    value: float = Field(..., description="Data point value")
    label: Optional[str] = Field(None, description="Data point label")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChartData(BaseModel):
    """Chart data structure."""
    
    title: str = Field(..., description="Chart title")
    chart_type: ChartType = Field(..., description="Chart type")
    x_axis_label: str = Field(..., description="X-axis label")
    y_axis_label: str = Field(..., description="Y-axis label")
    data_points: List[ChartDataPoint] = Field(..., description="Chart data points")
    series: Optional[List[Dict[str, Any]]] = Field(None, description="Multiple data series")
    config: Dict[str, Any] = Field(default_factory=dict, description="Chart configuration")


class ReportRequest(BaseModel):
    """Report generation request."""
    
    report_type: str = Field(..., description="Type of report")
    time_range: TimeRange = Field(..., description="Report time range")
    format: str = Field("pdf", description="Report format (pdf, csv, xlsx)")
    include_charts: bool = Field(True, description="Include charts in report")
    recipients: List[str] = Field(default_factory=list, description="Report recipients")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Report filters")


class ReportResponse(BaseModel):
    """Report generation response."""
    
    report_id: str = Field(..., description="Generated report ID")
    report_url: str = Field(..., description="Report download URL")
    report_size: int = Field(..., description="Report size in bytes")
    generated_at: datetime = Field(..., description="Generation timestamp")
    expires_at: datetime = Field(..., description="Report expiration")
    status: str = Field(..., description="Report generation status")


class ExportRequest(BaseModel):
    """Data export request."""
    
    data_type: str = Field(..., description="Type of data to export")
    format: str = Field("json", description="Export format")
    time_range: TimeRange = Field(..., description="Export time range")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Export filters")
    include_metadata: bool = Field(True, description="Include metadata")


class ExportResponse(BaseModel):
    """Data export response."""
    
    export_id: str = Field(..., description="Export ID")
    download_url: str = Field(..., description="Download URL")
    file_size: int = Field(..., description="File size in bytes")
    record_count: int = Field(..., description="Number of exported records")
    format: str = Field(..., description="Export format")
    generated_at: datetime = Field(..., description="Export timestamp")
    expires_at: datetime = Field(..., description="Download expiration")


class MessageResponse(BaseModel):
    """Generic response schema for simple operations."""
    
    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")