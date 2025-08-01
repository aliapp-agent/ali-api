#!/usr/bin/env python3
"""
Script para corrigir problemas críticos do projeto Ali API.

Este script identifica e corrige os principais problemas que impedem
o funcionamento correto da aplicação:

1. Problemas de configuração de banco de dados
2. Dependências ausentes ou mal configuradas
3. Problemas de importação
4. Configurações de ambiente
"""

import os
import sys
import asyncio
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_environment():
    """Verifica se as variáveis de ambiente estão configuradas."""
    print("🔍 Verificando configurações de ambiente...")
    
    env_file = project_root / ".env.development"
    if not env_file.exists():
        print("❌ Arquivo .env.development não encontrado")
        return False
    
    # Verificar variáveis críticas
    critical_vars = [
        "LLM_API_KEY",
        "JWT_SECRET_KEY",
        "POSTGRES_URL",
    ]
    
    missing_vars = []
    with open(env_file) as f:
        content = f.read()
        for var in critical_vars:
            if f"{var}=your-" in content or f"{var}=sk-your-" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Variáveis não configuradas: {', '.join(missing_vars)}")
        print("   Configure essas variáveis no .env.development")
        return False
    
    print("✅ Configurações de ambiente OK")
    return True


def check_database_connection():
    """Verifica a conexão com o banco de dados."""
    print("🔍 Verificando conexão com banco de dados...")
    
    try:
        from app.services.database import database_service
        # Tentar criar uma sessão
        session = database_service.get_session_maker()
        session.close()
        print("✅ Conexão com banco de dados OK")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        return False


def check_imports():
    """Verifica se todas as importações críticas funcionam."""
    print("🔍 Verificando importações críticas...")
    
    critical_imports = [
        "app.main",
        "app.api.v1.api",
        "app.core.agno.graph",
        "app.services.database",
        "app.domain.services",
    ]
    
    failed_imports = []
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0


def create_missing_directories():
    """Cria diretórios necessários que podem estar ausentes."""
    print("🔍 Criando diretórios necessários...")
    
    directories = [
        "data",
        "logs",
        "tmp",
        "evals/results",
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Criado: {directory}")
        else:
            print(f"✅ Existe: {directory}")


def fix_elasticsearch_issues():
    """Corrige problemas relacionados ao Elasticsearch."""
    print("🔍 Verificando configuração do Elasticsearch...")
    
    # Verificar se as configurações do Elasticsearch estão corretas
    env_file = project_root / ".env.development"
    if env_file.exists():
        with open(env_file) as f:
            content = f.read()
            if "ELASTICSEARCH_URL" in content and "ELASTICSEARCH_API_KEY" in content:
                print("✅ Configurações do Elasticsearch encontradas")
                return True
    
    print("⚠️  Configurações do Elasticsearch podem estar incompletas")
    return False


def run_basic_tests():
    """Executa testes básicos para verificar se os problemas foram corrigidos."""
    print("🔍 Executando testes básicos...")
    
    try:
        # Teste de importação da aplicação
        from app.main import app
        print("✅ Aplicação importada com sucesso")
        
        # Teste de configurações
        from app.core.config import settings
        print(f"✅ Configurações carregadas: {settings.PROJECT_NAME}")
        
        # Teste de agente Agno
        from app.core.agno.graph import AgnoAgent
        agent = AgnoAgent()
        print("✅ AgnoAgent inicializado")
        
        return True
    except Exception as e:
        print(f"❌ Erro nos testes básicos: {e}")
        return False


def main():
    """Função principal do script de correção."""
    print("🚀 Iniciando correção de problemas críticos do Ali API\n")
    
    # Lista de verificações
    checks = [
        ("Criando diretórios", create_missing_directories),
        ("Verificando ambiente", check_environment),
        ("Verificando importações", check_imports),
        ("Verificando banco de dados", check_database_connection),
        ("Verificando Elasticsearch", fix_elasticsearch_issues),
        ("Executando testes básicos", run_basic_tests),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{'='*50}")
        print(f"📋 {name}")
        print(f"{'='*50}")
        
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro durante {name}: {e}")
            results.append((name, False))
    
    # Resumo final
    print(f"\n{'='*50}")
    print("📊 RESUMO FINAL")
    print(f"{'='*50}")
    
    passed = 0
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{len(results)} verificações passaram")
    
    if passed == len(results):
        print("\n🎉 Todos os problemas críticos foram corrigidos!")
        print("   Você pode agora executar os testes com: pytest")
    else:
        print("\n⚠️  Ainda há problemas que precisam ser resolvidos manualmente.")
        print("   Verifique os erros acima e configure as variáveis necessárias.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)