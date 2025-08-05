
# Relatório de Diagnóstico - Ali API Produção
Data: 2025-08-04T22:33:51.198344
URL: https://ali-api-production-459480858531.us-central1.run.app

## Resumo dos Testes
- health_check: ✅ PASSOU
- detailed_health: ❌ FALHOU
- login_test: ❌ FALHOU
  Erro: all_credentials_failed
- cors_test: ✅ PASSOU

## Comandos de Diagnóstico
# Verificar logs da aplicação
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="ali-api-production"' --limit=50 --project=ali-api-production-459480858531

# Verificar status do serviço
gcloud run services describe ali-api-production --region=us-central1 --project=ali-api-production-459480858531

# Verificar variáveis de ambiente
gcloud run services describe ali-api-production --region=us-central1 --project=ali-api-production-459480858531 --format='value(spec.template.spec.template.spec.containers[0].env[].name)'

# Verificar métricas
gcloud monitoring metrics list --filter='metric.type:run.googleapis.com' --project=ali-api-production-459480858531

# Verificar últimas revisões
gcloud run revisions list --service=ali-api-production --region=us-central1 --project=ali-api-production-459480858531

## Próximos Passos
2. ❌ Endpoint de login com erro 500 - verificar:
   - Variáveis de ambiente (JWT_SECRET_KEY, FIREBASE_*)
   - Conexão com Firebase/Firestore
   - Logs de erro da aplicação

## Contato
Para suporte técnico, execute os comandos de diagnóstico acima.
