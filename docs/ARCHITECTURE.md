# Ali API - Documentação Arquitetural

## Visão Geral

A Ali API é uma **aplicação de chatbot inteligente** construída com FastAPI que integra modelos de linguagem (LLM) para conversas naturais. A aplicação oferece funcionalidades completas de autenticação, gerenciamento de sessões, e processamento de chat com persistência de histórico.

### Stack Tecnológico

- **FastAPI** - Framework web moderno e rápido
- **LangGraph/Agno** - Orquestração de workflows de LLM
- **PostgreSQL** - Banco de dados relacional
- **OpenAI GPT** - Modelo de linguagem
- **Langfuse** - Observabilidade e monitoramento de LLM
- **Docker** - Containerização
- **Prometheus/Grafana** - Métricas e dashboards
- **SQLModel** - ORM baseado em Pydantic

## Estrutura de Diretórios

```
ali-api/
├── app/
│   ├── api/v1/                    # Endpoints da API v1
│   │   ├── api.py                 # Router principal
│   │   ├── auth.py                # Autenticação e sessões
│   │   └── chatbot.py             # Endpoints de chat
│   ├── core/                      # Componentes centrais
│   │   ├── agno/                  # Implementação Agno (experimental)
│   │   ├── langgraph/             # Implementação LangGraph
│   │   ├── config.py              # Configurações da aplicação
│   │   ├── logging.py             # Sistema de logging
│   │   ├── metrics.py             # Métricas Prometheus
│   │   ├── middleware.py          # Middlewares customizados
│   │   └── limiter.py             # Rate limiting
│   ├── models/                    # Modelos SQLModel
│   ├── schemas/                   # Schemas Pydantic
│   ├── services/                  # Serviços de negócio
│   ├── utils/                     # Utilitários
│   └── main.py                    # Ponto de entrada
├── evals/                         # Sistema de avaliação
├── grafana/                       # Dashboards Grafana
├── prometheus/                    # Configuração Prometheus
├── scripts/                       # Scripts de deployment
├── docker-compose.yml             # Orquestração de containers
├── Dockerfile                     # Build da aplicação
├── pyproject.toml                 # Dependências e configuração
└── schema.sql                     # Schema do banco de dados
```

## Componentes Principais

### 1. Aplicação Principal (main.py)

O ponto de entrada da aplicação configura:

- **FastAPI app** com metadados
- **Middlewares**:
  - CORS para cross-origin requests
  - MetricsMiddleware para Prometheus
  - Rate limiting global
- **Exception handlers** para validação e errors
- **Lifespan events** para startup/shutdown
- **Health checks** com verificação de banco

```python
# Fluxo de inicialização:
1. Carrega configurações de ambiente
2. Inicializa Langfuse para observabilidade
3. Configura middlewares e rate limiting
4. Registra exception handlers
5. Inclui routers da API v1
```

### 2. Sistema de Configuração (config.py)

Sistema inteligente que:

- **Detecta ambiente automaticamente**: development/staging/production/test
- **Carrega arquivos .env** em ordem de prioridade
- **Aplica configurações específicas** por ambiente
- **Gerencia variáveis sensíveis** de forma segura

```python
# Hierarquia de arquivos .env:
1. .env.{environment}.local
2. .env.{environment}
3. .env.local
4. .env

# Configurações por ambiente:
Development: Debug ativo, rate limits relaxados, logging verbose
Production: Debug off, rate limits rígidos, logging minimal
Test: Configurações otimizadas para testes
```

### 3. Autenticação e Autorização (auth.py)

Sistema completo de autenticação com:

#### Endpoints:
- `POST /register` - Registro de novos usuários
- `POST /login` - Autenticação com JWT
- `POST /session` - Criação de sessões de chat
- `GET /sessions` - Listagem de sessões do usuário
- `PATCH /session/{id}/name` - Renomeação de sessões
- `DELETE /session/{id}` - Exclusão de sessões

#### Funcionalidades de Segurança:
- **Hashing de senhas** com bcrypt
- **JWT tokens** para autenticação stateless
- **Validação de força** de senhas
- **Sanitização de inputs** contra injection attacks
- **Rate limiting** específico por endpoint
- **Verificação de ownership** para operações de sessão

### 4. Sistema de Chat (chatbot.py)

Core da funcionalidade de conversação:

#### Endpoints:
- `POST /chat` - Chat tradicional (resposta completa)
- `POST /chat/stream` - Chat com streaming (tokens em tempo real)
- `GET /messages` - Recuperação de histórico
- `DELETE /messages` - Limpeza de histórico

