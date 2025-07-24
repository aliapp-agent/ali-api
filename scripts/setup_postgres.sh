#!/bin/bash

# Script para configurar PostgreSQL para o projeto Ali API

echo "🔧 Configurando PostgreSQL para Ali API..."

# Verificar se PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL não encontrado. Instalando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install postgresql
        brew services start postgresql
    else
        echo "Por favor, instale PostgreSQL manualmente para seu sistema operacional"
        exit 1
    fi
fi

# Configurar variáveis
DB_NAME="ali_db"
DB_USER="ali_user"
DB_PASSWORD="ali_password"

echo "📊 Criando banco de dados e usuário..."

# Criar usuário e banco de dados
psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
psql postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "✅ PostgreSQL configurado com sucesso!"
echo "📋 Detalhes da configuração:"
echo "   - Banco: $DB_NAME"
echo "   - Usuário: $DB_USER"
echo "   - Senha: $DB_PASSWORD"
echo "   - URL: postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"