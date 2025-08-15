#!/usr/bin/env python3
"""
Script para configuração automatizada do Evolution API.

Este script facilita a instalação e configuração inicial do Evolution API
para integração com o Ali API.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


class EvolutionAPISetup:
    """Classe para configuração do Evolution API."""

    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.instance_name = "ali-api-whatsapp"
        self.api_key = None
        self.docker_compose_path = Path("docker-compose-evolution.yml")

    def check_dependencies(self) -> bool:
        """Verifica se as dependências estão instaladas."""
        console.print("🔍 Verificando dependências...", style="blue")
        
        dependencies = {
            "docker": "Docker não encontrado. Instale: https://docs.docker.com/get-docker/",
            "docker-compose": "Docker Compose não encontrado. Instale: https://docs.docker.com/compose/install/"
        }
        
        for cmd, error_msg in dependencies.items():
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    console.print(f"❌ {error_msg}", style="red")
                    return False
                console.print(f"✅ {cmd} encontrado", style="green")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                console.print(f"❌ {error_msg}", style="red")
                return False
        
        return True

    def create_docker_compose(self) -> None:
        """Cria o arquivo docker-compose para Evolution API."""
        console.print("📝 Criando docker-compose.yml...", style="blue")
        
        compose_content = """
version: '3.8'

services:
  evolution-api:
    image: atendai/evolution-api:v2.1.1
    container_name: evolution-api
    restart: always
    ports:
      - "8080:8080"
    environment:
      # Servidor
      - SERVER_TYPE=http
      - SERVER_PORT=8080
      - SERVER_URL=http://localhost:8080
      
      # CORS
      - CORS_ORIGIN=*
      - CORS_METHODS=GET,POST,PUT,DELETE
      - CORS_CREDENTIALS=true
      
      # Logs
      - LOG_LEVEL=ERROR,WARN,DEBUG,INFO,LOG
      - LOG_COLOR=true
      - LOG_BAILEYS=error
      
      # Instâncias
      - DEL_INSTANCE=false
      
      # Banco de dados
      - DATABASE_ENABLED=false
      
      # Telemetria
      - TELEMETRY=false
    volumes:
      - evolution_instances:/evolution/instances
      - evolution_store:/evolution/store
    networks:
      - evolution-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  evolution_instances:
  evolution_store:

networks:
  evolution-network:
    driver: bridge
