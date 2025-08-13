#!/bin/bash
# Ali API - Script de Deploy em Produção na GCP
# =============================================================================

set -e  # Exit on any error

echo "🚀 Ali API - Deploy em Produção na GCP"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se gcloud está instalado e autenticado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI não está instalado!${NC}"
    echo "Instale com: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Verificar se está autenticado
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Error: Não está autenticado no gcloud!${NC}"
    echo "Execute: gcloud auth login"
    exit 1
fi

# Verificar se o projeto está configurado
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: Projeto GCP não configurado!${NC}"
    echo "Execute: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${BLUE}📋 Projeto GCP: ${PROJECT_ID}${NC}"
echo ""

# ==========================================
# PRÉ-REQUISITOS E VERIFICAÇÕES
# ==========================================

echo -e "${YELLOW}🔧 Verificando pré-requisitos...${NC}"

# Habilitar APIs necessárias
echo -e "${BLUE}Habilitando APIs necessárias...${NC}"
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet
gcloud services enable artifactregistry.googleapis.com --quiet
gcloud services enable secretmanager.googleapis.com --quiet

echo -e "${GREEN}✅ APIs habilitadas${NC}"

# Verificar se o repositório do Artifact Registry existe
REPO_EXISTS=$(gcloud artifacts repositories list --location=us-central1 --filter="name:ali-api-repo" --format="value(name)" || true)

if [ -z "$REPO_EXISTS" ]; then
    echo -e "${YELLOW}📦 Criando repositório no Artifact Registry...${NC}"
    gcloud artifacts repositories create ali-api-repo \
        --repository-format=docker \
        --location=us-central1 \
        --description="Ali API Docker Repository"
    echo -e "${GREEN}✅ Repositório criado${NC}"
else
    echo -e "${GREEN}✅ Repositório Artifact Registry já existe${NC}"
fi

# Configurar autenticação Docker
echo -e "${BLUE}🔐 Configurando autenticação Docker...${NC}"
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Verificar secrets
echo -e "${YELLOW}🔍 Verificando secrets...${NC}"
REQUIRED_SECRETS=("ali-jwt-secret-key" "ali-llm-api-key" "ali-qdrant-api-key" "ali-firebase-credentials" "ali-langfuse-secret-key" "ali-elasticsearch-api-key")
MISSING_SECRETS=()

for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! gcloud secrets describe "$secret" --quiet 2>/dev/null; then
        MISSING_SECRETS+=("$secret")
    fi
done

if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Secrets em falta: ${MISSING_SECRETS[*]}${NC}"
    echo -e "${YELLOW}💡 Execute primeiro: ./scripts/create-gcp-secrets.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Todos os secrets estão configurados${NC}"

# ==========================================
# DEPLOY
# ==========================================

echo ""
echo -e "${YELLOW}🚀 Iniciando deploy...${NC}"
echo ""

# Executar Cloud Build
echo -e "${BLUE}Building e fazendo deploy via Cloud Build...${NC}"
echo -e "${BLUE}Isso pode demorar alguns minutos...${NC}"
echo ""

gcloud builds submit --config=cloudbuild.yaml

# ==========================================
# PÓS-DEPLOY
# ==========================================

echo ""
echo -e "${GREEN}🎉 Deploy concluído!${NC}"
echo ""

# Obter URL do serviço
SERVICE_URL=$(gcloud run services describe ali-api-production \
    --region=us-central1 \
    --format="value(status.url)" 2>/dev/null || echo "N/A")

echo -e "${YELLOW}📋 Informações do Deploy:${NC}"
echo "   🌍 Service URL: $SERVICE_URL"
echo "   📊 Region: us-central1"
echo "   🏷️  Service Name: ali-api-production"
echo ""

# Testar health check
if [ "$SERVICE_URL" != "N/A" ]; then
    echo -e "${BLUE}🔍 Testando health check...${NC}"
    
    if curl -s -f "$SERVICE_URL/api/v1/health" > /dev/null; then
        echo -e "${GREEN}✅ Health check passou!${NC}"
        echo -e "${GREEN}✅ API está funcionando corretamente${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check falhou - verifique os logs${NC}"
    fi
    echo ""
fi

echo -e "${YELLOW}💡 Próximos passos:${NC}"
echo "   1. Testar a API: curl $SERVICE_URL/api/v1/health"
echo "   2. Verificar logs: gcloud logs read --limit=50 --format=json"
echo "   3. Monitorar: https://console.cloud.google.com/run"
echo ""

echo -e "${YELLOW}📚 Endpoints disponíveis:${NC}"
echo "   • Health: GET $SERVICE_URL/api/v1/health"
echo "   • Auth: POST $SERVICE_URL/api/v1/auth/register"
echo "   • Chat: POST $SERVICE_URL/api/v1/chatbot/chat"
echo "   • Documents: GET $SERVICE_URL/api/v1/documents"
echo ""

echo -e "${GREEN}🎉 Ali API está rodando em produção na GCP!${NC}"