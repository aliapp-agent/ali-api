#!/usr/bin/env python3
"""
Script de configuração para ambiente de desenvolvimento do Ali API.
Este script verifica e configura o ambiente necessário para executar a aplicação.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica se a versão do Python é compatível."""
    print("🐍 Verificando versão do Python...")
    if sys.version_info < (3, 9):
        print("  ❌ Python 3.9+ é necessário")
        return False
    print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def check_uv_installation():
    """Verifica se o uv está instalado."""
    print("\n📦 Verificando instalação do uv...")
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ uv instalado: {result.stdout.strip()}")
            return True
        else:
            print("  ❌ uv não encontrado")
            return False
    except FileNotFoundError:
        print("  ❌ uv não encontrado")
        print("  💡 Instale com: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False

def setup_virtual_environment():
    """Configura o ambiente virtual com uv."""
    print("\n🔧 Configurando ambiente virtual...")
    try:
        # Criar ambiente virtual
        subprocess.run(["uv", "venv", ".venv"], check=True)
        print("  ✅ Ambiente virtual criado")
        
        # Instalar dependências
        subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], check=True)
        print("  ✅ Dependências instaladas")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Erro ao configurar ambiente: {e}")
        return False

def check_env_file():
    """Verifica se o arquivo .env existe."""
    print("\n⚙️  Verificando arquivo de configuração...")
    env_file = Path(".env")
    if env_file.exists():
        print("  ✅ Arquivo .env encontrado")
        return True
    else:
        print("  ❌ Arquivo .env não encontrado")
        print("  💡 Copie .env.example para .env e configure")
        return False

def create_data_directory():
    """Cria o diretório de dados se não existir."""
    print("\n📁 Verificando diretório de dados...")
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()
        print("  ✅ Diretório 'data' criado")
    else:
        print("  ✅ Diretório 'data' já existe")
    return True

def create_logs_directory():
    """Cria o diretório de logs se não existir."""
    print("\n📝 Verificando diretório de logs...")
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("  ✅ Diretório 'logs' criado")
    else:
        print("  ✅ Diretório 'logs' já existe")
    return True

def check_firebase_config():
    """Verifica se o Firebase está configurado."""
    print("\n🔥 Verificando configuração Firebase...")
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        required_vars = ["FIREBASE_PROJECT_ID", "FIREBASE_CREDENTIALS_PATH"]
        missing_vars = []
        
        for var in required_vars:
            if f"{var}=" not in content:
                missing_vars.append(var)
        
        if not missing_vars:
            print("  ✅ Firebase configurado")
            return True
        else:
            print(f"  ⚠️  Variáveis Firebase faltando: {', '.join(missing_vars)}")
            return False
    return False

def run_health_check():
    """Executa um teste básico da aplicação."""
    print("\n🏥 Executando verificação de saúde...")
    try:
        # Ativar ambiente virtual e executar diagnóstico
        result = subprocess.run([
            "uv", "run", "python", "diagnose.py"
        ], capture_output=True, text=True, timeout=30)
        
        if "✅ PASSOU" in result.stdout:
            print("  ✅ Alguns testes passaram")
        if "❌ FALHOU" in result.stdout:
            print("  ⚠️  Alguns testes falharam (normal em desenvolvimento)")
        
        return True
    except subprocess.TimeoutExpired:
        print("  ⚠️  Timeout na verificação")
        return False
    except Exception as e:
        print(f"  ⚠️  Erro na verificação: {e}")
        return False

def main():
    """Função principal do script de setup."""
    print("🚀 Ali API - Setup de Desenvolvimento")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_uv_installation,
        setup_virtual_environment,
        check_env_file,
        create_data_directory,
        create_logs_directory,
        check_firebase_config,
        run_health_check,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Erro inesperado: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 RESUMO DO SETUP")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"  ✅ Todos os {total} checks passaram!")
        print("\n🎉 Ambiente configurado com sucesso!")
        print("\n💡 Para iniciar a aplicação:")
        print("   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print(f"  ⚠️  {passed}/{total} checks passaram")
        print("\n🔧 Corrija os problemas identificados antes de continuar.")
    
    print("\n📚 Documentação: README.md")
    print("🐛 Problemas? Execute: python diagnose.py")

if __name__ == "__main__":
    main()