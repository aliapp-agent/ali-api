#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas no backend da API Ali.

Este script verifica:
1. Configurações de ambiente
2. Conexão com Firebase
3. Serviços de banco de dados
4. Configuração JWT
5. Dependências críticas
"""

import os
import sys
import asyncio
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))


def check_environment_variables():
    """Verifica se as variáveis de ambiente necessárias estão definidas."""
    print("\n🔍 Verificando variáveis de ambiente...")

    required_vars = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_CREDENTIALS_PATH",
        "FIREBASE_STORAGE_BUCKET",
        "JWT_SECRET_KEY",
        "APP_ENV"
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var in ["JWT_SECRET_KEY", "FIREBASE_CREDENTIALS_PATH"]:
                print(f"  ✅ {var}: ***")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NÃO DEFINIDA")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n⚠️  Variáveis faltando: {', '.join(missing_vars)}")
        return False

    print("\n✅ Todas as variáveis de ambiente estão definidas")
    return True


def check_firebase_credentials():
    """Verifica se o arquivo de credenciais do Firebase existe."""
    print("\n🔍 Verificando credenciais do Firebase...")

    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not creds_path:
        print("  ❌ FIREBASE_CREDENTIALS_PATH não definida")
        return False

    if not os.path.exists(creds_path):
        print(f"  ❌ Arquivo de credenciais não encontrado: {creds_path}")
        return False

    print(f"  ✅ Arquivo de credenciais encontrado: {creds_path}")
    return True


async def test_firebase_connection():
    """Testa a conexão com o Firebase."""
    print("\n🔍 Testando conexão com Firebase...")

    try:
        from app.core.firebase import get_firestore, firebase_config

        # Verificar se o app Firebase foi inicializado
        if firebase_config._app:
            print(f"  ✅ Firebase app inicializado: {firebase_config._app.project_id}")
        else:
            print("  ❌ Firebase app não inicializado")
            return False

        # Testar conexão com Firestore
        db = get_firestore()
        if db:
            print("  ✅ Cliente Firestore criado")

            # Tentar uma operação simples
            try:
                collections = list(db.collections())
                print(f"  ✅ Firestore acessível ({len(collections)} coleções encontradas)")
                return True
            except Exception as e:
                print(f"  ❌ Erro ao acessar Firestore: {e}")
                return False
        else:
            print("  ❌ Falha ao criar cliente Firestore")
            return False

    except Exception as e:
        print(f"  ❌ Erro na conexão Firebase: {e}")
        return False


async def test_database_service():
    """Testa o serviço de banco de dados."""
    print("\n🔍 Testando DatabaseService...")

    try:
        from app.services.database import DatabaseService

        db_service = DatabaseService()
        print("  ✅ DatabaseService instanciado")

        # Testar health check
        health = await db_service.health_check()
        if health:
            print("  ✅ DatabaseService health check passou")
            return True
        else:
            print("  ❌ DatabaseService health check falhou")
            return False

    except Exception as e:
        print(f"  ❌ Erro no DatabaseService: {e}")
        return False


def test_jwt_configuration():
    """Testa a configuração JWT."""
    print("\n🔍 Testando configuração JWT...")

    try:
        from app.shared.utils.auth import create_access_token

        # Tentar criar um token de teste
        test_token = create_access_token(session_id="test_session")
        if test_token and test_token.access_token:
            print("  ✅ Token JWT criado com sucesso")
            return True
        else:
            print("  ❌ Falha ao criar token JWT")
            return False

    except Exception as e:
        print(f"  ❌ Erro na configuração JWT: {e}")
        return False


def test_imports():
    """Testa se todas as importações críticas funcionam."""
    print("\n🔍 Testando importações críticas...")

    critical_imports = [
        ("app.core.config", "settings"),
        ("app.core.firebase", "get_firestore"),
        ("app.services.database", "DatabaseService"),
        ("app.shared.utils.auth", "create_access_token"),
        ("app.api.v1.auth", "router"),
    ]

    failed_imports = []

    for module_name, item_name in critical_imports:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print(f"  ✅ {module_name}.{item_name}")
        except Exception as e:
            print(f"  ❌ {module_name}.{item_name}: {e}")
            failed_imports.append(f"{module_name}.{item_name}")

    if failed_imports:
        print(f"\n⚠️  Importações falharam: {', '.join(failed_imports)}")
        return False

    print("\n✅ Todas as importações críticas funcionaram")
    return True


async def main():
    """Executa todos os testes de diagnóstico."""
    print("🚀 Iniciando diagnóstico do backend Ali API...")
    print("=" * 50)

    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()

    results = {
        "environment_vars": check_environment_variables(),
        "firebase_credentials": check_firebase_credentials(),
        "imports": test_imports(),
        "firebase_connection": await test_firebase_connection(),
        "database_service": await test_database_service(),
        "jwt_config": test_jwt_configuration(),
    }

    print("\n" + "=" * 50)
    print("📊 RESUMO DO DIAGNÓSTICO")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("O problema pode estar na configuração de produção ou deployment.")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM!")
        print("Corrija os problemas identificados antes do deployment.")

    print("\n💡 PRÓXIMOS PASSOS:")
    if not results["environment_vars"]:
        print("  1. Configure as variáveis de ambiente faltando")
    if not results["firebase_credentials"]:
        print("  2. Verifique o arquivo de credenciais do Firebase")
    if not results["firebase_connection"]:
        print("  3. Teste a conectividade com Firebase/Firestore")
    if not results["database_service"]:
        print("  4. Verifique a implementação do DatabaseService")
    if not results["jwt_config"]:
        print("  5. Configure a chave secreta JWT")

    print("\n🔧 Para testar em produção:")
    print("  curl https://ali-api-production-459480858531.us-central1.run.app/api/v1/health/detailed")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
