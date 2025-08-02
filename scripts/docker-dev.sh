#!/bin/bash

# Script de conveniência para desenvolvimento com Docker
# Facilita o uso do docker-compose com PostgreSQL

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    print_error "Docker não está rodando. Por favor, inicie o Docker Desktop."
    exit 1
fi

# Verificar se docker-compose está disponível
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose não encontrado. Por favor, instale o Docker Compose."
    exit 1
fi

# Definir arquivos do docker-compose
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.postgres.yml"

# Função para mostrar ajuda
show_help() {
    echo "🐳 Ali API - Docker Development Helper"
    echo ""
    echo "Uso: $0 [COMANDO] [OPÇÕES]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  up          Iniciar todos os serviços (app + postgres)"
    echo "  up-admin    Iniciar com pgAdmin incluído"
    echo "  down        Parar todos os serviços"
    echo "  restart     Reiniciar todos os serviços"
    echo "  logs        Mostrar logs em tempo real"
    echo "  build       Rebuild da aplicação"
    echo "  shell       Abrir shell na aplicação"
    echo "  db-shell    Conectar ao PostgreSQL"
    echo "  test        Executar testes"
    echo "  migrate     Executar migrações do banco"
    echo "  status      Mostrar status dos serviços"
    echo "  clean       Limpar containers e volumes"
    echo "  help        Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 up                 # Iniciar app + postgres"
    echo "  $0 up-admin          # Iniciar app + postgres + pgAdmin"
    echo "  $0 logs app          # Ver logs apenas da aplicação"
    echo "  $0 shell             # Abrir bash na aplicação"
}

# Verificar se arquivo .env existe
check_env_file() {
    if [[ ! -f ".env.development" ]]; then
        print_warning "Arquivo .env.development não encontrado."
        print_info "Copiando .env.example para .env.development..."
        cp .env.example .env.development
        print_warning "Por favor, edite .env.development com suas configurações antes de continuar."
        print_info "Variáveis obrigatórias: LLM_API_KEY, JWT_SECRET_KEY"
        return 1
    fi
}

# Função principal
main() {
    case "${1:-help}" in
        "up")
            print_info "Iniciando Ali API com PostgreSQL..."
            check_env_file || exit 1
            docker-compose $COMPOSE_FILES up -d
            print_success "Serviços iniciados!"
            print_info "Aplicação: http://localhost:8000"
            print_info "Health Check: http://localhost:8000/health"
            print_info "Docs: http://localhost:8000/docs"
            ;;
        "up-admin")
            print_info "Iniciando Ali API com PostgreSQL e pgAdmin..."
            check_env_file || exit 1
            docker-compose $COMPOSE_FILES --profile admin up -d
            print_success "Serviços iniciados com pgAdmin!"
            print_info "Aplicação: http://localhost:8000"
            print_info "pgAdmin: http://localhost:5050 (admin@ali.com / admin123)"
            ;;
        "down")
            print_info "Parando todos os serviços..."
            docker-compose $COMPOSE_FILES --profile admin down
            print_success "Serviços parados!"
            ;;
        "restart")
            print_info "Reiniciando serviços..."
            docker-compose $COMPOSE_FILES restart
            print_success "Serviços reiniciados!"
            ;;
        "logs")
            if [[ -n "$2" ]]; then
                docker-compose $COMPOSE_FILES logs -f "$2"
            else
                docker-compose $COMPOSE_FILES logs -f
            fi
            ;;
        "build")
            print_info "Rebuilding aplicação..."
            docker-compose $COMPOSE_FILES build app
            print_success "Build concluído!"
            ;;
        "shell")
            print_info "Abrindo shell na aplicação..."
            docker-compose $COMPOSE_FILES exec app bash
            ;;
        "db-shell")
            print_info "Conectando ao PostgreSQL..."
            docker-compose $COMPOSE_FILES exec postgres psql -U ali_user -d ali_db
            ;;
        "test")
            print_info "Executando testes..."
            docker-compose $COMPOSE_FILES exec app uv run pytest "${@:2}"
            ;;
        "migrate")
            print_info "Executando migrações..."
            docker-compose $COMPOSE_FILES exec app uv run alembic upgrade head
            print_success "Migrações executadas!"
            ;;
        "status")
            print_info "Status dos serviços:"
            docker-compose $COMPOSE_FILES ps
            echo ""
            print_info "Health checks:"
            echo "Aplicação:"
            curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "  Não disponível"
            echo "PostgreSQL:"
            docker-compose $COMPOSE_FILES exec postgres pg_isready -U ali_user 2>/dev/null || echo "  Não disponível"
            ;;
        "clean")
            print_warning "Isso irá remover todos os containers e volumes. Dados do banco serão perdidos!"
            read -p "Continuar? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_info "Limpando containers e volumes..."
                docker-compose $COMPOSE_FILES --profile admin down -v
                docker system prune -f
                print_success "Limpeza concluída!"
            else
                print_info "Operação cancelada."
            fi
            ;;
        "help")
            show_help
            ;;
        *)
            print_error "Comando desconhecido: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Executar função principal
main "$@"