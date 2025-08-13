#!/bin/bash
# Ali API - Script para criar secrets no GCP Secret Manager
# =============================================================================

set -e  # Exit on any error

echo "🔐 Ali API - Criando Secrets no GCP Secret Manager"
echo "=================================================="

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

# Habilitar Secret Manager API se necessário
echo -e "${YELLOW}🔧 Verificando APIs necessárias...${NC}"
gcloud services enable secretmanager.googleapis.com --quiet

echo -e "${GREEN}✅ Secret Manager API habilitado${NC}"
echo ""

# Função para criar secret
create_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    echo -e "${BLUE}Creating secret: ${secret_name}${NC}"
    
    # Verificar se o secret já existe
    if gcloud secrets describe "$secret_name" --quiet 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Secret $secret_name já existe. Criando nova versão...${NC}"
        echo "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
    else
        echo -e "${GREEN}📝 Criando novo secret: $secret_name${NC}"
        echo "$secret_value" | gcloud secrets create "$secret_name" \
            --replication-policy="automatic" \
            --data-file=- \
            --labels="app=ali-api,env=production"
    fi
    
    echo -e "${GREEN}✅ Secret $secret_name criado/atualizado com sucesso${NC}"
    echo ""
}

# ==========================================
# CRIANDO TODOS OS SECRETS
# ==========================================

echo -e "${YELLOW}🚀 Iniciando criação dos secrets...${NC}"
echo ""

# 1. JWT Secret Key
JWT_SECRET_KEY="S6rT2c1N3GsrXFUEOyB62dyz7LEd-0AG5r02CcHgbkRopYI0QI53o37HXF2SwpOyytin2iv7xKOcXE35rx_njw"
create_secret "ali-jwt-secret-key" "$JWT_SECRET_KEY" "JWT Secret Key for Ali API"

# 2. LLM API Key (OpenAI)
LLM_API_KEY="change-apikey-here"
create_secret "ali-llm-api-key" "$LLM_API_KEY" "OpenAI API Key for Ali API"

# 3. Qdrant API Key
QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.yFsc6gtKzD5n2dalsPp6dvY8Cz9raMbkGUarmM0VbdM"
create_secret "ali-qdrant-api-key" "$QDRANT_API_KEY" "Qdrant Vector DB API Key for Ali API"

# 4. Firebase Credentials (conteúdo completo do arquivo)
if [ -f "../firebase-credentials.json" ]; then
    echo -e "${BLUE}Creating secret: ali-firebase-credentials${NC}"
    gcloud secrets create "ali-firebase-credentials" \
        --replication-policy="automatic" \
        --data-file="../firebase-credentials.json" \
        --labels="app=ali-api,env=production" || \
    gcloud secrets versions add "ali-firebase-credentials" \
        --data-file="../firebase-credentials.json"
    echo -e "${GREEN}✅ Firebase credentials secret criado/atualizado${NC}"
    echo ""
else
    echo -e "${RED}❌ Arquivo firebase-credentials.json não encontrado!${NC}"
    echo "   Certifique-se de que o arquivo existe no diretório pai"
fi

# 5. Langfuse Secret Key (Observabilidade - opcional)
LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY:-"your-langfuse-secret-key"}
if [ "$LANGFUSE_SECRET_KEY" != "your-langfuse-secret-key" ]; then
    create_secret "ali-langfuse-secret-key" "$LANGFUSE_SECRET_KEY" "Langfuse Secret Key for Ali API observability"
else
    echo -e "${YELLOW}⚠️  LANGFUSE_SECRET_KEY não configurada. Usando valor padrão.${NC}"
    echo -e "${YELLOW}   Configure com: export LANGFUSE_SECRET_KEY='sua_chave_langfuse'${NC}"
    create_secret "ali-langfuse-secret-key" "$LANGFUSE_SECRET_KEY" "Langfuse Secret Key for Ali API observability"
fi

# 6. Elasticsearch API Key (Busca - opcional)
ELASTICSEARCH_API_KEY=${ELASTICSEARCH_API_KEY:-"your-elasticsearch-api-key"}
if [ "$ELASTICSEARCH_API_KEY" != "your-elasticsearch-api-key" ]; then
    create_secret "ali-elasticsearch-api-key" "$ELASTICSEARCH_API_KEY" "Elasticsearch API Key for Ali API search"
else
    echo -e "${YELLOW}⚠️  ELASTICSEARCH_API_KEY não configurada. Usando valor padrão.${NC}"
    echo -e "${YELLOW}   Configure com: export ELASTICSEARCH_API_KEY='sua_chave_elastic'${NC}"
    create_secret "ali-elasticsearch-api-key" "$ELASTICSEARCH_API_KEY" "Elasticsearch API Key for Ali API search"
fi

# ==========================================
# VERIFICAÇÃO DOS SECRETS CRIADOS
# ==========================================

echo -e "${YELLOW}🔍 Verificando secrets criados...${NC}"
echo ""

SECRETS=("ali-jwt-secret-key" "ali-llm-api-key" "ali-qdrant-api-key" "ali-firebase-credentials" "ali-langfuse-secret-key" "ali-elasticsearch-api-key")

for secret in "${SECRETS[@]}"; do
    if gcloud secrets describe "$secret" --quiet 2>/dev/null; then
        echo -e "${GREEN}✅ $secret - OK${NC}"
    else
        echo -e "${RED}❌ $secret - FALHOU${NC}"
    fi
done

echo ""
echo -e "${GREEN}🎉 Processo de criação de secrets concluído!${NC}"
echo ""
echo -e "${YELLOW}💡 Próximos passos:${NC}"
echo "   1. Verificar se todos os secrets foram criados"
echo "   2. Atualizar cloudbuild.yaml para usar os secrets"
echo "   3. Fazer deploy com: gcloud builds submit --config=cloudbuild.yaml"
echo ""
echo -e "${BLUE}📋 Para verificar os secrets criados:${NC}"
echo "   gcloud secrets list --filter='labels.app=ali-api'"
echo ""