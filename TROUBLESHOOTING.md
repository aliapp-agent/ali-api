# 🔧 Guia de Troubleshooting - Ali API

Este documento contém soluções para os problemas mais comuns encontrados no Ali API.

## 🚨 Problemas Críticos Identificados

### 1. Erro 500 no Endpoint de Login

**Sintoma**: `/api/v1/auth/login` retorna erro 500 Internal Server Error

**Possíveis Causas**:
- Variáveis de ambiente não configuradas
- Problemas de conexão com Firebase/Firestore
- JWT_SECRET_KEY não definido
- Credenciais do Firebase inválidas

**Soluções**:

```bash
# 1. Verificar variáveis de ambiente
gcloud run services describe ali-api-production --region=us-central1 --project=ali-api-production-459480858531 --format='value(spec.template.spec.template.spec.containers[0].env[].name)'

# 2. Verificar logs de erro
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="ali-api-production" AND severity>=ERROR' --limit=20 --project=ali-api-production-459480858531

# 3. Testar endpoint localmente
curl -X POST https://ali-api-production-459480858531.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  -v
```

### 2. Endpoint de Saúde Detalhado (404)

**Sintoma**: `/api/v1/health/detailed` retorna 404 Not Found

**Causa**: Endpoint não foi deployado para produção

**Solução**: Fazer novo deploy com as correções implementadas

### 3. Erro 422 no Login

**Sintoma**: Todas as tentativas de login retornam 422 Unprocessable Entity

**Causa**: Validação de schema falhando

**Solução**: Verificar se o payload está no formato correto:

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

- ✅ Arquivo `.env.development` atualizado
- ✅ Configurações Firebase adicionadas
- ✅ Mock services para desenvolvimento

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