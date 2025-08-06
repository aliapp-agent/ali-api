# 🚀 Deploy Ali API na GCP com Secrets Manager

Este guia te ajuda a fazer o deploy da Ali API na Google Cloud Platform usando o Secret Manager para máxima segurança.

## 🎯 Pré-requisitos

### 1. Conta e Projeto GCP
- ✅ Conta Google Cloud ativa
- ✅ Projeto GCP criado
- ✅ Billing account configurada

### 2. gcloud CLI
```bash
# Instalar gcloud CLI
# Siga: https://cloud.google.com/sdk/docs/install

# Autenticar
gcloud auth login

# Configurar projeto
gcloud config set project SEU_PROJECT_ID
```

## 🔐 Passo 1: Criar Secrets no Secret Manager

Execute os comandos abaixo para criar todos os secrets necessários:

```bash
# Habilitar Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Criar secrets (substitua pelos seus valores reais)
echo "S6rT2c1N3GsrXFUEOyB62dyz7LEd-0AG5r02CcHgbkRopYI0QI53o37HXF2SwpOyytin2iv7xKOcXE35rx_njw" | \
gcloud secrets create ali-jwt-secret-key --data-file=-

echo "sk-proj-SEU_OPENAI_API_KEY" | \
gcloud secrets create ali-llm-api-key --data-file=-

echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.yFsc6gtKzD5n2dalsPp6dvY8Cz9raMbkGUarmM0VbdM" | \
gcloud secrets create ali-qdrant-api-key --data-file=-

# Firebase credentials (arquivo completo)
gcloud secrets create ali-firebase-credentials --data-file=./firebase-credentials.json

# Observabilidade Langfuse (opcional)
echo "sk_lf_YOUR_LANGFUSE_SECRET_KEY" | \
gcloud secrets create ali-langfuse-secret-key --data-file=-

# Elasticsearch API Key (opcional)
echo "YOUR_ELASTICSEARCH_API_KEY" | \
gcloud secrets create ali-elasticsearch-api-key --data-file=-
```

### OU use o script automatizado:
```bash
./scripts/create-gcp-secrets.sh
```

## 🏗️ Passo 2: Configurar Infraestrutura

```bash
# Habilitar APIs necessárias
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Criar repositório no Artifact Registry
gcloud artifacts repositories create ali-api-repo \
  --repository-format=docker \
  --location=us-central1

# Configurar autenticação Docker
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## 🚀 Passo 3: Deploy

Execute o deploy:

```bash
# Opção 1: Script automatizado (RECOMENDADO)
./scripts/deploy-production.sh

# Opção 2: Cloud Build manual
gcloud builds submit --config=cloudbuild.yaml
```

## ✅ Verificação Pós-Deploy

### 1. Verificar Service
```bash
gcloud run services describe ali-api-production --region=us-central1
```

### 2. Testar Health Check
```bash
SERVICE_URL=$(gcloud run services describe ali-api-production --region=us-central1 --format="value(status.url)")
curl $SERVICE_URL/api/v1/health
```

### 3. Ver Logs
```bash
gcloud logs read "resource.type=cloud_run_revision" --limit=50
```

## 🔧 Configurações do Deploy

### Secrets Manager (Dados Sensíveis)
- ✅ `ali-jwt-secret-key` - Chave JWT
- ✅ `ali-llm-api-key` - API Key OpenAI
- ✅ `ali-qdrant-api-key` - API Key Qdrant
- ✅ `ali-firebase-credentials` - Credenciais Firebase
- ✅ `ali-langfuse-secret-key` - Chave Langfuse (observabilidade)
- ✅ `ali-elasticsearch-api-key` - Chave Elasticsearch (busca)

### Environment Variables (Dados Públicos)
- ✅ APP_ENV=production
- ✅ DEBUG=false
- ✅ CORS configurado para produção
- ✅ Rate limiting otimizado
- ✅ Logs em formato JSON

### Recursos do Cloud Run
- 🚀 **CPU**: 2 vCPUs
- 🚀 **Memory**: 2Gi
- 🚀 **Max Instances**: 10
- 🚀 **Min Instances**: 1
- 🚀 **Timeout**: 900s
- 🚀 **Port**: 8080

## 📊 Endpoints Disponíveis

Após o deploy, os seguintes endpoints estarão disponíveis:

```
# Health Check
GET https://YOUR-SERVICE-URL/api/v1/health

# Autenticação
POST https://YOUR-SERVICE-URL/api/v1/auth/register
POST https://YOUR-SERVICE-URL/api/v1/auth/login

# Chat AI
POST https://YOUR-SERVICE-URL/api/v1/chatbot/chat
POST https://YOUR-SERVICE-URL/api/v1/chatbot/stream

# Documentos
GET https://YOUR-SERVICE-URL/api/v1/documents
```

## 🔍 Monitoramento

### Logs
```bash
# Logs em tempo real
gcloud logs tail "resource.type=cloud_run_revision"

# Logs específicos
gcloud logs read --limit=100 --format=json
```

### Métricas
- 📊 [Cloud Run Console](https://console.cloud.google.com/run)
- 📊 [Cloud Monitoring](https://console.cloud.google.com/monitoring)
- 📊 [Error Reporting](https://console.cloud.google.com/errors)

## 🚨 Troubleshooting

### Build Falhando
```bash
# Verificar Dockerfile
docker build -t test-build .

# Verificar logs do Cloud Build
gcloud builds log BUILD_ID
```

### Deploy Falhando
```bash
# Verificar secrets
gcloud secrets list --filter="labels.app=ali-api"

# Verificar permissões
gcloud projects get-iam-policy PROJECT_ID
```

### Runtime Errors
```bash
# Logs detalhados
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR"

# Testar localmente
docker run -p 8080:8080 --env-file .env IMAGE_NAME
```

## 🔄 Updates e Redeploys

Para atualizar a aplicação:

```bash
# Commit suas mudanças
git add .
git commit -m "Update: nova funcionalidade"

# Redeploy
gcloud builds submit --config=cloudbuild.yaml
```

## 🛡️ Segurança

### ✅ Implementado
- 🔐 Todos os secrets no Secret Manager
- 🔐 HTTPS obrigatório
- 🔐 CORS configurado
- 🔐 Rate limiting ativo
- 🔐 JWT authentication
- 🔐 Environment de produção

### 🚨 Importante
- ⚠️ Nunca commitar secrets no código
- ⚠️ Revisar logs regularmente
- ⚠️ Monitorar custos
- ⚠️ Backup das configurações

## 💰 Custos Estimados

**Recursos principais:**
- Cloud Run: ~$10-50/mês (dependendo do tráfego)
- Secret Manager: ~$0.06/secret/mês
- Artifact Registry: ~$0.10/GB/mês
- Cloud Build: $0.003/build-minute

**Total estimado: $15-70/mês** (varia com o uso)

---

## 🎉 Pronto!

Sua Ali API agora está rodando em produção na GCP com máxima segurança! 

🌍 **URL da API**: `https://ali-api-production-HASH-uc.a.run.app`

Para suporte, consulte os logs ou abra uma issue no repositório.