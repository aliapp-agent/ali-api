# Ali API

API FastAPI com integração LLM e WhatsApp para chatbot inteligente.

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

- **[Arquitetura](./docs/ARCHITECTURE.md)** - Visão geral do sistema
- **[Deploy](./docs/DEPLOY.md)** - Guia de deployment GCP
- **[Integração Frontend](./docs/FRONTEND_INTEGRATION.md)** - Como integrar frontend
- **[TODO Produção](./docs/PRODUCTION_TODO.md)** - Tarefas críticas para deploy

## 🛠️ Desenvolvimento

```bash
# Executar com hot reload
uv run uvicorn app.main:app --reload

# Executar testes
uv run pytest

# Verificar saúde
curl http://localhost:8000/health
```

## 📋 Funcionalidades

- ✅ FastAPI com LangGraph/Agno
- ✅ Autenticação JWT + PostgreSQL
- ✅ Chat streaming com OpenAI
- ✅ **Integração WhatsApp**
- ✅ Observabilidade Langfuse
- ✅ Rate limiting e métricas
- ✅ Docker e CI/CD

## 📱 WhatsApp

```bash
# Configurar WhatsApp
python scripts/setup_whatsapp.py

# Testar integração
python scripts/test_whatsapp.py --full-test
```

## 🔗 Endpoints

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

**v1.0.0** | **MIT**