# Ali API - Deploy Guide

Este guia fornece instruções completas para fazer deploy da Ali API no Google Cloud Platform (GCP).

## 📋 Pré-requisitos

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) instalado e configurado
- [Docker](https://docs.docker.com/get-docker/) instalado
- Conta no Google Cloud com billing ativado
- Repositório GitHub configurado

## 🚀 Setup Inicial do GCP

### 1. Configurar Projeto GCP

```bash
# Definir variáveis de ambiente
export PROJECT_ID="ali-api-staging"  # Substitua pelo seu project ID
export REGION="us-central1"
export NOTIFICATION_EMAIL="your-email@domain.com"

# Criar novo projeto (opcional)
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Habilitar billing (necessário via Console)
# https://console.cloud.google.com/billing/projects
```

### 2. Executar Setup Automático

```bash
# Tornar o script executável
chmod +x scripts/setup-gcp.sh

# Executar setup do GCP
PROJECT_ID=$PROJECT_ID REGION=$REGION ./scripts/setup-gcp.sh
```

Este script irá:
- Habilitar APIs necessárias
- Criar Artifact Registry
- Configurar Cloud SQL PostgreSQL
- Criar secrets no Secret Manager
- Configurar service account para GitHub Actions
- Gerar chave de service account

### 3. Configurar Secrets no GitHub

Adicione os seguintes secrets no seu repositório GitHub:

1. Vá para `Settings > Secrets and variables > Actions`
2. Adicione os secrets:

```
GCP_PROJECT_ID=ali-api-staging
GCP_SA_KEY=[conteúdo do arquivo github-actions-key.json em base64]
```

Para gerar o GCP_SA_KEY:
```bash
cat github-actions-key.json | base64 -w 0
```

### 4. Configurar API Keys

```bash
# Atualizar LLM API Key
gcloud secrets versions add llm-api-key --data-file=<(echo -n 'sua-openai-api-key-aqui') --project=$PROJECT_ID

# Configurar outros secrets se necessário
gcloud secrets versions add langfuse-public-key --data-file=<(echo -n 'sua-langfuse-public-key') --project=$PROJECT_ID
gcloud secrets versions add langfuse-secret-key --data-file=<(echo -n 'sua-langfuse-secret-key') --project=$PROJECT_ID
```

## 🔄 Deploy Automático

### Deploy para Staging

O deploy para staging é automático quando você faz push para a branch `main`:

```bash
git add .
git commit -m "feat: implementar nova funcionalidade"
git push origin main
```

O GitHub Actions irá:
1. Executar testes
2. Build da imagem Docker
3. Deploy no Cloud Run (staging)
4. Verificar saúde da aplicação

### Deploy para Production

O deploy para produção é manual e requer confirmação:

1. Criar uma tag semântica:
```bash
git tag v1.0.0
git push origin v1.0.0
```

2. Ir para `Actions > Deploy to Production`
3. Inserir a tag (ex: `v1.0.0`)
4. Confirmar digitando `DEPLOY`
5. Executar o workflow

## 📊 Monitoramento e Alertas

### Setup do Monitoramento

```bash
# Configurar monitoramento
chmod +x scripts/setup-monitoring.sh
PROJECT_ID=$PROJECT_ID NOTIFICATION_EMAIL=$NOTIFICATION_EMAIL ./scripts/setup-monitoring.sh
```

Isso criará:
- Dashboard personalizado no Cloud Monitoring
- Alertas para error rate, latência e saúde do banco
- Notificações por email

### Visualizar Logs

```bash
# Logs em tempo real
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=ali-api-staging" --project=$PROJECT_ID

# Logs de erro
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=ali-api-staging AND severity>=ERROR" --limit=50 --project=$PROJECT_ID
```

## 🏥 Health Checks

### Verificar Saúde da Aplicação

```bash
# Staging
curl https://ali-api-staging-[hash]-uc.a.run.app/health

# Production  
curl https://ali-api-production-[hash]-uc.a.run.app/health
```

### Endpoints Disponíveis

- `GET /` - Informações básicas da API
- `GET /health` - Health check detalhado
- `GET /docs` - Documentação Swagger (apenas staging/dev)
- `GET /redoc` - Documentação ReDoc (apenas staging/dev)

## 🔒 Segurança

### Configurações de Produção

- HTTPS obrigatório
- CORS restrito aos domínios do frontend
- API docs desabilitadas
- Rate limiting ativo
- Secrets gerenciados pelo Secret Manager

### Rotação de Secrets

```bash
# Gerar nova JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 64)
gcloud secrets versions add jwt-secret-key --data-file=<(echo -n "$NEW_JWT_SECRET") --project=$PROJECT_ID

# Fazer redeploy para aplicar
gcloud run deploy ali-api-production --region=$REGION --project=$PROJECT_ID
```

## 🐛 Troubleshooting

### Deploy Falhando

1. Verificar logs do Cloud Build:
```bash
gcloud builds list --project=$PROJECT_ID
gcloud builds log [BUILD_ID] --project=$PROJECT_ID
```

2. Verificar configuração do service account:
```bash
gcloud projects get-iam-policy $PROJECT_ID
```

### Aplicação não Responde

1. Verificar logs do Cloud Run:
```bash
gcloud logs read "resource.type=cloud_run_revision" --limit=100 --project=$PROJECT_ID
```

2. Verificar configuração do serviço:
```bash
gcloud run services describe ali-api-staging --region=$REGION --project=$PROJECT_ID
```

### Banco de Dados

1. Verificar conectividade:
```bash
gcloud sql connect ali-postgres --user=ali_user --project=$PROJECT_ID
```

2. Verificar logs do SQL:
```bash
gcloud sql operations list --instance=ali-postgres --project=$PROJECT_ID
```

## 🔄 Rollback

### Rollback Rápido

```bash
# Listar revisões
gcloud run revisions list --service=ali-api-production --region=$REGION --project=$PROJECT_ID

# Fazer rollback para revisão anterior
gcloud run services update-traffic ali-api-production --to-revisions=[REVISION_NAME]=100 --region=$REGION --project=$PROJECT_ID
```

### Rollback via GitHub

1. Revert do commit problemático
2. Push para main (staging) ou criar nova tag (production)

## 📈 Scaling

### Configurar Auto-scaling

```bash
# Configurar instâncias mínimas e máximas
gcloud run services update ali-api-production \
  --min-instances=2 \
  --max-instances=100 \
  --cpu=2 \
  --memory=4Gi \
  --region=$REGION \
  --project=$PROJECT_ID
```

### Monitorar Performance

- Dashboard do Cloud Monitoring
- Alertas configurados para latência > 2s
- Alertas para error rate > 5%

## 🧹 Limpeza

### Remover Recursos (Cuidado!)

```bash
# Deletar serviços Cloud Run
gcloud run services delete ali-api-staging --region=$REGION --project=$PROJECT_ID
gcloud run services delete ali-api-production --region=$REGION --project=$PROJECT_ID

# Deletar instância SQL
gcloud sql instances delete ali-postgres --project=$PROJECT_ID

# Deletar repositório Artifact Registry  
gcloud artifacts repositories delete ali-api-repo --location=$REGION --project=$PROJECT_ID
```

## 📞 Suporte

Para problemas relacionados ao deploy:
1. Verificar logs detalhados nos comandos acima
2. Consultar a documentação do Google Cloud Run
3. Verificar status dos serviços no console GCP

---

**⚠️ Importante**: Sempre teste mudanças em staging antes de fazer deploy para produção!