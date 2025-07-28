#!/bin/bash

# Setup GCP for Ali API
# This script sets up the necessary GCP resources for staging and production

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-ali-api-staging}"
REGION="${REGION:-us-central1}"
SERVICE_NAME_STAGING="ali-api-staging"
SERVICE_NAME_PRODUCTION="ali-api-production"
ARTIFACT_REPO="ali-api-repo"
DB_INSTANCE_NAME="ali-postgres"

echo "🚀 Setting up GCP resources for Ali API"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  sql-component.googleapis.com \
  secretmanager.googleapis.com \
  cloudmonitoring.googleapis.com \
  logging.googleapis.com \
  --project=$PROJECT_ID

# Create Artifact Registry repository
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create $ARTIFACT_REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="Ali API Docker images" \
  --project=$PROJECT_ID || echo "Repository may already exist"

# Create Cloud SQL instance
echo "🗄️ Creating Cloud SQL PostgreSQL instance..."
gcloud sql instances create $DB_INSTANCE_NAME \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --project=$PROJECT_ID || echo "Instance may already exist"

# Create database
echo "📋 Creating database..."
gcloud sql databases create ali_db \
  --instance=$DB_INSTANCE_NAME \
  --project=$PROJECT_ID || echo "Database may already exist"

# Create database user
echo "👤 Creating database user..."
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create ali_user \
  --instance=$DB_INSTANCE_NAME \
  --password=$DB_PASSWORD \
  --project=$PROJECT_ID || echo "User may already exist"

# Get database connection string
DB_CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE_NAME --format="value(connectionName)" --project=$PROJECT_ID)
POSTGRES_URL="postgresql://ali_user:$DB_PASSWORD@/$DB_INSTANCE_NAME?host=/cloudsql/$DB_CONNECTION_NAME"

echo "📝 Creating secrets..."

# Create secrets
gcloud secrets create postgres-url-staging --data-file=<(echo -n "$POSTGRES_URL") --project=$PROJECT_ID || echo "Secret may already exist"

# Generate JWT secret
JWT_SECRET=$(openssl rand -base64 64)
gcloud secrets create jwt-secret-key --data-file=<(echo -n "$JWT_SECRET") --project=$PROJECT_ID || echo "Secret may already exist"

# Create placeholder for LLM API key (to be set manually)
gcloud secrets create llm-api-key --data-file=<(echo -n "REPLACE_WITH_ACTUAL_API_KEY") --project=$PROJECT_ID || echo "Secret may already exist"

# Create service account for GitHub Actions
echo "🔑 Creating service account for GitHub Actions..."
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account" \
  --description="Service account for GitHub Actions CI/CD" \
  --project=$PROJECT_ID || echo "Service account may already exist"

# Grant necessary permissions
echo "🛡️ Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Generate service account key
echo "🗝️ Generating service account key..."
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com \
  --project=$PROJECT_ID

echo ""
echo "✅ GCP setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Add the following secrets to your GitHub repository:"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - GCP_SA_KEY: $(cat github-actions-key.json | base64 -w 0)"
echo ""
echo "2. Update your LLM API key:"
echo "   gcloud secrets versions add llm-api-key --data-file=<(echo -n 'YOUR_ACTUAL_API_KEY') --project=$PROJECT_ID"
echo ""
echo "3. Database connection string (for reference):"
echo "   $POSTGRES_URL"
echo ""
echo "4. Clean up the service account key file:"
echo "   rm github-actions-key.json"
echo ""
echo "🎉 Ready to deploy! Push to main branch to trigger staging deployment."