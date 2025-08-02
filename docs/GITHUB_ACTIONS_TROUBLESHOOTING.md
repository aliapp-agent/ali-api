# GitHub Actions - Solução de Problemas

## ⚠️ ATUALIZAÇÃO: Qdrant Removido dos Containers

### Status Atual
- ✅ Qdrant foi removido do docker-compose.yml e workflows do GitHub Actions
- ✅ Aplicação agora roda sem dependência de container Qdrant
- ✅ Qdrant deve ser executado separadamente quando necessário
- ✅ Configuração via variável de ambiente QDRANT_URL

### 🚀 Como Executar Qdrant Separadamente

```bash
# Executar Qdrant em container separado
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v qdrant_data:/qdrant/storage \
  qdrant/qdrant:v1.7.4

# Verificar se está rodando
curl http://localhost:6333/healthz

# Configurar variável de ambiente
export QDRANT_URL=http://localhost:6333
```

### 🔍 Causa Raiz (Histórico)
O problema estava relacionado a:

1. **Versão Instável do Qdrant**
   - Estava usando `qdrant/qdrant:latest` que pode introduzir mudanças incompatíveis
   - Solução: Fixar versão estável `qdrant/qdrant:v1.7.4`

2. **Endpoint de Health Check Incorreto**
   - Estava usando endpoint raiz `/` em vez do endpoint dedicado de saúde
   - Solução: Usar endpoint `/healthz` que é mais confiável para ambientes CI/CD

3. **Tempo de Inicialização Insuficiente**
   - Start period de 30s era muito curto para inicialização do Qdrant no ambiente CI
   - Solução: Aumentar start period para 60s

4. **Timing de Health Check Subótimo**
   - Intervalo de 30s era muito longo para detectar quando o serviço fica disponível
   - Solução: Reduzir intervalo para 10s com mais tentativas (12)

5. **Falta de Logs de Debug**
   - Difícil identificar onde exatamente falha
   - Solução: Adicionar logs detalhados e testes de conectividade

6. **Formatação YAML Incorreta**
   - Uso de `>` em vez de `>-` causava quebra de linha extra
   - Erro: `time: unknown unit "s\x0a"` no parâmetro `--health-start-period`
   - Solução: Usar `>-` para remover quebra de linha final

### ✅ Correções Aplicadas

#### 1. Versão Qdrant Fixada
```yaml
qdrant:
  image: qdrant/qdrant:v1.7.4  # Era: qdrant/qdrant:latest
```

#### 2. Health Check Otimizado
```yaml
# ANTES (problemático)
options: >
  --health-cmd "curl -f http://localhost:6333/ || exit 1"
  --health-interval 30s
  --health-timeout 10s
  --health-retries 10

# DEPOIS (corrigido)
options: >-
  --health-cmd "curl -f http://localhost:6333/healthz || exit 1"
  --health-interval 10s
  --health-timeout 10s
  --health-retries 12
  --health-start-period 60s
```

#### 🚨 **Problema Crítico: Formatação YAML**
```yaml
# ❌ ERRADO - Causa erro "time: unknown unit 's\x0a'"
options: >
  --health-start-period 30s

# ✅ CORRETO - Remove quebra de linha final
options: >-
  --health-start-period 30s
```

**Explicação**: O operador `>` em YAML preserva a quebra de linha final, enquanto `>-` a remove. Docker interpreta `30s\n` como uma unidade de tempo inválida.

## 🏥 Health Check: /healthz vs /readyz

### Diferenças dos Endpoints

- **`/healthz`**: Verifica se o serviço está rodando e respondendo
  - ✅ Mais tolerante e confiável para CI/CD
  - ✅ Retorna 200 se o Qdrant iniciou com sucesso
  - ✅ Não falha por questões de inicialização de shards

