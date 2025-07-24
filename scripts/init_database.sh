#!/bin/bash

# Script completo para inicializar o banco de dados

echo "🚀 Inicializando banco de dados Ali API..."

# Executar setup do PostgreSQL
./scripts/setup_postgres.sh

# Remover migração vazia
rm -f alembic/versions/21582096e6c1_primeira.py

# Gerar nova migração baseada nos modelos
echo "📝 Gerando migração inicial..."
alembic revision --autogenerate -m "Create initial tables"

# Executar migrações
echo "⬆️ Executando migrações..."
alembic upgrade head

echo "✅ Banco de dados inicializado com sucesso!"
echo "🔗 Você pode conectar em: postgresql://ali_user:ali_password@localhost:5432/ali_db"