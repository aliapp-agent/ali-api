# WhatsApp Setup - Evolution API

## 🔧 Configuração Rápida

### 1. Variáveis .env
```bash
# Evolution API
EVOLUTION_API_URL=https://your-evolution-api-domain.com
EVOLUTION_INSTANCE=your-instance-name
EVOLUTION_API_KEY=your-api-key
```

### 2. Criar Instância
```bash
curl -X POST "${EVOLUTION_API_URL}/instance/create-instance-basic" \
  -H "Content-Type: application/json" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -d '{
    "instanceName": "minha-instancia",
    "webhook": {
      "url": "https://your-ali-api-domain.com/api/v1/whatsapp/webhook/evolution",
      "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE", "QRCODE_UPDATED"]
    }
  }'
```

### 3. Configurar Webhook

Configure o webhook para receber mensagens:

```bash
curl -X POST "https://your-evolution-api-domain.com/webhook/set/minha-instancia" \
  -H "Content-Type: application/json" \
  -H "apikey: YOUR_API_KEY" \
  -d '{
    "url": "https://your-ali-api-domain.com/api/v1/whatsapp/webhook/evolution",
    "events": [
      "MESSAGES_UPSERT",
      "CONNECTION_UPDATE", 
      "QRCODE_UPDATED"
    ]
  }'
```

### 4. Conectar WhatsApp

1. **Obter QR Code:**
```bash
curl -X GET "https://your-evolution-api-domain.com/instance/connect/minha-instancia" \
  -H "apikey: YOUR_API_KEY"
```

2. **Escanear QR Code** com o WhatsApp no celular
3. **Verificar conexão:**
```bash
curl -X GET "https://your-evolution-api-domain.com/instance/connectionState/minha-instancia" \
  -H "apikey: YOUR_API_KEY"
```

## 🧪 Testes

### 1. Testar Webhook

```bash
curl -X GET "http://localhost:8000/api/v1/whatsapp/webhook/test"
```

**Resposta esperada:**
```json
{
  "status": "ok",
  "message": "WhatsApp webhook is working",
  "timestamp": "2024-01-15T10:30:00Z",
  "evolution_config": {
    "api_url": "https://api.evolution.com",
    "instance": "minha-instancia",
    "api_key_configured": true
  }
}
```

### 2. Simular Mensagem

```bash
curl -X POST "http://localhost:8000/api/v1/whatsapp/webhook/test-message" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "5511999999999",
    "message": "Olá, teste do chatbot!"
  }'
```

### 3. Enviar Mensagem Direta

```bash
curl -X POST "http://localhost:8000/api/v1/chatbot/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "message": "Envie uma mensagem para 5511999999999 dizendo: Olá do Ali!",
    "session_id": "test-session"
  }'
```

## 📱 Fluxo de Funcionamento

### 1. Recebimento de Mensagens

1. **WhatsApp** → **Evolution API** → **Ali API** (webhook)
2. **Ali API** processa com **AgnoAgent**
3. **AgnoAgent** gera resposta usando RAG + LLM
4. **AgnoAgent** usa `whatsapp_tool` para enviar resposta
5. **Ali API** → **Evolution API** → **WhatsApp**

### 2. Eventos Suportados

- `MESSAGES_UPSERT`: Novas mensagens recebidas
- `CONNECTION_UPDATE`: Mudanças no status da conexão
- `QRCODE_UPDATED`: Atualização do QR Code

### 3. Tipos de Mensagem

**Suportados:**
- ✅ Mensagens de texto
- ✅ Mensagens de texto extendidas

**Não suportados ainda:**
- ❌ Imagens
- ❌ Áudios
- ❌ Documentos
- ❌ Stickers

## 🔍 Monitoramento

### 1. Logs da Aplicação

```bash
# Ver logs em tempo real
tail -f logs/app.log

# Filtrar logs do WhatsApp
grep "whatsapp" logs/app.log

# Ver erros
grep "ERROR" logs/app.log | grep "whatsapp"
```

### 2. Health Check

```bash
# Verificar saúde da aplicação
curl -X GET "http://localhost:8000/health"

# Verificar saúde detalhada
curl -X GET "http://localhost:8000/deep-health"
```

### 3. Verificar Configuração Evolution API

```bash
# Status da instância
curl -X GET "https://your-evolution-api-domain.com/instance/connectionState/minha-instancia" \
  -H "apikey: YOUR_API_KEY"

# Webhook configurado
curl -X GET "https://your-evolution-api-domain.com/webhook/find/minha-instancia" \
  -H "apikey: YOUR_API_KEY"
```

## 🚨 Troubleshooting

### Problema: Webhook não recebe mensagens

**Verificações:**
1. URL do webhook está acessível publicamente
2. Instância está conectada
3. Eventos estão configurados corretamente

```bash
# Testar conectividade
curl -X GET "https://your-ali-api-domain.com/api/v1/whatsapp/webhook/test"

# Verificar logs
grep "evolution_webhook" logs/app.log
```

### Problema: Não consegue enviar mensagens

**Verificações:**
1. Variáveis `EVOLUTION_API_*` estão corretas
2. API Key tem permissões
3. Instância está ativa

```bash
# Testar envio direto
curl -X POST "https://your-evolution-api-domain.com/message/sendText/minha-instancia" \
  -H "Content-Type: application/json" \
  -H "apikey: YOUR_API_KEY" \
  -d '{
    "number": "5511999999999",
    "text": "Teste direto"
  }'
```

### Problema: QR Code não aparece

**Soluções:**
1. Reiniciar a instância:
```bash
curl -X PUT "https://your-evolution-api-domain.com/instance/restart/minha-instancia" \
  -H "apikey: YOUR_API_KEY"
```

2. Deletar e recriar instância:
```bash
# Deletar
curl -X DELETE "https://your-evolution-api-domain.com/instance/delete/minha-instancia" \
  -H "apikey: YOUR_API_KEY"

# Recriar (ver seção "Criar Instância")
```

## 📊 Métricas e Observabilidade

A aplicação coleta métricas sobre:

- **Mensagens recebidas** via webhook
- **Mensagens enviadas** via Evolution API
- **Tempo de processamento** do AgnoAgent
- **Erros** de comunicação
- **Status de conexão** do WhatsApp

Acesse as métricas em: `http://localhost:8000/metrics`

## 🔒 Segurança

### Recomendações:

1. **HTTPS obrigatório** para webhooks em produção
2. **Validação de origem** dos webhooks (IP allowlist)
3. **Rate limiting** configurado
4. **Logs seguros** (não exposição de números/conteúdo)
5. **API Keys** em variáveis de ambiente seguras

### Implementar Validação de Webhook:

```python
# Exemplo de middleware para validar origem
def validate_webhook_origin(request):
    allowed_ips = ["IP_DA_EVOLUTION_API"]
    client_ip = request.client.host
    if client_ip not in allowed_ips:
        raise HTTPException(403, "Forbidden")
```

## 📚 Recursos Adicionais

- [Evolution API Documentation](https://doc.evolution-api.com/v2/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/)
- [FastAPI WebHooks](https://fastapi.tiangolo.com/advanced/events/)
- [Agno Framework](https://github.com/agno-ai/agno)

---

**Versão:** 1.0.0  
**Última atualização:** Janeiro 2024