- **`/readyz`**: Verifica se o serviço está completamente pronto
  - ⚠️ Mais rigoroso, pode falhar mesmo com serviço funcional
  - ⚠️ Pode retornar erro se shards não estão inicializados
  - ⚠️ Problemático em ambientes CI/CD com timing restrito

### Por que mudamos para /healthz?

O endpoint `/readyz` é muito rigoroso para ambientes de teste, podendo falhar com "some shards are not ready" mesmo quando o Qdrant está funcionalmente operacional. Para CI/CD, precisamos apenas verificar se o serviço está rodando, não se está em estado de produção completo.

#### 2. Logs de Debug Adicionados
```bash
echo "Checking docker version"
docker --version

echo "Clean up resources from previous jobs"
docker system prune -f || true

echo "Testing Qdrant readiness endpoint..."
curl -v http://localhost:6333/healthz || echo "⚠️ Qdrant healthz endpoint failed"
```

#### 3. Timeouts Aumentados
- Timeout de espera: 60s → 120s
- Intervalo de verificação: 1s → 2s
- Logs informativos durante a espera

### 🛠️ Como Testar Localmente

```bash
# Testar Qdrant standalone
docker run --rm -d --name test-qdrant -p 6333:6333 qdrant/qdrant:latest

# Verificar se está respondendo
curl http://localhost:6333/
curl http://localhost:6333/healthz

# Limpar
docker stop test-qdrant
```

### 🔧 Troubleshooting Adicional

#### Se o problema persistir:

1. **Verificar versão do Qdrant**
   ```yaml
   # Fixar versão específica em vez de 'latest'
   image: qdrant/qdrant:v1.7.4
   ```

2. **Adicionar variáveis de ambiente**
   ```yaml
   qdrant:
     image: qdrant/qdrant:latest
     environment:
       - QDRANT__SERVICE__HTTP_PORT=6333
       - QDRANT__LOG_LEVEL=INFO
   ```

3. **Verificar recursos do runner**
   ```yaml
   # Adicionar step para verificar recursos
   - name: Check system resources
     run: |
       echo "Memory:"
       free -h
       echo "Disk:"
       df -h
       echo "Docker info:"
       docker info
   ```

### 📋 Checklist de Verificação

- [ ] Health check usa endpoint correto (`/healthz` em vez de `/` ou `/readyz`)
- [ ] Timeouts são adequados (≥30s start period)
- [ ] Logs de debug estão habilitados
- [ ] Versão do Qdrant é compatível
- [ ] Recursos do sistema são suficientes
- [ ] Network connectivity está funcionando

### 🚀 Próximos Passos

1. **Monitoramento**: Adicionar métricas de saúde dos containers
2. **Alertas**: Configurar notificações para falhas de CI/CD
3. **Cache**: Implementar cache de imagens Docker para acelerar builds
4. **Testes**: Adicionar testes de integração específicos para Qdrant

## Resultado Esperado

Após essas correções, o workflow deve:

1. ✅ Usar versão estável do Qdrant (v1.7.4)
2. ✅ Inicializar o container Qdrant com sucesso
3. ✅ Passar no health check `/healthz` dentro de 90s
4. ✅ Detectar rapidamente quando o serviço fica disponível (10s interval)
5. ✅ Executar os testes sem falhas de conectividade
6. ✅ Completar o deploy sem erros

Os logs devem mostrar:
```
✅ PostgreSQL is ready
✅ Qdrant is ready
Testing Qdrant readiness endpoint...
```

### Melhorias Implementadas

- **Estabilidade**: Versão fixa elimina surpresas de breaking changes
- **Confiabilidade**: Endpoint `/healthz` é mais confiável para CI/CD que `/readyz`
- **Performance**: Detecção mais rápida (10s vs 30s) quando serviço fica disponível
- **Robustez**: Mais tempo para inicialização (60s) e mais tentativas (12)

---

**Nota**: Essas correções foram aplicadas tanto no workflow de staging quanto no de produção para manter consistência.