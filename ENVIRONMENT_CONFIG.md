# Configuração de Ambiente - Ali API

## Estrutura Simplificada

A partir de agora, o projeto utiliza uma estrutura de configuração simplificada com apenas dois arquivos de ambiente:

- **`.env.example`** - Template com todas as variáveis disponíveis
- **`.env`** - Arquivo principal de configuração (não versionado)

## Como Configurar

### 1. Configuração Inicial

```bash
# Copiar template para arquivo principal
cp .env.example .env

# Editar com suas configurações
nano .env
```

### 2. Variáveis Obrigatórias

Para o funcionamento básico, configure:

```bash
# JWT para autenticação
JWT_SECRET_KEY=sua-chave-secreta-aqui

# OpenAI para LLM
LLM_API_KEY=sk-sua-api-key-openai

# Firebase
FIREBASE_PROJECT_ID=seu-projeto-firebase
```

### 3. Configuração por Ambiente

O ambiente é controlado pela variável `APP_ENV`:

```bash
# Desenvolvimento (padrão)
APP_ENV=development
DEBUG=true

# Produção
APP_ENV=production
DEBUG=false
```

## Migração de Arquivos Antigos

Se você tinha arquivos `.env.development` ou `.env.production`, migre as configurações para o `.env` principal:

```bash
# Backup das configurações antigas (se existirem)
cp .env.development .env.backup

# Usar o novo arquivo principal
cp .env.example .env

# Copiar configurações relevantes do backup
# (edite manualmente o .env com as configurações necessárias)
```

## Vantagens da Nova Estrutura

1. **Simplicidade** - Apenas um arquivo para gerenciar
2. **Flexibilidade** - Mesmo arquivo serve para todos os ambientes
3. **Menos Confusão** - Não há dúvidas sobre qual arquivo usar
4. **Padrão da Indústria** - Segue convenções amplamente adotadas

## Scripts Atualizados

Todos os scripts foram atualizados para usar o novo padrão:

- `setup_dev.py` - Verifica `.env`
- `diagnose.py` - Usa configurações do `.env`
- `scripts/docker-dev.sh` - Cria `.env` se não existir
- Documentação atualizada

## Troubleshooting

### Arquivo .env não encontrado
```bash
cp .env.example .env
```

### Configurações não carregando
```bash
# Verificar se o arquivo existe
ls -la .env

# Verificar sintaxe
cat .env | grep -v '^#' | grep '='
```

### Problemas de permissão
```bash
chmod 600 .env  # Apenas proprietário pode ler/escrever
```

## Segurança

- O arquivo `.env` está no `.gitignore` e não será versionado
- Use valores seguros em produção
- Nunca commite o arquivo `.env` com secrets reais
- Para produção, considere usar gerenciadores de secrets (Google Secret Manager, AWS Secrets Manager, etc.)