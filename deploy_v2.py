#!/usr/bin/env python3
"""
Script de Deploy para CloudDataOrchestrator v2.0
Automatiza o processo de deploy com Docker e verificação de saúde
"""

import os
import sys
import subprocess
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional


class DeployManager:
    """Gerenciador de deploy para CloudDataOrchestrator v2.0"""
    
    def __init__(self):
        self.project_name = "CloudDataOrchestrator"
        self.version = "2.0.0"
        self.services = [
            "dashboard",
            "data-pipeline", 
            "alerts",
            "ml-service"
        ]
        
        # Configurações de deploy
        self.docker_compose_file = "docker-compose.yml"
        self.env_file = ".env"
        self.health_check_url = "http://localhost:8501/_stcore/health"
        
        # Status do deploy
        self.deploy_status = {
            "start_time": None,
            "end_time": None,
            "services_status": {},
            "health_checks": {},
            "errors": []
        }
    
    def run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Executa um comando do sistema"""
        print(f"🔄 Executando: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                print(f"✅ Saída: {result.stdout.strip()}")
            
            if result.stderr:
                print(f"⚠️ Erro: {result.stderr.strip()}")
            
            return result
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao executar comando: {e}")
            if check:
                raise
            return e
    
    def check_prerequisites(self) -> bool:
        """Verifica pré-requisitos para o deploy"""
        print("🔍 Verificando pré-requisitos...")
        
        # Verificar Docker
        try:
            result = self.run_command("docker --version", check=False)
            if result.returncode == 0:
                print("✅ Docker encontrado")
            else:
                print("❌ Docker não encontrado")
                return False
        except Exception as e:
            print(f"❌ Erro ao verificar Docker: {e}")
            return False
        
        # Verificar Docker Compose
        try:
            result = self.run_command("docker-compose --version", check=False)
            if result.returncode == 0:
                print("✅ Docker Compose encontrado")
            else:
                print("❌ Docker Compose não encontrado")
                return False
        except Exception as e:
            print(f"❌ Erro ao verificar Docker Compose: {e}")
            return False
        
        # Verificar arquivos necessários
        required_files = [
            self.docker_compose_file,
            "requirements.txt",
            "docker/Dockerfile"
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path} encontrado")
            else:
                print(f"❌ {file_path} não encontrado")
                return False
        
        # Verificar arquivo .env
        if not os.path.exists(self.env_file):
            print(f"⚠️ {self.env_file} não encontrado, criando exemplo...")
            self.create_env_example()
        
        print("✅ Todos os pré-requisitos atendidos!")
        return True
    
    def create_env_example(self):
        """Cria arquivo .env de exemplo se não existir"""
        env_content = """# CloudDataOrchestrator v2.0 - Configurações
# Copie este arquivo e configure suas chaves de API

# Configurações AWS
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
DYNAMODB_TABLE=clouddataorchestrator

