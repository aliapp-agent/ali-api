#!/bin/bash

# Script para configurar o Evolution API
# Este script instala as dependências e executa a configuração automatizada

set -e

echo "🚀 Configuração do Evolution API para Ali API"
echo "============================================="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.8+"
    exit 1
fi

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Instale pip"
    exit 1
fi

# Instalar dependências do script
echo "📦 Instalando dependências..."
pip3 install -r requirements.txt

# Executar script de configuração
echo "🔧 Iniciando configuração..."
python3 scripts/setup_evolution.py

echo "✅ Configuração concluída!"
echo "📚 Consulte docs/EVOLUTION_API_SETUP.md para mais informações"