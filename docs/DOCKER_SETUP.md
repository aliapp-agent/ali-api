# Docker Setup - Ali API

## 🚀 Quick Start

### Desenvolvimento Completo (App + PostgreSQL)
```bash
# Subir todos os serviços
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml up -d

# Verificar logs
docker-compose logs -f ali-api

# Parar serviços
docker-compose down
```

### Apenas Aplicação (PostgreSQL externo)
```bash
# Configurar DATABASE_URL no .env primeiro
docker-compose up -d ali-api
```

## 🔧 Configurações

### docker-compose.yml
- ✅ Aplicação principal
- ✅ Rede ali-network
- ✅ Volumes desenvolvimento
- ✅ Healthcheck integrado

### docker-compose.postgres.yml
- ✅ PostgreSQL 15-alpine
- ✅ pgAdmin opcional
- ✅ Volumes persistentes
- ✅ Init script automático

```bash
# Configurar POSTGRES_URL no .env
echo "POSTGRES_URL=postgresql://user:pass@host:5432/db" >> .env

# Subir apenas a aplicação
docker-compose up -d
```

### Opção 3: Com pgAdmin (Interface de administração)

```bash
# Subir com pgAdmin
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml --profile admin up -d

# Acessar pgAdmin em http://localhost:5050
# Email: admin@ali.com
# Senha: admin123
```

## Configuração de Ambiente

### Variáveis Obrigatórias

Crie um arquivo `.env` com:

```bash
# Aplicação
APP_ENV=development
DEBUG=true

# Banco de dados (automático com docker-compose.postgres.yml)
POSTGRES_URL=postgresql://ali_user:ali_password@postgres:5432/ali_db

# LLM
LLM_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4o-mini

# Autenticação
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars

# Observabilidade (opcional)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Comandos Úteis

### Desenvolvimento

```bash
# Build e start
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml up --build

# Rebuild apenas a aplicação
docker-compose build app

# Logs em tempo real
docker-compose logs -f app

# Executar comandos na aplicação
docker-compose exec app bash
docker-compose exec app uv run pytest
docker-compose exec app uv run alembic upgrade head
```

### Banco de Dados

```bash
# Conectar ao PostgreSQL
docker-compose exec postgres psql -U ali_user -d ali_db

# Backup do banco
docker-compose exec postgres pg_dump -U ali_user ali_db > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U ali_user ali_db < backup.sql
```

### Limpeza

```bash
# Parar e remover containers
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml down

# Remover volumes (CUIDADO: apaga dados do banco)
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml down -v

# Limpeza completa
docker system prune -a
```

## Estrutura de Rede

```
ali-network (bridge)
├── app (porta 8000)
├── postgres (porta 5432)
└── pgadmin (porta 5050) [opcional]
```

## Troubleshooting

### Problema: Aplicação não conecta ao PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
docker-compose ps postgres

# Verificar logs do PostgreSQL
docker-compose logs postgres

# Testar conexão
docker-compose exec app ping postgres
```

### Problema: Dependências não instaladas

```bash
# Rebuild com cache limpo
docker-compose build --no-cache app

# Verificar se uv está funcionando
docker-compose exec app uv --version
```

### Problema: Permissões de arquivo

```bash
# Verificar proprietário dos arquivos
ls -la logs/

# Ajustar permissões se necessário
sudo chown -R $USER:$USER logs/
```

## Monitoramento

### Health Checks

```bash
# Status dos serviços
docker-compose ps

# Health check da aplicação
curl http://localhost:8000/health

# Health check do PostgreSQL
docker-compose exec postgres pg_isready -U ali_user
```

### Métricas

- **Aplicação**: http://localhost:8000/metrics
- **pgAdmin**: http://localhost:5050 (se habilitado)
- **Logs**: `./logs/` directory

## Produção

Para produção, considere:

1. **Usar PostgreSQL gerenciado** (Cloud SQL, RDS, etc.)
2. **Configurar secrets** adequadamente
3. **Usar imagens otimizadas** sem volumes de desenvolvimento
4. **Configurar reverse proxy** (nginx, traefik)
5. **Implementar backup automatizado**
6. **Monitoramento avançado** (Prometheus, Grafana)

Veja `docs/PRODUCTION_TODO.md` para mais detalhes.