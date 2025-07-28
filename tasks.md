🚀 CHECKLIST COMPLETO PARA PRODUÇÃO - Ali API (GCP + GitHub Secrets)            │
     │                                                                                 │
     │ 🔑 1. SECRETS E CONFIGURAÇÃO                                                    │
     │                                                                                 │
     │ 1.1 GitHub Repository Secrets                                                   │
     │                                                                                 │
     │ - GCP_PROJECT_ID - ID do projeto GCP                                            │
     │ - GCP_SERVICE_ACCOUNT_KEY - JSON da service account                             │
     │ - JWT_SECRET_KEY - Chave JWT forte (não usar a de desenvolvimento)              │
     │ - LLM_API_KEY - Chave da API do LLM (OpenAI/Anthropic)                          │
     │ - POSTGRES_PASSWORD - Senha forte do PostgreSQL                                 │
     │ - ELASTICSEARCH_API_KEY - Chave do Elasticsearch                                │
     │ - LANGFUSE_PUBLIC_KEY - Chave pública Langfuse                                  │
     │ - LANGFUSE_SECRET_KEY - Chave secreta Langfuse                                  │
     │                                                                                 │
     │ 1.2 Arquivos de Configuração                                                    │
     │                                                                                 │
     │ - CRÍTICO: Criar .env.production (template)                                     │
     │ - Criar .env.staging                                                            │
     │ - Configurar variáveis de ambiente no Cloud Run                                 │
     │ - Configurar CORS para domínios de produção                                     │
     │ - Implementar rate limiting mais restritivo                                     │
     │                                                                                 │
     │ ☁️ 2. INFRAESTRUTURA GCP                                                        │
     │                                                                                 │
     │ 2.1 Setup Inicial GCP                                                           │
     │                                                                                 │
     │ - Criar projeto GCP                                                             │
     │ - Configurar billing account                                                    │
     │ - Criar service account com permissões mínimas necessárias                      │
     │ - Habilitar APIs: Cloud Run, Cloud SQL, Container Registry, Cloud Monitoring    │
     │                                                                                 │
     │ 2.2 Cloud SQL (PostgreSQL)                                                      │
     │                                                                                 │
     │ - Criar instância Cloud SQL PostgreSQL (Production-ready)                       │
     │ - Configurar backup automático diário                                           │
     │ - Configurar rede privada/VPC                                                   │
     │ - Criar database ali_api                                                        │
     │ - Criar usuário específico da aplicação                                         │
     │ - Configurar SSL obrigatório                                                    │
     │ - Executar migrações do Alembic                                                 │
     │                                                                                 │
     │ 2.3 Elasticsearch                                                               │
     │                                                                                 │
     │ Escolher uma opção:                                                             │
     │ - Opção A: Elasticsearch Service (Elastic Cloud) - Recomendado                  │
     │ - Opção B: GCE com Elasticsearch auto-gerenciado                                │
     │ - Opção C: Vertex AI Search (alternativa GCP nativa)                            │
     │ - Configurar índices com settings adequados                                     │
     │ - Implementar backup de índices                                                 │
     │ - Configurar autenticação e autorização                                         │
     │                                                                                 │
     │ 2.4 Cloud Run (Aplicação)                                                       │
     │                                                                                 │
     │ - Configurar serviço Cloud Run                                                  │
     │ - Definir resource limits (CPU: 2, Memory: 4Gi recomendado)                     │
     │ - Configurar scaling (min: 1, max: 10 instances)                                │
     │ - Configurar VPC connector para Cloud SQL                                       │
     │ - Configurar SSL/TLS automático                                                 │
     │ - Configurar custom domain se necessário                                        │
     │                                                                                 │
     │ 🧪 3. TESTES E QUALIDADE (CRÍTICO - FALTANDO)                                   │
     │                                                                                 │
     │ 3.1 Estrutura de Testes (PRIORIDADE ALTA)                                       │
     │                                                                                 │
     │ tests/                                                                          │
     │   __init__.py                                                                   │
     │   conftest.py          # Configuração pytest                                    │
     │   test_health.py       # Teste health check                                     │
     │   test_database.py     # Teste DatabaseService                                  │
     │   test_rag.py          # Teste RAGService                                       │
     │   test_auth.py         # Teste autenticação                                     │
     │   test_api_endpoints.py # Teste endpoints críticos                              │
     │   integration/                                                                  │
     │     test_db_integration.py                                                      │
     │     test_elasticsearch.py                                                       │
     │                                                                                 │
     │ 3.2 Implementação de Testes                                                     │
     │                                                                                 │
     │ - CRÍTICO: Criar testes unitários básicos                                       │
     │ - CRÍTICO: Criar testes de integração                                           │
     │ - Configurar pytest adequadamente                                               │
     │ - Implementar testes de carga básicos                                           │
     │ - Configurar code coverage (mínimo 70%)                                         │
     │ - Testes end-to-end para fluxos críticos                                        │
     │                                                                                 │
     │ 3.3 Qualidade de Código                                                         │
     │                                                                                 │
     │ - Executar análise de segurança (bandit, safety)                                │
     │ - Implementar pre-commit hooks                                                  │
     │ - Revisar dependências por vulnerabilidades                                     │
     │ - Configurar SonarQube ou similar (opcional)                                    │
     │                                                                                 │
     │ 🚀 4. CI/CD PIPELINE                                                            │
     │                                                                                 │
     │ 4.1 GitHub Actions Workflow                                                     │
     │                                                                                 │
     │ - Criar .github/workflows/test.yml - Executa testes em PRs                      │
     │ - Criar .github/workflows/deploy-staging.yml - Deploy automático staging        │
     │ - Criar .github/workflows/deploy-production.yml - Deploy produção com aprovação │
     │ - Build e push da imagem Docker para GCR/Artifact Registry                      │
     │ - Executar migrações automáticas                                                │
     │ - Health check pós-deploy                                                       │
     │                                                                                 │
     │ 4.2 Estratégia de Deploy                                                        │
     │                                                                                 │
     │ - Staging: Branch develop → Cloud Run staging (automático)                      │
     │ - Production: Branch main → Cloud Run production (manual approval)              │
     │ - Implementar rollback automático em caso de falha                              │
     │ - Blue-green deployment ou canary (avançado)                                    │
     │                                                                                 │
     │ 🛡️ 5. SEGURANÇ                                                                 │
     │                                                                                 │
     │ 5.1 Configurações de Segurança                                                  │
     │                                                                                 │
     │ - Configurar HTTPS obrigatório                                                  │
     │ - Implementar headers de segurança (HSTS, CSP, etc.)                            │
     │ - Configurar Cloud Armor para proteção DDoS                                     │
     │ - Implementar validação de entrada rigorosa                                     │
     │ - Configurar autenticação/autorização adequada                                  │
     │                                                                                 │
     │ 5.2 IAM e Permissões GCP                                                        │
     │                                                                                 │
     │ - Service account com princípio de menor privilégio                             │
     │ - Configurar Cloud IAM adequadamente                                            │
     │ - Habilitar audit logs                                                          │
     │ - Configurar VPC e subnets adequadas                                            │
     │ - Implementar secrets management adequado                                       │
     │                                                                                 │
     │ 📊 6. MONITORAMENTO E OBSERVABILIDADE                                           │
     │                                                                                 │
     │ 6.1 Cloud Monitoring (GCP)                                                      │
     │                                                                                 │
     │ - Configurar alertas de uptime (>99.5%)                                         │
     │ - Configurar alertas de error rate (>1%)                                        │
     │ - Configurar alertas de latência (>2s p95)                                      │
     │ - Configurar alertas de resource usage (CPU>80%, Memory>85%)                    │
     │ - Dashboard customizado no Cloud Monitoring                                     │
     │                                                                                 │
     │ 6.2 Logging                                                                     │
     │                                                                                 │
     │ - Configurar structured logging completo                                        │
     │ - Implementar log aggregation no Cloud Logging                                  │
     │ - Criar log-based metrics                                                       │
     │ - Configurar alertas baseados em logs                                           │
     │ - Garantir logs não contenham informações sensíveis                             │
     │ - Configurar log retention adequado                                             │
     │                                                                                 │
     │ 6.3 Métricas Customizadas                                                       │
     │                                                                                 │
     │ - Métricas de negócio (requests RAG, tokens processados)                        │
     │ - Métricas de performance do LLM                                                │
     │ - Métricas de saúde do Elasticsearch                                            │
     │ - SLA/SLI definidos e monitorados                                               │
     │                                                                                 │
     │ 6.4 Health Checks Detalhados                                                    │
     │                                                                                 │
     │ - Health check básico (/health)                                                 │
     │ - Deep health check com dependências                                            │
     │ - Readiness probe para Cloud Run                                                │
     │ - Liveness probe para Cloud Run                                                 │
     │                                                                                 │
     │ 🔄 7. BACKUP E DISASTER RECOVERY                                                │
     │                                                                                 │
     │ - Backup automático do Cloud SQL (diário, retenção 30 dias)                     │
     │ - Backup dos índices Elasticsearch                                              │
     │ - Backup de configurações e secrets                                             │
     │ - Plano de disaster recovery documentado                                        │
     │ - Testes regulares de restore (mensal)                                          │
     │ - RTO: <1h, RPO: <15min definidos                                               │
     │                                                                                 │
     │ 📈 8. PERFORMANCE E ESCALABILIDADE                                              │
     │                                                                                 │
     │ 8.1 Otimizações                                                                 │
     │                                                                                 │
     │ - Implementar caching (Cloud Memorystore/Redis)                                 │
     │ - Otimizar queries do banco (índices, connection pooling)                       │
     │ - Configurar CDN (Cloud CDN) se necessário                                      │
     │ - Implementar compressão de responses                                           │
     │ - Otimizar modelo de embedding/RAG                                              │
     │                                                                                 │
     │ 8.2 Escalabilidade                                                              │
     │                                                                                 │
     │ - Configurar auto-scaling no Cloud Run                                          │
     │ - Implementar load balancing                                                    │
     │ - Testar capacidade máxima                                                      │
     │ - Configurar quotas e limits adequados                                          │
     │                                                                                 │
     │ 📋 9. ARQUIVOS E SCRIPTS A CRIAR                                                │
     │                                                                                 │
     │ 9.1 GitHub Actions                                                              │
     │                                                                                 │
     │ .github/                                                                        │
     │   workflows/                                                                    │
     │     test.yml           # Testes automatizados                                   │
     │     deploy-staging.yml # Deploy staging                                         │
     │     deploy-production.yml # Deploy produção                                     │
     │                                                                                 │
     │ 9.2 Configurações                                                               │
     │                                                                                 │
     │ .env.production        # Template variáveis produção                            │
     │ .env.staging          # Template variáveis staging                              │
     │ cloudbuild.yaml       # Cloud Build config (alternativa)                        │
     │                                                                                 │
     │ 9.3 Scripts                                                                     │
     │                                                                                 │
     │ scripts/                                                                        │
     │   setup-gcp.sh         # Setup inicial GCP                                      │
     │   deploy-manual.sh     # Deploy manual emergencial                              │
     │   migrate-db.sh        # Migrações banco                                        │
     │   backup-restore.sh    # Scripts backup/restore                                 │
     │                                                                                 │
     │ 9.4 Documentação                                                                │
     │                                                                                 │
     │ - README.md atualizado com instruções de deploy                                 │
     │ - Documentação de APIs (OpenAPI/Swagger)                                        │
     │ - Runbooks de operação                                                          │
     │ - Procedimentos de emergência                                                   │
     │ - Guia de troubleshooting                                                       │
     │                                                                                 │
     │ 🔧 10. CONFIGURAÇÕES ESPECÍFICAS                                                │
     │                                                                                 │
     │ 10.1 Dockerfile Otimizado                                                       │
     │                                                                                 │
     │ - Multi-stage build para reduzir tamanho                                        │
     │ - Non-root user configurado                                                     │
     │ - Health check integrado                                                        │
     │ - Otimizações de cache de layers                                                │
     │                                                                                 │
     │ 10.2 Configuração Cloud Run                                                     │
     │                                                                                 │
     │ - Concurrency: 80-100 requests por instance                                     │
     │ - CPU allocation: only during requests                                          │
     │ - Request timeout: 900s (máximo)                                                │
     │ - Memory: 4Gi mínimo para RAG                                                   │
     │                                                                                 │
     │ ⚡ ROADMAP DE IMPLEMENTAÇÃO                                                      │
     │                                                                                 │
     │ Fase 1 - Fundação (Semana 1)                                                    │
     │                                                                                 │
     │ 1. Setup GCP e GitHub Secrets                                                   │
     │ 2. CRÍTICO: Criar estrutura de testes básica                                    │
     │ 3. Configurar Cloud SQL                                                         │
     │ 4. Pipeline CI/CD básico                                                        │
     │                                                                                 │
     │ Fase 2 - Deploy Staging (Semana 2)                                              │
     │                                                                                 │
     │ 1. Configurar Elasticsearch                                                     │
     │ 2. Deploy staging funcional                                                     │
     │ 3. Monitoramento básico                                                         │
     │ 4. Testes de integração                                                         │
     │                                                                                 │
     │ Fase 3 - Produção (Semana 3)                                                    │
     │                                                                                 │
     │ 1. Deploy produção                                                              │
     │ 2. Monitoramento completo                                                       │
     │ 3. Backup e DR                                                                  │
     │ 4. Performance tuning                                                           │
     │                                                                                 │
     │ Fase 4 - Otimização (Semana 4)                                                  │
     │                                                                                 │
     │ 1. Caching e otimizações                                                        │
     │ 2. Testes de carga                                                              │
     │ 3. Documentação completa                                                        │
     │ 4. Treinamento da equipe                                                        │
     │                                                                                 │
     │ 🚨 ITENS CRÍTICOS E BLOQUEADORES                                                │
     │                                                                                 │
     │ DEVE SER FEITO PRIMEIRO:                                                        │
     │                                                                                 │
     │ 1. Criar estrutura de testes - Sem isso, deploy é arriscado                     │
     │ 2. Configurar secrets adequadamente - Segurança básica                          │
     │ 3. Setup Cloud SQL - Dependência crítica                                        │
     │ 4. Health checks detalhados - Para monitoramento                                │
     │                                                                                 │
     │ PODE SER FEITO DEPOIS:                                                          │
     │                                                                                 │
     │ - Otimizações de performance                                                    │
     │ - Caching avançado                                                              │
     │ - Monitoramento avançado                                                        │
     │ - Disaster recovery completo                                                    │
     │                                                                                 │
     │ Esta é a lista completa e priorizada para colocar a Ali API em produção na GCP!