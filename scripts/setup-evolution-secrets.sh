#!/bin/bash

# Script para configurar secrets da Evolution API no Google Cloud Secret Manager
# Execute este script após configurar suas credenciais do gcloud

set -e

echo "🔐 Configurando secrets da Evolution API..."

# Verificar se o gcloud está configurado
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI não encontrado. Instale o Google Cloud SDK primeiro."
    exit 1
fi

# Verificar se o projeto está configurado
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Projeto do Google Cloud não configurado. Execute: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Projeto atual: $PROJECT_ID"

# Função para criar secret
create_secret() {
    local secret_name=$1
    local secret_value=$2
    
    echo "🔑 Criando secret: $secret_name"
    
    # Verificar se o secret já existe
    if gcloud secrets describe "$secret_name" &>/dev/null; then
        echo "⚠️  Secret $secret_name já existe. Atualizando..."
        echo -n "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
    else
        echo "➕ Criando novo secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets create "$secret_name" --data-file=-
    fi
    
    echo "✅ Secret $secret_name configurado com sucesso"
}

# Solicitar informações da Evolution API
echo ""
echo "📝 Por favor, forneça as informações da sua Evolution API:"
echo ""

read -p "🌐 URL da Evolution API (ex: https://api.evolution.com): " EVOLUTION_API_URL
read -p "🏷️  Nome da instância (ex: my-instance): " EVOLUTION_INSTANCE
read -s -p "🔐 API Key da Evolution API: " EVOLUTION_API_KEY
echo ""

# Validar inputs
if [ -z "$EVOLUTION_API_URL" ] || [ -z "$EVOLUTION_INSTANCE" ] || [ -z "$EVOLUTION_API_KEY" ]; then
    echo "❌ Todos os campos são obrigatórios!"
    exit 1
fi

# Validar URL
if [[ ! "$EVOLUTION_API_URL" =~ ^https?:// ]]; then
    echo "❌ URL deve começar com http:// ou https://"
    exit 1
fi

echo ""
echo "🚀 Criando secrets no Google Cloud Secret Manager..."
echo ""

# Criar os secrets
create_secret "ali-evolution-api-key" "$EVOLUTION_API_KEY"

echo ""
echo "✅ Todos os secrets da Evolution API foram configurados com sucesso!"
echo ""
echo "📋 Resumo dos secrets criados:"
echo "   - ali-evolution-api-key: ✅ Configurado"
echo ""
echo "⚙️  Próximos passos:"
echo "   1. Atualize o cloudbuild.yaml com os valores corretos:"
echo "      _EVOLUTION_API_URL: '$EVOLUTION_API_URL'"
echo "      _EVOLUTION_INSTANCE: '$EVOLUTION_INSTANCE'"
echo "   2. Execute o deploy: gcloud builds submit --config=cloudbuild.yaml"
echo ""
echo "🎉 Configuração concluída!"