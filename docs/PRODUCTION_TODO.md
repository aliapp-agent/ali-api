# 📋 Produção Ali API - TODO

## 🔥 CRÍTICO

### 1. Infraestrutura GCP
- [ ] Executar `./scripts/setup-gcp.sh`
- [ ] Configurar billing no projeto GCP
- [ ] Criar Cloud SQL PostgreSQL
- [ ] Configurar Artifact Registry
- [ ] Configurar Cloud Run
- [ ] Configurar Secret Manager

### 2. Secrets
- [ ] GitHub Actions secrets:
  - [ ] `GCP_PROJECT_ID`
  - [ ] `GCP_SERVICE_ACCOUNT_KEY`
  - [ ] `OPENAI_API_KEY`
  - [ ] `LANGFUSE_SECRET_KEY`
- [ ] Google Secret Manager
- [ ] Atualizar `.env` produção

### 3. Banco de Dados
- [ ] Executar migrações Alembic
- [ ] Configurar connection pooling
- [ ] Testar conectividade Cloud SQL
- [ ] Configurar backup automático

### 4. Deploy
- [ ] Testar workflow staging
- [ ] Validar build Docker
- [ ] Deploy Cloud Run
- [ ] Configurar domínio/HTTPS

## ⚡ IMPORTANTE

### 5. Segurança
- [ ] Configurar CORS produção
- [ ] Rate limiting robusto
- [ ] Firewall rules GCP
- [ ] Audit dependências
- [ ] JWT robusta + RBAC

### 6. Monitoramento
- [ ] Alertas Cloud Monitoring
- [ ] Dashboards Grafana
- [ ] Health checks robustos
- [ ] Log aggregation
- [ ] Métricas customizadas

### 7. Performance
- [ ] Auto-scaling Cloud Run
- [ ] Otimizar queries DB
- [ ] Cache Redis
- [ ] Load testing
- [ ] Profiling performance

### 8. Testes
- [ ] Testes unitários
- [ ] Testes integração
- [ ] Testes carga/stress
- [ ] Security scan OWASP

## 🔧 MELHORIAS

### 9. CI/CD
- [ ] Blue-green deployment
- [ ] Rollback automático
- [ ] Canary deployments
- [ ] Feature flags

### 10. Backup/DR
- [ ] Backup automático DB
- [ ] Procedimentos restore
- [ ] Plano disaster recovery
- [ ] Replicação cross-region

## 📊 CHECKLIST PRÉ-DEPLOY

- [ ] Todos testes passando
- [ ] Secrets configurados
- [ ] DB migrado
- [ ] Monitoramento ativo
- [ ] Alertas configurados
- [ ] Backup testado
- [ ] Load testing OK
- [ ] Security scan OK

---

**Status:** 🔴 Não iniciado | 🟡 Em progresso | 🟢 Concluído