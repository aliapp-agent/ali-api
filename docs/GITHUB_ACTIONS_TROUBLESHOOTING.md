# GitHub Actions - Solução de Problemas

## 🚨 Problema: Container Qdrant Falhando no GitHub Actions

### Sintomas
- Erro: "Service container qdrant failed"
- Mensagem: "One or more containers failed to start"
- Health check do Qdrant não passa

### 🔍 Causa Raiz
O problema estava relacionado a:

1. **Endpoint de Health Check Incorreto**
   - Estava usando `/health` que pode não existir na versão latest
   - Solução: Usar endpoint raiz `/` que sempre responde

2. **Timeouts Muito Agressivos**
   - Health check com apenas 5s de timeout
   - Apenas 5 tentativas de retry
   - Solução: Aumentar para 10s timeout, 10 retries, 30s start period

3. **Falta de Logs de Debug**
   - Difícil identificar onde exatamente falha
   - Solução: Adicionar logs detalhados e testes de conectividade

### ✅ Correções Aplicadas

#### 1. Health Check Melhorado
```yaml
# ANTES (problemático)
options: >
  --health-cmd "curl -f http://localhost:6333/health || exit 1"
  --health-interval 10s
  --health-timeout 5s
  --health-retries 5

# DEPOIS (corrigido)
options: >
  --health-cmd "curl -f http://localhost:6333/ || exit 1"
  --health-interval 30s
  --health-timeout 10s
  --health-retries 10
  --health-start-period 30s
```

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

---

**Nota**: Essas correções foram aplicadas tanto no workflow de staging quanto no de produção para manter consistência.