"""
        
        with open(self.docker_compose_path, 'w') as f:
            f.write(compose_content.strip())
        
        console.print(f"✅ Arquivo {self.docker_compose_path} criado", style="green")

    def start_evolution_api(self) -> bool:
        """Inicia o Evolution API via Docker Compose."""
        console.print("🚀 Iniciando Evolution API...", style="blue")
        
        try:
            # Parar containers existentes
            subprocess.run(["docker-compose", "-f", str(self.docker_compose_path), "down"], 
                         capture_output=True)
            
            # Iniciar novo container
            result = subprocess.run(
                ["docker-compose", "-f", str(self.docker_compose_path), "up", "-d"],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                console.print(f"❌ Erro ao iniciar: {result.stderr}", style="red")
                return False
            
            console.print("✅ Evolution API iniciado", style="green")
            return True
            
        except Exception as e:
            console.print(f"❌ Erro: {e}", style="red")
            return False

    def wait_for_api(self, timeout: int = 60) -> bool:
        """Aguarda a API ficar disponível."""
        console.print("⏳ Aguardando API ficar disponível...", style="yellow")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Conectando...", total=timeout)
            
            for i in range(timeout):
                try:
                    response = requests.get(f"{self.base_url}", timeout=5)
                    if response.status_code == 200:
                        console.print("✅ API disponível!", style="green")
                        return True
                except requests.RequestException:
                    pass
                
                time.sleep(1)
                progress.update(task, advance=1)
        
        console.print("❌ Timeout aguardando API", style="red")
        return False

    def generate_api_key(self) -> str:
        """Gera uma chave API segura."""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))

    def create_instance(self) -> bool:
        """Cria uma instância WhatsApp."""
        console.print("📱 Criando instância WhatsApp...", style="blue")
        
        self.api_key = self.generate_api_key()
        
        payload = {
            "instanceName": self.instance_name,
            "token": self.api_key,
            "qrcode": True,
            "webhook": {
                "url": "http://localhost:8000/api/v1/whatsapp/webhook/evolution",
                "events": [
                    "MESSAGES_UPSERT",
                    "CONNECTION_UPDATE",
                    "QRCODE_UPDATED"
                ]
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/instance/create",
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                console.print("✅ Instância criada com sucesso!", style="green")
                return True
            else:
                console.print(f"❌ Erro ao criar instância: {response.text}", style="red")
                return False
                
        except requests.RequestException as e:
            console.print(f"❌ Erro de conexão: {e}", style="red")
            return False

    def connect_whatsapp(self) -> bool:
        """Conecta ao WhatsApp e exibe QR Code."""
        console.print("🔗 Conectando ao WhatsApp...", style="blue")
        
        try:
            response = requests.get(
                f"{self.base_url}/instance/connect/{self.instance_name}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'qrcode' in data:
                    console.print("\n📱 QR Code gerado! Escaneie com seu WhatsApp:", style="green")
                    console.print(f"\n{data['qrcode']['code']}\n", style="cyan")
                    
                    # Aguardar conexão
                    console.print("⏳ Aguardando conexão...", style="yellow")
                    
                    for i in range(60):  # 60 segundos timeout
                        status = self.check_connection_status()
                        if status == "open":
                            console.print("✅ WhatsApp conectado com sucesso!", style="green")
                            return True
                        elif status == "close":
                            console.print("❌ Conexão falhou", style="red")
                            return False
                        
                        time.sleep(1)
                    
                    console.print("⏰ Timeout - tente novamente", style="yellow")
                    return False
                else:
                    console.print("❌ QR Code não encontrado na resposta", style="red")
                    return False
            else:
                console.print(f"❌ Erro ao conectar: {response.text}", style="red")
                return False
                
        except requests.RequestException as e:
            console.print(f"❌ Erro de conexão: {e}", style="red")
            return False

    def check_connection_status(self) -> Optional[str]:
        """Verifica o status da conexão."""
        try:
            response = requests.get(
                f"{self.base_url}/instance/connectionState/{self.instance_name}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('instance', {}).get('state')
            
        except requests.RequestException:
            pass
        
        return None

    def configure_webhook(self) -> bool:
        """Configura webhook para a instância."""
        console.print("🔗 Configurando webhook...", style="blue")
        
        payload = {
            "url": "http://localhost:8000/api/v1/whatsapp/webhook/evolution",
            "events": [
                "MESSAGES_UPSERT",
                "CONNECTION_UPDATE",
                "QRCODE_UPDATED"
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/webhook/set/{self.instance_name}",
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                console.print("✅ Webhook configurado com sucesso!", style="green")
                return True
            else:
                console.print(f"❌ Erro ao configurar webhook: {response.text}", style="red")
                return False
                
        except requests.RequestException as e:
            console.print(f"❌ Erro de conexão: {e}", style="red")
            return False

    def update_ali_api_env(self) -> None:
        """Atualiza o arquivo .env do Ali API."""
        console.print("📝 Atualizando configurações do Ali API...", style="blue")
        
        env_path = Path(".env")
        env_example_path = Path(".env.example")
        
        # Configurações do Evolution API
        evolution_config = {
            "EVOLUTION_API_URL": self.base_url,
            "EVOLUTION_INSTANCE": self.instance_name,
            "EVOLUTION_API_KEY": self.api_key or "your-api-key-here"
        }
        
        # Ler arquivo .env existente ou criar novo
        env_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
        elif env_example_path.exists():
            with open(env_example_path, 'r') as f:
                env_content = f.read()
        
        # Atualizar ou adicionar configurações
        lines = env_content.split('\n')
        updated_lines = []
        updated_keys = set()
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in evolution_config:
                    updated_lines.append(f"{key}={evolution_config[key]}")
                    updated_keys.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Adicionar configurações não encontradas
        for key, value in evolution_config.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}")
        
        # Salvar arquivo .env
        with open(env_path, 'w') as f:
            f.write('\n'.join(updated_lines))
        
        console.print("✅ Arquivo .env atualizado", style="green")

    def test_integration(self) -> bool:
        """Testa a integração com o Ali API."""
        console.print("🧪 Testando integração...", style="blue")
        
        # Verificar se o Ali API está rodando
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
            if response.status_code != 200:
                console.print("⚠️  Ali API não está rodando em localhost:8000", style="yellow")
                return False
        except requests.RequestException:
            console.print("⚠️  Ali API não está acessível", style="yellow")
            return False
        
        # Testar envio de mensagem (opcional)
        if Confirm.ask("Deseja testar o envio de uma mensagem?"):
            phone = Prompt.ask("Digite o número (com código do país, ex: 5511999999999)")
            
            payload = {
                "number": phone,
                "text": "🤖 Teste do Ali API - Evolution API funcionando!"
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/message/sendText/{self.instance_name}",
                    json=payload,
                    headers={"apikey": self.api_key},
                    timeout=30
                )
                
                if response.status_code == 200:
                    console.print("✅ Mensagem enviada com sucesso!", style="green")
                    return True
                else:
                    console.print(f"❌ Erro ao enviar mensagem: {response.text}", style="red")
                    return False
                    
            except requests.RequestException as e:
                console.print(f"❌ Erro de conexão: {e}", style="red")
                return False
        
        return True

    def show_summary(self) -> None:
        """Exibe resumo da configuração."""
        table = Table(title="📋 Resumo da Configuração")
        table.add_column("Configuração", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Evolution API URL", self.base_url)
        table.add_row("Instância WhatsApp", self.instance_name)
        table.add_row("API Key", self.api_key or "Não gerada")
        table.add_row("Status", "✅ Configurado" if self.api_key else "❌ Não configurado")
        
        console.print(table)
        
        console.print("\n📚 Próximos passos:", style="bold blue")
        console.print("1. Verifique se o Ali API está rodando")
        console.print("2. Teste o envio de mensagens via API")
        console.print("3. Configure webhooks para receber mensagens")
        console.print("4. Monitore os logs regularmente")
        
        console.print("\n🔗 Links úteis:", style="bold blue")
        console.print(f"• Evolution API: {self.base_url}")
        console.print("• Documentação: https://doc.evolution-api.com/")
        console.print("• Ali API Health: http://localhost:8000/api/v1/health")

    def run(self) -> None:
        """Executa o processo completo de configuração."""
        console.print(Panel.fit(
            "🚀 Configuração do Evolution API para Ali API",
            style="bold blue"
        ))
        
        steps = [
            ("Verificar dependências", self.check_dependencies),
            ("Criar docker-compose", self.create_docker_compose),
            ("Iniciar Evolution API", self.start_evolution_api),
            ("Aguardar API", self.wait_for_api),
            ("Gerar API key", self.generate_api_key),
            ("Criar instância", self.create_instance),
            ("Conectar WhatsApp", self.connect_whatsapp),
            ("Configurar webhook", self.configure_webhook),
            ("Atualizar .env", lambda: (self.update_ali_api_env(), True)[1]),
            ("Testar integração", self.test_integration),
        ]
        
        for step_name, step_func in steps:
            console.print(f"\n🔄 {step_name}...", style="bold")
            
            try:
                if not step_func():
                    console.print(f"❌ Falha em: {step_name}", style="red")
                    if not Confirm.ask("Continuar mesmo assim?"):
                        return
            except Exception as e:
                console.print(f"❌ Erro em {step_name}: {e}", style="red")
                if not Confirm.ask("Continuar mesmo assim?"):
                    return
        
        console.print("\n🎉 Configuração concluída!", style="bold green")
        self.show_summary()


def main():
    """Função principal."""
    try:
        setup = EvolutionAPISetup()
        setup.run()
    except KeyboardInterrupt:
        console.print("\n⚠️  Configuração cancelada pelo usuário", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Erro inesperado: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()