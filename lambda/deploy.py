#!/usr/bin/env python3
"""
Script de Deploy para Funções Lambda
Deploy automatizado das funções Lambda para AWS
"""

import os
import sys
import zipfile
import shutil
import subprocess
import json
from pathlib import Path

class LambdaDeployer:
    """Deployer para funções Lambda"""
    
    def __init__(self):
        self.function_name = "data-pipeline-handler"
        self.region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        self.zip_file = "data_handler.zip"
        self.lambda_dir = Path(__file__).parent
        
    def check_aws_cli(self):
        """Verifica se AWS CLI está instalado"""
        try:
            result = subprocess.run(
                ["aws", "--version"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print(f"✅ AWS CLI: {result.stdout.strip()}")
                return True
            else:
                print("❌ AWS CLI não encontrado")
                return False
        except:
            print("❌ AWS CLI não encontrado")
            return False
    
    def check_aws_credentials(self):
        """Verifica se as credenciais AWS estão configuradas"""
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                identity = json.loads(result.stdout)
                print(f"✅ AWS Credenciais: {identity.get('Account', 'N/A')}")
                return True
            else:
                print("❌ AWS Credenciais não configuradas")
                return False
        except:
            print("❌ Erro ao verificar credenciais AWS")
            return False
    
    def install_dependencies(self):
        """Instala dependências Python"""
        print("📦 Instalando dependências...")
        
        try:
            # Instalar dependências
            result = subprocess.run(
                ["pip", "install", "-r", "requirements.txt", "-t", "."],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Dependências instaladas com sucesso")
                return True
            else:
                print(f"❌ Erro ao instalar dependências: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            return False
    
    def create_zip_package(self):
        """Cria pacote ZIP para deploy"""
        print("🗜️  Criando pacote ZIP...")
        
        try:
            # Remover ZIP anterior se existir
            if os.path.exists(self.zip_file):
                os.remove(self.zip_file)
                print(f"🗑️  ZIP anterior removido: {self.zip_file}")
            
            # Criar novo ZIP
            with zipfile.ZipFile(self.zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar arquivos Python
                for file_path in self.lambda_dir.rglob("*.py"):
                    if file_path.name != "deploy.py":  # Não incluir este script
                        arcname = file_path.relative_to(self.lambda_dir)
                        zipf.write(file_path, arcname)
                        print(f"📁 Adicionado: {arcname}")
                
                # Adicionar dependências instaladas
                for item in self.lambda_dir.iterdir():
                    if item.is_dir() and item.name not in ["__pycache__", ".git"]:
                        if item.name.startswith("boto3") or item.name.startswith("botocore"):
                            for file_path in item.rglob("*"):
                                if file_path.is_file():
                                    arcname = file_path.relative_to(self.lambda_dir)
                                    zipf.write(file_path, arcname)
                                    print(f"📦 Adicionado: {arcname}")
            
            print(f"✅ Pacote ZIP criado: {self.zip_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar ZIP: {e}")
            return False
    
    def deploy_to_aws(self):
        """Faz deploy para AWS Lambda"""
        print("☁️  Fazendo deploy para AWS Lambda...")
        
        try:
            # Verificar se a função existe
            result = subprocess.run(
                ["aws", "lambda", "get-function", "--function-name", self.function_name, "--region", self.region],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Função Lambda encontrada: {self.function_name}")
                # Atualizar função existente
                update_result = subprocess.run([
                    "aws", "lambda", "update-function-code",
                    "--function-name", self.function_name,
                    "--zip-file", f"fileb://{self.zip_file}",
                    "--region", self.region
                ], capture_output=True, text=True)
                
                if update_result.returncode == 0:
                    print("✅ Função Lambda atualizada com sucesso")
                    return True
                else:
                    print(f"❌ Erro ao atualizar função: {update_result.stderr}")
                    return False
            else:
                print(f"⚠️  Função Lambda não encontrada: {self.function_name}")
                print("💡 Crie a função primeiro usando Terraform ou AWS Console")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao fazer deploy: {e}")
            return False
    
    def cleanup(self):
        """Limpa arquivos temporários"""
        print("🧹 Limpando arquivos temporários...")
        
        try:
            # Remover dependências instaladas
            for item in self.lambda_dir.iterdir():
                if item.is_dir() and item.name not in ["__pycache__", ".git"]:
                    if item.name.startswith("boto3") or item.name.startswith("botocore"):
                        shutil.rmtree(item)
                        print(f"🗑️  Removido: {item.name}")
            
            # Remover ZIP
            if os.path.exists(self.zip_file):
                os.remove(self.zip_file)
                print(f"🗑️  Removido: {self.zip_file}")
            
            print("✅ Limpeza concluída")
            
        except Exception as e:
            print(f"⚠️  Erro na limpeza: {e}")
    
    def deploy(self):
        """Executa deploy completo"""
        print("🚀 Iniciando deploy das funções Lambda...")
        print(f"📊 Função: {self.function_name}")
        print(f"🌍 Região: {self.region}")
        print("=" * 50)
        
        try:
            # Verificar pré-requisitos
            if not self.check_aws_cli():
                return False
            
            if not self.check_aws_credentials():
                return False
            
            # Instalar dependências
            if not self.install_dependencies():
                return False
            
            # Criar pacote ZIP
            if not self.create_zip_package():
                return False
            
            # Deploy para AWS
            if not self.deploy_to_aws():
                return False
            
            print("=" * 50)
            print("🎉 Deploy concluído com sucesso!")
            print(f"⚡ Função Lambda: {self.function_name}")
            print(f"🌍 Região: {self.region}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante deploy: {e}")
            return False
        finally:
            # Limpeza
            self.cleanup()

def main():
    """Função principal"""
    deployer = LambdaDeployer()
    
    try:
        success = deployer.deploy()
        
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
