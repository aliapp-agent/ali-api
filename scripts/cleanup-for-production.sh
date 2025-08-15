#!/bin/bash

# Script de Limpeza para Produção
# Remove arquivos não essenciais para reduzir tamanho e melhorar segurança

set -e

echo "🧹 Iniciando limpeza para produção..."

# Função para remover arquivo/pasta se existir
remove_if_exists() {
    if [ -e "$1" ]; then
        echo "  ❌ Removendo: $1"
        rm -rf "$1"
    else
        echo "  ⏭️  Não encontrado: $1"
    fi
}

# Arquivos de teste
echo "📋 Removendo arquivos de teste..."
remove_if_exists "tests/"
remove_if_exists "pytest.ini"
remove_if_exists "simple_session_test.py"

# Arquivos de desenvolvimento
echo "🔧 Removendo arquivos de desenvolvimento..."
remove_if_exists "setup_dev.py"
remove_if_exists "diagnose.py"
remove_if_exists "docker-compose.yml"
remove_if_exists ".env.example"
remove_if_exists "firebase-credentials.json.example"

# Sistema de avaliação
echo "📊 Removendo sistema de avaliação..."
remove_if_exists "evals/"

# Scripts de desenvolvimento
echo "📜 Removendo scripts de desenvolvimento..."
remove_if_exists "scripts/docker-dev.sh"
remove_if_exists "scripts/logs-docker.sh"
remove_if_exists "scripts/run-docker.sh"
remove_if_exists "scripts/stop-docker.sh"
remove_if_exists "scripts/build-docker.sh"
remove_if_exists "scripts/migration/"

# Makefile
echo "🔨 Removendo Makefile..."
remove_if_exists "Makefile"

# Setup scripts (após configuração inicial)
echo "⚙️ Removendo scripts de setup..."
remove_if_exists "setup_evolution.sh"
remove_if_exists "scripts/setup-evolution-secrets.sh"
remove_if_exists "scripts/setup-gcp.sh"
remove_if_exists "scripts/setup-monitoring.sh"
remove_if_exists "scripts/setup_evolution.py"
remove_if_exists "scripts/setup_qdrant.py"
remove_if_exists "scripts/setup_whatsapp.py"

# Arquivos de monitoramento (opcional)
read -p "🔍 Remover configurações de monitoramento? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📈 Removendo configurações de monitoramento..."
    remove_if_exists "grafana/"
    remove_if_exists "prometheus/"
    remove_if_exists "k8s-health-config.yaml"
else
    echo "📈 Mantendo configurações de monitoramento..."
fi

# GitHub Actions (opcional)
read -p "🚀 Remover workflows do GitHub Actions? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Removendo workflows do GitHub Actions..."
    remove_if_exists ".github/"
else
    echo "🔄 Mantendo workflows do GitHub Actions..."
fi

# requirements-evolution.txt já foi consolidado no requirements.txt principal

# Documentação (opcional)
read -p "📚 Remover documentação (pasta docs/)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📚 Removendo documentação..."
    remove_if_exists "docs/"
else
    echo "📚 Mantendo documentação..."
fi

echo ""
echo "✅ Limpeza concluída!"
echo "📊 Verificando tamanho atual..."
du -sh . 2>/dev/null || echo "Não foi possível calcular o tamanho"

echo ""
echo "🔍 Arquivos restantes na raiz:"
ls -la | grep -E '^-' | awk '{print $9}' | head -20

echo ""
echo "📁 Pastas restantes:"
ls -la | grep -E '^d' | awk '{print $9}' | grep -v '^\.$' | grep -v '^\.\.$' | head -10

echo ""
echo "⚠️  IMPORTANTE:"
echo "   - Teste a aplicação após a limpeza"
echo "   - Faça backup antes de usar em produção"
echo "   - Verifique se todas as dependências estão corretas"
echo "   - Atualize o .dockerignore se necessário"