#### Funcionalidades:
- **Integração com LangGraph Agent** para processamento
- **Streaming de respostas** via Server-Sent Events
- **Persistência de conversas** por sessão
- **Métricas de performance** para monitoramento
- **Tratamento de erros** robusto com logging

### 5. LangGraph Agent (langgraph/graph.py)

Orquestrador principal do workflow de LLM:

#### Arquitetura do Graph:
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Chat      │    │  Conditional │    │   Tool      │
│   Node      ├────┤    Edge      ├────┤   Node      │
│             │    │              │    │             │
└─────────────┘    └──────────────┘    └─────────────┘
      │                     │                   │
      │                     │                   │
      ▼                     ▼                   ▼
   Processa              Decide se            Executa
  mensagem               usar tools           ferramentas
  com LLM                                    (DuckDuckGo)
```

#### Componentes:
- **Chat Node**: Processa mensagens com OpenAI LLM
- **Tool Node**: Executa ferramentas disponíveis
- **Conditional Edges**: Decide fluxo baseado em tool calls
- **PostgreSQL Checkpointer**: Persiste estado das conversas
- **Retry Logic**: Recuperação de falhas com fallback models

#### Configurações por Ambiente:
```python
Development: Parâmetros relaxados, logging detalhado
Production: Fallback models, timeouts otimizados, pool connections
```

### 6. Modelos de Dados (models/)

#### User Model:
```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Métodos de segurança:
    - hash_password(): Hash seguro com bcrypt
    - verify_password(): Verificação de senha
```

#### Session Model:
```python
class Session(SQLModel, table=True):
    id: str = Field(primary_key=True)  # UUID
    user_id: int = Field(foreign_key="user.id")
    name: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 7. Serviço de Banco (database.py)

Camada de abstração para operações de banco:

#### Funcionalidades:
- **Connection pooling** configurável por ambiente
- **Health checks** para monitoramento
- **Operações CRUD** para User e Session
- **Tratamento de erros** específico por ambiente
- **Transações seguras** com rollback automático

#### Configuração do Pool:
```python
Development: Pool pequeno para economia de recursos
Production: Pool grande para alta concorrência
```

### 8. Schemas de Validação (schemas/)

Estruturas Pydantic para validação de API:

#### Chat Schemas:
```python
ChatRequest: Validação de entrada de mensagens
ChatResponse: Estrutura de resposta padronizada
StreamResponse: Eventos de streaming
Message: Estrutura básica de mensagem
```

#### Auth Schemas:
```python
UserCreate: Validação de registro
UserResponse: Dados públicos de usuário
TokenResponse: Estrutura de tokens JWT
SessionResponse: Dados de sessão com token
```

### 9. Utilitários (utils/)

#### auth.py:
- **Criação de JWT tokens** com expiração configurável
- **Verificação de tokens** com tratamento de erros
- **Configuração de claims** customizados

#### sanitization.py:
- **Sanitização de strings** contra injection
- **Validação de emails** com normalização
- **Validação de força** de senhas

#### graph.py:
- **Preparação de mensagens** para LLM
- **Conversão de formatos** entre APIs
- **Processamento de respostas** de LLM

## Fluxo de Dados Completo

### 1. Registro e Autenticação
```
Cliente                API                 Banco
  │                     │                   │
  ├─POST /register─────▶│                   │
  │                     ├─Valida dados─────▶│
  │                     ├─Hash password     │
  │                     ├─Cria user────────▶│
  │                     ◀─User criado───────┤
  │                     ├─Gera JWT token    │
  ◀─JWT token───────────┤                   │
```

### 2. Criação de Sessão
```
Cliente                API                 Banco
  │                     │                   │
  ├─POST /session──────▶│                   │
  │ (JWT header)        ├─Valida JWT       │
  │                     ├─Gera UUID        │
  │                     ├─Cria session────▶│
  │                     ◀─Session criada───┤
  │                     ├─Gera session JWT │
  ◀─Session token───────┤                   │
```

