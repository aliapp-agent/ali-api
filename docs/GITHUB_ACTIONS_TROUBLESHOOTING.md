# GitHub Actions - Solução de Problemas

## 🚨 Problema: Container Qdrant Falhando no GitHub Actions

### Sintomas
- Erro: "Service container qdrant failed"
- Mensagem: "One or more containers failed to start"
- Health check do Qdrant não passa

### 🔍 Causa Raiz
O problema estava relacionado a:

1. **Versão Instável do Qdrant**
   - Estava usando `qdrant/qdrant:latest` que pode introduzir mudanças incompatíveis
   - Solução: Fixar versão estável `qdrant/qdrant:v1.7.4`

2. **Endpoint de Health Check Incorreto**
   - Estava usando endpoint raiz `/` em vez do endpoint dedicado de saúde
   - Solução: Usar endpoint `/health` que é especificamente projetado para health checks

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
  --health-cmd "curl -f http://localhost:6333/health || exit 1"
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

#### 2. Logs de Debug Adicionados
```bash
echo "Checking docker version"
docker --version

echo "Clean up resources from previous jobs"
docker system prune -f || true

echo "Testing Qdrant health endpoint..."
curl -v http://localhost:6333/ || echo "⚠️ Qdrant root endpoint failed"
curl -v http://localhost:6333/health || echo "⚠️ Qdrant health endpoint failed"
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
curl http://localhost:6333/health

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

- [ ] Health check usa endpoint correto (`/` em vez de `/health`)
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
3. ✅ Passar no health check `/health` dentro de 60s
4. ✅ Detectar rapidamente quando o serviço fica disponível (10s interval)
5. ✅ Executar os testes sem falhas de conectividade
6. ✅ Completar o deploy sem erros

Os logs devem mostrar:
```
✅ PostgreSQL is ready
✅ Qdrant is ready
Testing Qdrant health endpoint...
```

### Melhorias Implementadas

- **Estabilidade**: Versão fixa elimina surpresas de breaking changes
- **Confiabilidade**: Endpoint `/health` é mais confiável que `/`
- **Performance**: Detecção mais rápida (10s vs 30s) quando serviço fica disponível
- **Robustez**: Mais tempo para inicialização (60s) e mais tentativas (12)

---

**Nota**: Essas correções foram aplicadas tanto no workflow de staging quanto no de produção para manter consistência.