# 🔧 Troubleshooting - Ali API

## 🚨 Problemas Comuns

### 1. Erro 500 Login
**Causa**: JWT_SECRET_KEY ou Firebase mal configurados
```bash
# Verificar logs
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=20

# Testar endpoint
curl -X POST https://your-api-url/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### 2. Health Check 404
**Causa**: Endpoint não deployado
**Solução**: Redeploy com correções

### 3. Erro 422 Login
**Causa**: Schema inválido
**Formato correto**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "grant_type": "password"
}
```

## 🛠️ Scripts de Diagnóstico

### Diagnóstico Local

```bash
# Executar diagnóstico completo
python diagnose.py

# Setup do ambiente de desenvolvimento
python setup_dev.py
```

### Diagnóstico de Produção

```bash
# Testar API de produção
python fix_production.py
```

## 🔍 Comandos Úteis de Diagnóstico

### Cloud Run

```bash
# Verificar status do serviço
gcloud run services describe ali-api-production --region=us-central1 --project=ali-api-production-459480858531

# Verificar logs em tempo real
gcloud logging tail 'resource.type="cloud_run_revision" AND resource.labels.service_name="ali-api-production"' --project=ali-api-production-459480858531

# Verificar últimas revisões
gcloud run revisions list --service=ali-api-production --region=us-central1 --project=ali-api-production-459480858531

# Verificar variáveis de ambiente
gcloud run services describe ali-api-production --region=us-central1 --project=ali-api-production-459480858531 --format='value(spec.template.spec.template.spec.containers[0].env[])'
```

### Testes de API

```bash
# Testar saúde básica
curl https://ali-api-production-459480858531.us-central1.run.app/api/v1/health

# Testar saúde detalhada (após deploy)
curl https://ali-api-production-459480858531.us-central1.run.app/api/v1/health/detailed

# Testar login
curl -X POST https://ali-api-production-459480858531.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"123456","grant_type":"password"}'
```

## 🔧 Correções Implementadas

### 1. Health Check Melhorado

- ✅ Verificação detalhada de Firebase
- ✅ Verificação de DatabaseService
- ✅ Verificação de variáveis de ambiente
- ✅ Endpoint `/api/v1/health/detailed` adicionado

### 2. Tratamento de Erros Aprimorado

- ✅ Logging detalhado de erros
- ✅ Tratamento específico para cada tipo de erro
- ✅ Respostas de erro padronizadas

### 3. Configuração de Ambiente

- ✅ Arquivo `.env` atualizado
- ✅ Configurações Firebase adicionadas
- ✅ Serviços configurados para desenvolvimento

### 4. Scripts de Diagnóstico

- ✅ `diagnose.py` - Diagnóstico local
- ✅ `setup_dev.py` - Setup de desenvolvimento
- ✅ `fix_production.py` - Diagnóstico de produção

## 📋 Checklist de Deploy

Antes de fazer deploy para produção:

- [ ] Executar `python diagnose.py` localmente
- [ ] Verificar se todas as variáveis de ambiente estão configuradas
- [ ] Testar endpoints críticos localmente
- [ ] Verificar se os logs estão funcionando
- [ ] Confirmar configuração do Firebase
- [ ] Testar JWT token creation

## 🚀 Próximos Passos

### Prioridade Alta

1. **Deploy das Correções**
   - Fazer deploy do código atualizado
   - Verificar se o endpoint `/api/v1/health/detailed` está funcionando
   - Testar o endpoint de login após deploy

2. **Configuração de Variáveis de Ambiente**
   - Verificar se `JWT_SECRET_KEY` está configurado
   - Verificar credenciais do Firebase
   - Configurar variáveis de logging

3. **Monitoramento**
   - Configurar alertas para erros 500
   - Implementar dashboard de métricas
   - Configurar notificações de saúde

### Prioridade Média

1. **Testes Automatizados**
   - Implementar testes de integração
   - Configurar CI/CD com testes
   - Testes de carga

2. **Documentação**
   - Atualizar documentação da API
   - Criar guias de troubleshooting específicos
   - Documentar processo de deploy

## 📞 Suporte

Para problemas não cobertos neste guia:

1. Execute os scripts de diagnóstico
2. Colete logs relevantes
3. Documente os passos para reproduzir o problema
4. Inclua informações do ambiente (desenvolvimento/produção)

## 📚 Recursos Adicionais

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Firebase Documentation](https://firebase.google.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT Documentation](https://jwt.io/)