### 3. Chat Conversation
```
Cliente           API              LangGraph         OpenAI         Banco
  │                │                   │               │              │
  ├─POST /chat────▶│                   │               │              │
  │ (Session JWT)  ├─Valida JWT        │               │              │
  │                ├─Carrega histórico─┼──────────────▶│              │
  │                ├─Prepara mensagens─┼──────────────▶│              │
  │                │                   ├─Processa─────▶│              │
  │                │                   ◀─Resposta LLM─┤              │
  │                │                   ├─Decide tools  │              │
  │                │                   ├─Salva estado─┼─────────────▶│
  │                ◀─Resposta formatada┤               │              │
  ◀─Chat response──┤                   │               │              │
```

### 4. Streaming Chat
```
Cliente           API              LangGraph         OpenAI
  │                │                   │               │
  ├─POST /stream──▶│                   │               │
  │                ├─Inicia stream────▶│               │
  │                │                   ├─Stream LLM───▶│
  │                │                   ◀─Tokens────────┤
  │                ◀─SSE: token 1──────┤               │
  │                ◀─SSE: token 2──────┤               │
  │                ◀─SSE: token N──────┤               │
  │                ◀─SSE: done─────────┤               │
```

## Observabilidade e Monitoramento

### Métricas Prometheus
- **Latência de requests** por endpoint
- **Rate de erros** por tipo
- **Duração de inferência** do LLM
- **Conexões de banco** ativas
- **Throughput** de mensagens

### Logging Estruturado
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "chat_request_received",
  "session_id": "uuid-123",
  "user_id": "456",
  "message_count": 3,
  "environment": "production"
}
```

### Dashboards Grafana
- **Performance de API**: Latência, throughput, errors
- **LLM Metrics**: Tokens por segundo, custo, latência
- **Sistema**: CPU, memória, disco, rede
- **Negócio**: Usuários ativos, sessões, mensagens

## Configuração de Desenvolvimento

### Variáveis de Ambiente Requeridas:
```bash
# Banco de dados
POSTGRES_URL=postgresql://user:pass@localhost:5432/ali_db

# OpenAI
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# Autenticação
JWT_SECRET_KEY=your-secret-key

# Langfuse (opcional)
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...

# Ambiente
APP_ENV=development
```

### Setup Local:
```bash
# 1. Instalar dependências
pip install uv
uv pip install -e .

# 2. Configurar banco PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_DB=ali_db postgres

# 3. Rodar aplicação
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Problemas Conhecidos e Soluções

### 1. Dependência Agno Ausente
**Problema**: `agno` importado mas não declarado em pyproject.toml
**Solução**: Adicionar `agno>=X.X.X` às dependências ou remover implementação

### 2. Conflito LangGraph vs Agno
**Problema**: Duas implementações simultâneas causando confusão
**Solução**: Decidir por uma implementação e remover a outra

### 3. Arquivos .env Ausentes
**Problema**: Configuração depende de arquivos não commitados
**Solução**: Criar .env.example e documentar variáveis obrigatórias

### 4. Schema SQL Incompatível
**Problema**: schema.sql usa sintaxe SQLite, app usa PostgreSQL
**Solução**: Migrar schema para sintaxe PostgreSQL padrão

### 5. PostgreSQL Ausente no Docker
**Solução**: Criado docker-compose.postgres.yml para desenvolvimento local com PostgreSQL
**Solução**: Adicionar serviço postgres com volumes persistentes

## Roadmap de Melhorias

### Curto Prazo:
- [ ] Corrigir dependências e imports
- [ ] Adicionar PostgreSQL ao docker-compose
- [ ] Criar arquivo requirements.txt
- [ ] Implementar testes automatizados

### Médio Prazo:
- [ ] Sistema de plugins para tools
- [ ] Cache Redis para sessões
- [ ] Autenticação OAuth2
- [ ] API rate limiting por usuário

### Longo Prazo:
- [ ] Multi-tenancy
- [ ] Suporte a múltiplos LLMs
- [ ] Interface web administrativa
- [ ] Analytics avançados de conversas

## Contribuição

Para contribuir com o projeto:

1. **Fork** o repositório
2. **Crie branch** para feature: `git checkout -b feature/nova-funcionalidade`
3. **Commit** mudanças: `git commit -m 'Add: nova funcionalidade'`
4. **Push** para branch: `git push origin feature/nova-funcionalidade`
5. **Abra Pull Request** com descrição detalhada

### Padrões de Código:
- **Formato**: Black + isort
- **Linting**: Ruff + Flake8
- **Tipos**: mypy para type hints
- **Testes**: pytest com coverage >80%
- **Commits**: Conventional commits

---

*Este documento é mantido atualizado conforme a evolução da arquitetura. Para dúvidas ou sugestões, abra uma issue no repositório.*