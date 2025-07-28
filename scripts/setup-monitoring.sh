#!/bin/bash

# Setup GCP Monitoring and Alerting for Ali API
# This script creates dashboards, alert policies, and notification channels

set -e

PROJECT_ID="${PROJECT_ID:-ali-api-staging}"
REGION="${REGION:-us-central1}"
SERVICE_NAME_STAGING="ali-api-staging"
SERVICE_NAME_PRODUCTION="ali-api-production"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-alerts@your-domain.com}"

echo "🔔 Setting up monitoring and alerting for Ali API"
echo "Project ID: $PROJECT_ID"

# Create notification channel for email alerts
echo "📧 Creating email notification channel..."
gcloud alpha monitoring channels create \
  --display-name="Ali API Email Alerts" \
  --type=email \
  --channel-labels=email_address=$NOTIFICATION_EMAIL \
  --project=$PROJECT_ID || echo "Notification channel may already exist"

# Get the notification channel ID
NOTIFICATION_CHANNEL_ID=$(gcloud alpha monitoring channels list \
  --filter="displayName='Ali API Email Alerts'" \
  --format="value(name)" \
  --project=$PROJECT_ID)

echo "📊 Creating uptime checks..."

# Create uptime check for staging
cat > uptime-check-staging.json << EOF
{
  "displayName": "Ali API Staging Uptime",
  "monitoredResource": {
    "type": "uptime_url",
    "labels": {}
  },
  "httpCheck": {
    "path": "/health",
    "port": 443,
    "useSsl": true,
    "validateSsl": true
  },
  "timeout": "10s",
  "period": "300s",
  "contentMatchers": [
    {
      "content": "healthy",
      "matcher": "CONTAINS_STRING"
    }
  ]
}
EOF

# Create uptime check for production
cat > uptime-check-production.json << EOF
{
  "displayName": "Ali API Production Uptime", 
  "monitoredResource": {
    "type": "uptime_url",
    "labels": {}
  },
  "httpCheck": {
    "path": "/health",
    "port": 443,
    "useSsl": true,
    "validateSsl": true
  },
  "timeout": "10s",
  "period": "60s",
  "contentMatchers": [
    {
      "content": "healthy",
      "matcher": "CONTAINS_STRING"
    }
  ]
}
EOF

echo "🚨 Creating alert policies..."

# High error rate alert
cat > alert-policy-error-rate.json << EOF
{
  "displayName": "Ali API High Error Rate",
  "documentation": {
    "content": "Alert when error rate exceeds 5% for more than 5 minutes",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "High 5xx error rate",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=~\"ali-api.*\" AND metric.type=\"run.googleapis.com/request_count\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_SUM",
            "groupByFields": ["resource.labels.service_name"]
          }
        ],
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.05,
        "duration": "300s",
        "evaluationMissingData": "EVALUATION_MISSING_DATA_INACTIVE"
      }
    }
  ],
  "notificationChannels": ["$NOTIFICATION_CHANNEL_ID"],
  "alertStrategy": {
    "autoClose": "86400s"
  },
  "combiner": "OR",
  "enabled": true
}
EOF

# High latency alert  
cat > alert-policy-latency.json << EOF
{
  "displayName": "Ali API High Latency",
  "documentation": {
    "content": "Alert when 95th percentile latency exceeds 2 seconds",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "High request latency",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=~\"ali-api.*\" AND metric.type=\"run.googleapis.com/request_latencies\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_DELTA",
            "crossSeriesReducer": "REDUCE_PERCENTILE_95",
            "groupByFields": ["resource.labels.service_name"]
          }
        ],
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 2000,
        "duration": "300s"
      }
    }
  ],
  "notificationChannels": ["$NOTIFICATION_CHANNEL_ID"],
  "alertStrategy": {
    "autoClose": "86400s"
  },
  "combiner": "OR",
  "enabled": true
}
EOF

# Database connectivity alert
cat > alert-policy-db-health.json << EOF
{
  "displayName": "Ali API Database Health",
  "documentation": {
    "content": "Alert when database health checks fail",
    "mimeType": "text/markdown"  
  },
  "conditions": [
    {
      "displayName": "Database connection failures",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=~\"ali-api.*\" AND metric.type=\"logging.googleapis.com/user/database_error\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_SUM"
          }
        ],
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.1,
        "duration": "300s"
      }
    }
  ],
  "notificationChannels": ["$NOTIFICATION_CHANNEL_ID"],
  "combiner": "OR",
  "enabled": true
}
EOF

# Apply alert policies
gcloud alpha monitoring policies create --policy-from-file=alert-policy-error-rate.json --project=$PROJECT_ID
gcloud alpha monitoring policies create --policy-from-file=alert-policy-latency.json --project=$PROJECT_ID  
gcloud alpha monitoring policies create --policy-from-file=alert-policy-db-health.json --project=$PROJECT_ID

echo "📈 Creating custom dashboard..."

cat > dashboard.json << EOF
{
  "displayName": "Ali API Dashboard",
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Count",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=~\"ali-api.*\" AND metric.type=\"run.googleapis.com/request_count\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_RATE",
                      "crossSeriesReducer": "REDUCE_SUM",
                      "groupByFields": ["resource.labels.service_name"]
                    }
                  }
                },
                "plotType": "LINE"
              }
            ],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Requests/sec",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 6,
        "widget": {
          "title": "Response Latency (95th percentile)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=~\"ali-api.*\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                    "aggregation": {
                      "alignmentPeriod": "300s", 
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_PERCENTILE_95",
                      "groupByFields": ["resource.labels.service_name"]
                    }
                  }
                },
                "plotType": "LINE"
              }
            ],
            "yAxis": {
              "label": "Latency (ms)",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "yPos": 4,
        "widget": {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=~\"ali-api.*\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_RATE", 
                      "crossSeriesReducer": "REDUCE_SUM",
                      "groupByFields": ["resource.labels.service_name"]
                    }
                  }
                },
                "plotType": "LINE"
              }
            ],
            "yAxis": {
              "label": "Errors/sec",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "width": 6, 
        "height": 4,
        "xPos": 6,
        "yPos": 4,
        "widget": {
          "title": "CPU Utilization",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=~\"ali-api.*\" AND metric.type=\"run.googleapis.com/cpu/utilizations\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN",
                      "groupByFields": ["resource.labels.service_name"]
                    }
                  }
                },
                "plotType": "LINE"
              }
            ],
            "yAxis": {
              "label": "CPU %",
              "scale": "LINEAR" 
            }
          }
        }
      }
    ]
  }
}
EOF

gcloud monitoring dashboards create --config-from-file=dashboard.json --project=$PROJECT_ID

# Clean up temporary files
rm -f uptime-check-*.json alert-policy-*.json dashboard.json

echo ""
echo "✅ Monitoring setup completed!"
echo ""
echo "📋 Created resources:"
echo "- Email notification channel: Ali API Email Alerts"
echo "- Alert policies: High Error Rate, High Latency, Database Health"  
echo "- Custom dashboard: Ali API Dashboard"
echo ""
echo "🔗 View your monitoring dashboard:"
echo "https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
echo ""
echo "📧 Alerts will be sent to: $NOTIFICATION_EMAIL"