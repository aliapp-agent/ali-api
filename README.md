# Ali API

Uma API FastAPI robusta e pronta para produção com integração Agno e Langfuse.

## 🚀 Início Rápido

```bash
# Instalar dependências
uv sync

# Configurar ambiente
cp .env.example .env

# Executar aplicação
uv run python -m app.main
```

## 📚 Documentação

Toda a documentação detalhada está disponível na pasta [`docs/`](./docs/):

- **[Arquitetura](./docs/ARCHITECTURE.md)** - Visão geral da arquitetura do sistema
- **[Deploy](./docs/DEPLOY.md)** - Guia de deployment e configuração
- **[Integração Frontend](./docs/FRONTEND_INTEGRATION.md)** - Como integrar com frontend
- **[TODO Produção](./docs/PRODUCTION_TODO.md)** - Lista de tarefas críticas para deploy

## 🛠️ Desenvolvimento

```bash
# Executar testes
uv run pytest

# Executar com hot reload
uv run uvicorn app.main:app --reload

# Verificar saúde da aplicação
curl http://localhost:8000/health
```

## 📋 Funcionalidades

- ✅ FastAPI com documentação automática
- ✅ Integração com Agno para agentes de IA
- ✅ Sistema RAG com Elasticsearch
- ✅ Observabilidade com Langfuse
- ✅ Autenticação JWT
- ✅ Rate limiting
- ✅ Métricas e monitoramento
- ✅ Testes automatizados
- ✅ Docker e CI/CD

## 🔗 Links Úteis

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

**Versão**: 1.0.0 | **Licença**: MIT