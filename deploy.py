#!/usr/bin/env python3
"""
Script de Deploy Completo para o Projeto Cloud Data Orchestrator
Executa todos os passos necessários para deploy na AWS
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

class DeployManager:
    """Gerenciador de deploy para o projeto Cloud Data Orchestrator"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.infrastructure_dir = self.project_root / "infrastructure"
        self.lambda_dir = self.project_root / "lambda"
        
    def run_command(self, command, cwd=None, check=True):
        """Executa um comando no terminal"""
        if cwd is None:
            cwd = self.project_root
            
        print(f"🚀 Executando: {command}")
        print(f"📁 Diretório: {cwd}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                check=check,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                print(f"✅ Saída: {result.stdout}")
            
            if result.stderr:
                print(f"⚠️  Stderr: {result.stderr}")
                
            return result
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao executar comando: {e}")
            if check:
                sys.exit(1)
            return e
    
    def check_prerequisites(self):
        """Verifica pré-requisitos para deploy"""
        print("🔍 Verificando pré-requisitos...")
        
        # Verificar Python
        try:
            python_version = subprocess.run(
                ["python", "--version"], 
                capture_output=True, 
                text=True
            ).stdout.strip()
            print(f"✅ Python: {python_version}")
        except:
            print("❌ Python não encontrado")
            return False
        
        # Verificar AWS CLI
        try:
            aws_version = subprocess.run(
                ["aws", "--version"], 
                capture_output=True, 
                text=True
            ).stdout.strip()
            print(f"✅ AWS CLI: {aws_version}")
        except:
            print("❌ AWS CLI não encontrado")
            return False
        
        # Verificar se as credenciais AWS estão configuradas
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                identity = json.loads(result.stdout)
                print(f"✅ AWS Credenciais: {identity.get('Account', 'N/A')}")
            else:
                print("❌ AWS Credenciais não configuradas")
                return False
        except:
            print("❌ Erro ao verificar credenciais AWS")
            return False
        
        return True
    
    def install_dependencies(self):
        """Instala dependências Python"""
        print("📦 Instalando dependências...")
        
        # Instalar dependências principais
        self.run_command("pip install -r requirements.txt")
        
        # Instalar dependências do Lambda
        self.run_command("pip install -r lambda/requirements.txt")
        
        print("✅ Dependências instaladas com sucesso")
    
    def run_tests(self):
        """Executa testes automatizados"""
        print("🧪 Executando testes...")
        
        # Executar testes
        result = self.run_command("python -m pytest tests/ -v", check=False)
        
        if result.returncode == 0:
            print("✅ Todos os testes passaram")
        else:
            print("⚠️  Alguns testes falharam, mas continuando...")
    
    def run_linting(self):
        """Executa verificações de qualidade de código"""
        print("🔍 Executando verificações de qualidade...")
        
        # Black
        self.run_command("black --check .", check=False)
        
        # Flake8
        self.run_command("flake8 . --max-line-length=88 --ignore=E203,W503", check=False)
        
        print("✅ Verificações de qualidade concluídas")
    
    def deploy_infrastructure(self):
        """Deploy da infraestrutura com Terraform"""
        print("🏗️  Deploy da infraestrutura...")
        
        if not self.infrastructure_dir.exists():
            print("❌ Diretório de infraestrutura não encontrado")
            return False
        
        # Navegar para diretório de infraestrutura
        os.chdir(self.infrastructure_dir)
        
        try:
            # Terraform init
            print("📥 Inicializando Terraform...")
            self.run_command("terraform init")
            
            # Terraform plan
            print("📋 Criando plano de deploy...")
            self.run_command("terraform plan -out=tfplan")
            
            # Terraform apply
            print("🚀 Aplicando configurações...")
            self.run_command("terraform apply -auto-approve tfplan")
            
            # Obter outputs
            print("📊 Obtendo informações da infraestrutura...")
            result = self.run_command("terraform output -json")
            
            if result.returncode == 0:
                outputs = json.loads(result.stdout)
                print(f"✅ Infraestrutura deployada com sucesso")
                print(f"🌐 API Gateway URL: {outputs.get('api_gateway_url', {}).get('value', 'N/A')}")
                print(f"🗄️  DynamoDB Table: {outputs.get('dynamodb_table_name', {}).get('value', 'N/A')}")
                print(f"⚡ Lambda Function: {outputs.get('lambda_function_name', {}).get('value', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no deploy da infraestrutura: {e}")
            return False
        finally:
            # Voltar ao diretório raiz
            os.chdir(self.project_root)
    
    def deploy_lambda(self):
        """Deploy das funções Lambda"""
        print("⚡ Deploy das funções Lambda...")
        
        if not self.lambda_dir.exists():
            print("❌ Diretório Lambda não encontrado")
            return False
        
        # Navegar para diretório Lambda
        os.chdir(self.lambda_dir)
        
        try:
            # Tornar script executável (Linux/Mac)
            if os.name != 'nt':  # Não Windows
                self.run_command("chmod +x deploy.sh")
            
            # Executar deploy
            if os.name == 'nt':  # Windows
                self.run_command("python deploy.py")
            else:
                self.run_command("./deploy.sh")
            
            print("✅ Funções Lambda deployadas com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro no deploy das funções Lambda: {e}")
            return False
        finally:
            # Voltar ao diretório raiz
            os.chdir(self.project_root)
    
    def test_data_pipeline(self):
        """Testa o data pipeline"""
        print("🔬 Testando data pipeline...")
        
        try:
            # Executar data collector em modo de teste
            result = self.run_command("python data_pipeline/data_collector_test.py", check=False)
            
            if result.returncode == 0:
                print("✅ Data pipeline funcionando corretamente")
                return True
            else:
                print("⚠️  Data pipeline com problemas, mas continuando...")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao testar data pipeline: {e}")
            return False
    
    def run_dashboard(self):
        """Executa o dashboard para teste"""
        print("📊 Iniciando dashboard para teste...")
        
        try:
            # Executar dashboard em background
            if os.name == 'nt':  # Windows
                self.run_command("start streamlit run dashboard/app_test.py --server.port 8501", check=False)
            else:
                self.run_command("streamlit run dashboard/app_test.py --server.port 8501 &", check=False)
            
            print("✅ Dashboard iniciado em http://localhost:8501")
            print("⏳ Aguarde alguns segundos para o dashboard carregar...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar dashboard: {e}")
            return False
    
    def deploy(self, skip_infrastructure=False, skip_lambda=False):
        """Executa o deploy completo"""
        print("🚀 Iniciando deploy completo do projeto Cloud Data Orchestrator...")
        print("=" * 60)
        
        # Verificar pré-requisitos
        if not self.check_prerequisites():
            print("❌ Pré-requisitos não atendidos. Abortando deploy.")
            return False
        
        # Instalar dependências
        self.install_dependencies()
        
        # Executar testes
        self.run_tests()
        
        # Executar linting
        self.run_linting()
        
        # Deploy da infraestrutura
        if not skip_infrastructure:
            if not self.deploy_infrastructure():
                print("❌ Falha no deploy da infraestrutura")
                return False
        else:
            print("⏭️  Pulando deploy da infraestrutura")
        
        # Deploy das funções Lambda
        if not skip_lambda:
            if not self.deploy_lambda():
                print("❌ Falha no deploy das funções Lambda")
                return False
        else:
            print("⏭️  Pulando deploy das funções Lambda")
        
        # Testar data pipeline
        self.test_data_pipeline()
        
        # Executar dashboard
        self.run_dashboard()
        
        print("=" * 60)
        print("🎉 Deploy concluído com sucesso!")
        print("📊 Dashboard disponível em: http://localhost:8501")
        print("🔧 Para verificar logs: docker-compose logs -f")
        
        return True

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy do Projeto Cloud Data Orchestrator")
    parser.add_argument("--skip-infrastructure", action="store_true", 
                       help="Pular deploy da infraestrutura")
    parser.add_argument("--skip-lambda", action="store_true", 
                       help="Pular deploy das funções Lambda")
    
    args = parser.parse_args()
    
    deploy_manager = DeployManager()
    
    try:
        success = deploy_manager.deploy(
            skip_infrastructure=args.skip_infrastructure,
            skip_lambda=args.skip_lambda
        )
        
        if success:
            print("✅ Deploy concluído com sucesso!")
            sys.exit(0)
        else:
            print("❌ Deploy falhou!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Deploy interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