# Chaves de API para Provedores de Dados
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
NEWSAPI_API_KEY=your_newsapi_api_key
COINAPI_API_KEY=your_coinapi_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Configurações de Email para Alertas
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Configurações de ML
ML_ENABLED=true
ALERTS_ENABLED=true
PROVIDERS_ENABLED=true
"""
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        print(f"📝 Arquivo {self.env_file} criado com configurações de exemplo")
        print("⚠️ Configure suas chaves de API antes de continuar!")
    
    def build_images(self) -> bool:
        """Constrói as imagens Docker"""
        print("🔨 Construindo imagens Docker...")
        
        try:
            # Parar serviços existentes
            self.run_command("docker-compose down", check=False)
            
            # Limpar imagens antigas
            self.run_command("docker system prune -f", check=False)
            
            # Construir imagens
            result = self.run_command("docker-compose build --no-cache")
            
            if result.returncode == 0:
                print("✅ Imagens construídas com sucesso!")
                return True
            else:
                print("❌ Erro ao construir imagens")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao construir imagens: {e}")
            return False
    
    def start_services(self) -> bool:
        """Inicia os serviços"""
        print("🚀 Iniciando serviços...")
        
        try:
            # Iniciar serviços em background
            result = self.run_command("docker-compose up -d")
            
            if result.returncode == 0:
                print("✅ Serviços iniciados com sucesso!")
                return True
            else:
                print("❌ Erro ao iniciar serviços")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao iniciar serviços: {e}")
            return False
    
    def wait_for_services(self, timeout: int = 120) -> bool:
        """Aguarda os serviços ficarem prontos"""
        print(f"⏳ Aguardando serviços ficarem prontos (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Verificar status dos containers
                result = self.run_command("docker-compose ps", check=False)
                
                if result.returncode == 0:
                    # Verificar se todos os serviços estão rodando
                    if all(service in result.stdout for service in self.services):
                        print("✅ Todos os serviços estão rodando!")
                        return True
                
                print("⏳ Aguardando serviços...")
                time.sleep(10)
                
            except Exception as e:
                print(f"⚠️ Erro ao verificar status: {e}")
                time.sleep(10)
        
        print("❌ Timeout aguardando serviços")
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """Executa verificações de saúde dos serviços"""
        print("🏥 Executando verificações de saúde...")
        
        health_results = {}
        
        # Verificar dashboard
        try:
            response = requests.get(self.health_check_url, timeout=10)
            if response.status_code == 200:
                health_results["dashboard"] = "healthy"
                print("✅ Dashboard: Saudável")
            else:
                health_results["dashboard"] = f"unhealthy (HTTP {response.status_code})"
                print(f"❌ Dashboard: Não saudável (HTTP {response.status_code})")
        except Exception as e:
            health_results["dashboard"] = f"unhealthy (Error: {e})"
            print(f"❌ Dashboard: Erro de conexão - {e}")
        
        # Verificar containers
        try:
            result = self.run_command("docker-compose ps --format json", check=False)
            if result.returncode == 0:
                containers = json.loads(result.stdout)
                for container in containers:
                    service_name = container.get("Service", "unknown")
                    status = container.get("State", "unknown")
                    health_results[f"container_{service_name}"] = status
                    print(f"📦 {service_name}: {status}")
        except Exception as e:
            print(f"⚠️ Erro ao verificar containers: {e}")
        
        # Verificar logs de erro
        try:
            result = self.run_command("docker-compose logs --tail=10", check=False)
            if result.returncode == 0:
                if "ERROR" in result.stdout or "error" in result.stdout:
                    print("⚠️ Encontrados erros nos logs")
                    health_results["logs"] = "warnings_found"
                else:
                    print("✅ Logs sem erros críticos")
                    health_results["logs"] = "clean"
        except Exception as e:
            print(f"⚠️ Erro ao verificar logs: {e}")
            health_results["logs"] = f"error: {e}"
        
        self.deploy_status["health_checks"] = health_results
        return health_results
    
    def deploy(self) -> bool:
        """Executa o deploy completo"""
        print(f"🚀 Iniciando deploy do {self.project_name} v{self.version}")
        print("=" * 60)
        
        self.deploy_status["start_time"] = datetime.now()
        
        try:
            # 1. Verificar pré-requisitos
            if not self.check_prerequisites():
                print("❌ Pré-requisitos não atendidos. Deploy abortado.")
                return False
            
            # 2. Construir imagens
            if not self.build_images():
                print("❌ Falha ao construir imagens. Deploy abortado.")
                return False
            
            # 3. Iniciar serviços
            if not self.start_services():
                print("❌ Falha ao iniciar serviços. Deploy abortado.")
                return False
            
            # 4. Aguardar serviços ficarem prontos
            if not self.wait_for_services():
                print("❌ Timeout aguardando serviços. Deploy pode ter falhado.")
                return False
            
            # 5. Verificar saúde
            health_results = self.health_check()
            
            # 6. Verificar se o deploy foi bem-sucedido
            dashboard_healthy = health_results.get("dashboard", "").startswith("healthy")
            
            if dashboard_healthy:
                print("🎉 Deploy concluído com sucesso!")
                self.deploy_status["end_time"] = datetime.now()
                self._save_deploy_report()
                return True
            else:
                print("⚠️ Deploy concluído com problemas de saúde")
                self.deploy_status["end_time"] = datetime.now()
                self._save_deploy_report()
                return False
                
        except Exception as e:
            print(f"❌ Erro fatal durante deploy: {e}")
            self.deploy_status["errors"].append(str(e))
            self.deploy_status["end_time"] = datetime.now()
            self._save_deploy_report()
            return False
    
    def _save_deploy_report(self):
        """Salva relatório do deploy"""
        try:
            report = {
                "project": self.project_name,
                "version": self.version,
                "deploy_status": self.deploy_status,
                "timestamp": datetime.now().isoformat()
            }
            
            with open("deploy_report.json", "w") as f:
                json.dump(report, f, indent=2, default=str)
            
            print("📊 Relatório de deploy salvo em deploy_report.json")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar relatório: {e}")
    
    def show_status(self):
        """Mostra status atual dos serviços"""
        print("📊 Status dos serviços:")
        print("-" * 40)
        
        try:
            result = self.run_command("docker-compose ps", check=False)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print("❌ Erro ao obter status")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def show_logs(self, service: str = None, lines: int = 50):
        """Mostra logs dos serviços"""
        if service:
            print(f"📋 Logs do serviço {service}:")
            command = f"docker-compose logs --tail={lines} {service}"
        else:
            print(f"📋 Logs de todos os serviços (últimas {lines} linhas):")
            command = f"docker-compose logs --tail={lines}"
        
        try:
            result = self.run_command(command, check=False)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print("❌ Erro ao obter logs")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def stop_services(self):
        """Para todos os serviços"""
        print("🛑 Parando serviços...")
        
        try:
            result = self.run_command("docker-compose down")
            if result.returncode == 0:
                print("✅ Serviços parados com sucesso!")
            else:
                print("❌ Erro ao parar serviços")
        except Exception as e:
            print(f"❌ Erro: {e}")


def main():
    """Função principal"""
    deploy_manager = DeployManager()
    
    if len(sys.argv) < 2:
        print("Uso: python deploy_v2.py [comando]")
        print("Comandos disponíveis:")
        print("  deploy     - Executa deploy completo")
        print("  status     - Mostra status dos serviços")
        print("  logs       - Mostra logs dos serviços")
        print("  stop       - Para todos os serviços")
        print("  health     - Executa verificação de saúde")
        return
    
    command = sys.argv[1].lower()
    
    if command == "deploy":
        success = deploy_manager.deploy()
        sys.exit(0 if success else 1)
    
    elif command == "status":
        deploy_manager.show_status()
    
    elif command == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        deploy_manager.show_logs(service)
    
    elif command == "stop":
        deploy_manager.stop_services()
    
    elif command == "health":
        health_results = deploy_manager.health_check()
        print("🏥 Resultados da verificação de saúde:")
        for service, status in health_results.items():
            print(f"  {service}: {status}")
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("Use: deploy, status, logs, stop, health")


if __name__ == "__main__":
    main()
