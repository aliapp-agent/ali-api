#!/usr/bin/env python3
"""
Script para configurar automaticamente a integração WhatsApp via Evolution API.

Este script:
1. Valida configurações necessárias
2. Cria instância na Evolution API
3. Configura webhook
4. Testa a conexão
5. Fornece QR Code para conectar WhatsApp

Uso:
    python scripts/setup_whatsapp.py
    python scripts/setup_whatsapp.py --instance-name minha-instancia
    python scripts/setup_whatsapp.py --reset  # Recria instância
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


class Colors:
    """Cores para output no terminal."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class WhatsAppSetup:
    """Classe para configurar WhatsApp via Evolution API."""

    def __init__(self, instance_name: Optional[str] = None):
        """Inicializa o setup."""
        self.instance_name = instance_name or os.getenv('EVOLUTION_INSTANCE', 'ali-api-instance')
        self.api_url = os.getenv('EVOLUTION_API_URL', '').rstrip('/')
        self.api_key = os.getenv('EVOLUTION_API_KEY', '')
        self.webhook_base_url = os.getenv('APP_BASE_URL', 'http://localhost:8000')

        # Configurações
        self.webhook_url = f"{self.webhook_base_url}/api/v1/whatsapp/webhook/evolution"
        self.timeout = 30

        # Headers para requisições
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key
        }

    def print_status(self, message: str, status: str = "info"):
        """Imprime mensagem com cor baseada no status."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if status == "success":
            print(f"{Colors.GREEN}✓ [{timestamp}] {message}{Colors.END}")
        elif status == "error":
            print(f"{Colors.RED}✗ [{timestamp}] {message}{Colors.END}")
        elif status == "warning":
            print(f"{Colors.YELLOW}⚠ [{timestamp}] {message}{Colors.END}")
        elif status == "info":
            print(f"{Colors.BLUE}ℹ [{timestamp}] {message}{Colors.END}")
        elif status == "step":
            print(f"{Colors.PURPLE}{Colors.BOLD}➤ [{timestamp}] {message}{Colors.END}")
        else:
            print(f"[{timestamp}] {message}")

    def print_header(self, title: str):
        """Imprime cabeçalho."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
        print(f" {title}")
        print(f"{'='*60}{Colors.END}\n")

    def validate_config(self) -> bool:
        """Valida configurações necessárias."""
        self.print_step("Validando configurações...")

        errors = []

        if not self.api_url:
            errors.append("EVOLUTION_API_URL não configurada")

        if not self.api_key:
            errors.append("EVOLUTION_API_KEY não configurada")

        if not self.instance_name:
            errors.append("Nome da instância não fornecido")

        # Validar URL base da aplicação
        if self.webhook_base_url == 'http://localhost:8000':
            self.print_status(
                "Usando URL local para webhook. Em produção, configure APP_BASE_URL",
                "warning"
            )

        if errors:
            self.print_status("Erros de configuração encontrados:", "error")
            for error in errors:
                print(f"  - {error}")
            return False

        self.print_status("Configurações válidas", "success")
        return True

    def print_step(self, message: str):
        """Imprime passo atual."""
        self.print_status(message, "step")

    def test_evolution_api(self) -> bool:
        """Testa conectividade com Evolution API."""
        self.print_step("Testando conectividade com Evolution API...")

        try:
            response = requests.get(
                f"{self.api_url}/information",
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                api_info = response.json()
                self.print_status(
                    f"Evolution API conectada: {api_info.get('version', 'N/A')}",
                    "success"
                )
                return True
            else:
                self.print_status(
                    f"Erro ao conectar Evolution API: {response.status_code}",
                    "error"
                )
                return False

        except requests.exceptions.ConnectionError:
            self.print_status("Não foi possível conectar à Evolution API", "error")
            return False
        except Exception as e:
            self.print_status(f"Erro inesperado: {str(e)}", "error")
            return False

    def check_instance_exists(self) -> bool:
        """Verifica se a instância já existe."""
        self.print_step("Verificando se instância já existe...")

        try:
            response = requests.get(
                f"{self.api_url}/instance/fetch-instances",
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                instances = response.json()

                for instance in instances:
                    if instance.get('instance', {}).get('instanceName') == self.instance_name:
                        self.print_status(f"Instância '{self.instance_name}' já existe", "warning")
                        return True

                self.print_status(f"Instância '{self.instance_name}' não existe", "info")
                return False
            else:
                self.print_status(f"Erro ao buscar instâncias: {response.status_code}", "error")
                return False

        except Exception as e:
            self.print_status(f"Erro ao verificar instâncias: {str(e)}", "error")
            return False

    def delete_instance(self) -> bool:
        """Deleta instância existente."""
        self.print_step(f"Deletando instância '{self.instance_name}'...")

        try:
            response = requests.delete(
                f"{self.api_url}/instance/delete/{self.instance_name}",
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code in [200, 404]:
                self.print_status("Instância deletada com sucesso", "success")
                return True
            else:
                self.print_status(f"Erro ao deletar instância: {response.status_code}", "error")
                return False

        except Exception as e:
            self.print_status(f"Erro ao deletar instância: {str(e)}", "error")
            return False

    def create_instance(self) -> bool:
        """Cria nova instância na Evolution API."""
        self.print_step(f"Criando instância '{self.instance_name}'...")

        payload = {
            "instanceName": self.instance_name,
            "webhook": {
                "url": self.webhook_url,
                "events": [
                    "MESSAGES_UPSERT",
                    "CONNECTION_UPDATE",
                    "QRCODE_UPDATED"
                ]
            }
        }

        try:
            response = requests.post(
                f"{self.api_url}/instance/create",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 201:
                result = response.json()
                self.print_status("Instância criada com sucesso", "success")

                # Mostrar detalhes
                if 'instance' in result:
                    instance_info = result['instance']
                    print(f"  - Nome: {instance_info.get('instanceName')}")
                    print(f"  - Status: {instance_info.get('status')}")

                return True
            else:
                self.print_status(f"Erro ao criar instância: {response.status_code}", "error")
                try:
                    error_detail = response.json()
                    print(f"  Detalhes: {error_detail}")
                except:
                    print(f"  Resposta: {response.text}")
                return False

        except Exception as e:
            self.print_status(f"Erro ao criar instância: {str(e)}", "error")
            return False

    def configure_webhook(self) -> bool:
        """Configura webhook para a instância."""
        self.print_step("Configurando webhook...")

        payload = {
            "url": self.webhook_url,
            "events": [
                "MESSAGES_UPSERT",
                "CONNECTION_UPDATE",
                "QRCODE_UPDATED"
            ]
        }

        try:
            response = requests.post(
                f"{self.api_url}/webhook/set/{self.instance_name}",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code in [200, 201]:
                self.print_status("Webhook configurado com sucesso", "success")
                print(f"  - URL: {self.webhook_url}")
                return True
            else:
                self.print_status(f"Erro ao configurar webhook: {response.status_code}", "error")
                return False

        except Exception as e:
            self.print_status(f"Erro ao configurar webhook: {str(e)}", "error")
            return False

    def connect_instance(self) -> Optional[str]:
        """Conecta instância e obtém QR code."""
        self.print_step("Conectando instância...")

        try:
            response = requests.get(
                f"{self.api_url}/instance/connect/{self.instance_name}",
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()

                if 'qrcode' in result:
                    qr_code = result['qrcode']
                    self.print_status("QR Code gerado", "success")
                    return qr_code
                else:
                    self.print_status("Instância conectada (já autenticada)", "success")
                    return None
            else:
                self.print_status(f"Erro ao conectar instância: {response.status_code}", "error")
                return None

        except Exception as e:
            self.print_status(f"Erro ao conectar instância: {str(e)}", "error")
            return None

    def check_connection_status(self, max_attempts: int = 30) -> bool:
        """Verifica status da conexão."""
        self.print_step("Verificando status da conexão...")

        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.api_url}/instance/connectionState/{self.instance_name}",
                    headers=self.headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    state = result.get('instance', {}).get('state', 'unknown')

                    if state == 'open':
                        self.print_status("WhatsApp conectado com sucesso!", "success")
                        return True
                    elif state in ['connecting', 'qr']:
                        print(f"  Status: {state} (tentativa {attempt + 1}/{max_attempts})")
                        time.sleep(2)
                    else:
                        self.print_status(f"Status inesperado: {state}", "warning")
                        time.sleep(2)
                else:
                    self.print_status(f"Erro ao verificar status: {response.status_code}", "error")
                    return False

            except Exception as e:
                self.print_status(f"Erro ao verificar status: {str(e)}", "error")
                return False

        self.print_status("Timeout aguardando conexão", "warning")
        return False

    def test_webhook(self) -> bool:
        """Testa se webhook está funcionando."""
        self.print_step("Testando webhook...")

        try:
            # Testar endpoint de teste
            webhook_test_url = f"{self.webhook_base_url}/api/v1/whatsapp/webhook/test"

            response = requests.get(webhook_test_url, timeout=10)

            if response.status_code == 200:
                self.print_status("Webhook está funcionando", "success")
                return True
            else:
                self.print_status(f"Webhook com problema: {response.status_code}", "warning")
                return False

        except requests.exceptions.ConnectionError:
            self.print_status("Não foi possível conectar ao webhook (aplicação não está rodando?)", "warning")
            return False
        except Exception as e:
            self.print_status(f"Erro ao testar webhook: {str(e)}", "error")
            return False

    def print_summary(self, qr_code: Optional[str] = None):
        """Imprime resumo da configuração."""
        self.print_header("RESUMO DA CONFIGURAÇÃO")

        print(f"{Colors.WHITE}Instância:{Colors.END} {self.instance_name}")
        print(f"{Colors.WHITE}Evolution API:{Colors.END} {self.api_url}")
        print(f"{Colors.WHITE}Webhook URL:{Colors.END} {self.webhook_url}")

        if qr_code:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}QR CODE para conectar WhatsApp:")
            print(f"{Colors.WHITE}{qr_code}{Colors.END}")
            print(f"\n{Colors.CYAN}1. Abra o WhatsApp no seu celular")
            print(f"2. Vá em Configurações > Aparelhos conectados")
            print(f"3. Toque em 'Conectar um aparelho'")
            print(f"4. Escaneie o QR Code acima{Colors.END}")

        print(f"\n{Colors.GREEN}{Colors.BOLD}Próximos passos:")
        print(f"{Colors.WHITE}1. Certifique-se de que a aplicação Ali API está rodando")
        print(f"2. Envie uma mensagem WhatsApp para testar")
        print(f"3. Verifique os logs: tail -f logs/app.log{Colors.END}")

        print(f"\n{Colors.PURPLE}{Colors.BOLD}Comandos úteis:")
        print(f"{Colors.WHITE}# Verificar status da instância")
        print(f"curl -H 'apikey: {self.api_key}' {self.api_url}/instance/connectionState/{self.instance_name}")
        print(f"\n# Testar webhook")
        print(f"curl {self.webhook_base_url}/api/v1/whatsapp/webhook/test{Colors.END}")

    def run_setup(self, reset: bool = False) -> bool:
        """Executa to-do o processo de configuração."""
        self.print_header("CONFIGURAÇÃO WHATSAPP VIA EVOLUTION API")

        # 1. Validar configurações
        if not self.validate_config():
            return False

        # 2. Testar Evolution API
        if not self.test_evolution_api():
            return False

        # 3. Verificar/gerenciar instância existente
        instance_exists = self.check_instance_exists()

        if instance_exists and reset:
            if not self.delete_instance():
                return False
            time.sleep(2)  # Aguardar deleção
        elif instance_exists and not reset:
            self.print_status("Use --reset para recriar a instância", "info")

        # 4. Criar instância se necessário
        if reset or not instance_exists:
            if not self.create_instance():
                return False
            time.sleep(2)  # Aguardar criação

        # 5. Configurar webhook
        if not self.configure_webhook():
            return False

        # 6. Testar webhook
        self.test_webhook()

        # 7. Conectar instância
        qr_code = self.connect_instance()

        # 8. Imprimir resumo
        self.print_summary(qr_code)

        # 9. Se tiver QR code, aguardar conexão
        if qr_code:
            print(f"\n{Colors.YELLOW}Aguardando conexão do WhatsApp...{Colors.END}")
            self.check_connection_status()

        return True


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Configurar integração WhatsApp via Evolution API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/setup_whatsapp.py
  python scripts/setup_whatsapp.py --instance-name minha-instancia
  python scripts/setup_whatsapp.py --reset
  python scripts/setup_whatsapp.py --instance-name teste --reset
        """
    )

    parser.add_argument(
        '--instance-name',
        type=str,
        help='Nome da instância WhatsApp (padrão: ali-api-instance)'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Deletar e recriar instância se ela já existir'
    )

    args = parser.parse_args()

    # Criar setup
    setup = WhatsAppSetup(instance_name=args.instance_name)

    try:
        success = setup.run_setup(reset=args.reset)

        if success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Configuração concluída com sucesso!{Colors.END}\n")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ Configuração falhou!{Colors.END}\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Configuração cancelada pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Erro inesperado: {str(e)}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
