#!/usr/bin/env python3
"""
Script de Monitoramento para Cloud Data Orchestrator
Monitora o status de todos os componentes do projeto
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

class ProjectMonitor:
    """Monitor do projeto Cloud Data Orchestrator"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.monitoring_data = {}
        
    def check_file_structure(self):
        """Verifica a estrutura de arquivos do projeto"""
        print("📁 Verificando estrutura de arquivos...")
        
        required_files = [
            "README.md",
            "requirements.txt",
            "docker-compose.yml",
            "deploy.py",
            "monitor.py",
            "run_tests.py",
            ".github/workflows/ci-cd.yml",
            "infrastructure/main.tf",
            "lambda/data_handler.py",
            "data_pipeline/data_collector.py",
            "dashboard/app.py",
            "tests/test_data_collector.py"
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                existing_files.append(file_path)
                print(f"✅ {file_path}")
            else:
                missing_files.append(file_path)
                print(f"❌ {file_path}")
        
        self.monitoring_data['file_structure'] = {
            'total_required': len(required_files),
            'existing': len(existing_files),
            'missing': len(missing_files),
            'missing_files': missing_files,
            'coverage': f"{(len(existing_files)/len(required_files))*100:.1f}%"
        }
        
        return len(missing_files) == 0
    
    def check_dependencies(self):
        """Verifica dependências Python"""
        print("\n📦 Verificando dependências...")
        
        try:
            result = subprocess.run(
                ["pip", "list"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                installed_packages = result.stdout.lower()
                
                required_packages = [
                    'boto3', 'requests', 'streamlit', 'plotly', 
                    'pandas', 'pytest', 'black', 'flake8'
                ]
                
                found_packages = []
                missing_packages = []
                
                for package in required_packages:
                    if package.lower() in installed_packages:
                        found_packages.append(package)
                        print(f"✅ {package}")
                    else:
                        missing_packages.append(package)
                        print(f"❌ {package}")
                
                self.monitoring_data['dependencies'] = {
                    'total_required': len(required_packages),
                    'found': len(found_packages),
                    'missing': len(missing_packages),
                    'missing_packages': missing_packages,
                    'coverage': f"{(len(found_packages)/len(required_packages))*100:.1f}%"
                }
                
                return len(missing_packages) == 0
            else:
                print("❌ Erro ao verificar dependências")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao verificar dependências: {e}")
            return False
    
    def check_git_status(self):
        """Verifica status do Git"""
        print("\n🔧 Verificando status do Git...")
        
        try:
            # Verificar se é um repositório Git
            if not (self.project_root / ".git").exists():
                print("❌ Não é um repositório Git")
                self.monitoring_data['git_status'] = {'is_repo': False}
                return False
            
            # Verificar status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"], 
                capture_output=True, 
                text=True,
                cwd=self.project_root
            )
            
            # Verificar branch atual
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"], 
                capture_output=True, 
                text=True,
                cwd=self.project_root
            )
            
            # Verificar remote
            remote_result = subprocess.run(
                ["git", "remote", "-v"], 
                capture_output=True, 
                text=True,
                cwd=self.project_root
            )
            
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            has_changes = len(status_result.stdout.strip()) > 0
            remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else "none"
            
            print(f"✅ Branch atual: {current_branch}")
            print(f"✅ Mudanças pendentes: {'Sim' if has_changes else 'Não'}")
            print(f"✅ Remote configurado: {'Sim' if 'origin' in remote_url else 'Não'}")
            
            self.monitoring_data['git_status'] = {
                'is_repo': True,
                'current_branch': current_branch,
                'has_changes': has_changes,
                'remote_url': remote_url
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao verificar Git: {e}")
            return False
    
    def check_aws_config(self):
        """Verifica configuração AWS"""
        print("\n☁️  Verificando configuração AWS...")
        
        try:
            # Verificar AWS CLI
            aws_version_result = subprocess.run(
                ["aws", "--version"], 
                capture_output=True, 
                text=True
            )
            
            if aws_version_result.returncode == 0:
                print(f"✅ AWS CLI: {aws_version_result.stdout.strip()}")
                
                # Verificar credenciais
                identity_result = subprocess.run(
                    ["aws", "sts", "get-caller-identity"], 
                    capture_output=True, 
                    text=True
                )
                
                if identity_result.returncode == 0:
                    identity = json.loads(identity_result.stdout)
                    print(f"✅ AWS Account: {identity.get('Account', 'N/A')}")
                    print(f"✅ AWS User: {identity.get('Arn', 'N/A')}")
                    
                    self.monitoring_data['aws_config'] = {
                        'cli_installed': True,
                        'credentials_configured': True,
                        'account_id': identity.get('Account'),
                        'user_arn': identity.get('Arn')
                    }
                    
                    return True
                else:
                    print("❌ AWS Credenciais não configuradas")
                    self.monitoring_data['aws_config'] = {
                        'cli_installed': True,
                        'credentials_configured': False
                    }
                    return False
            else:
                print("❌ AWS CLI não instalado")
                self.monitoring_data['aws_config'] = {
                    'cli_installed': False,
                    'credentials_configured': False
                }
                return False
                
        except Exception as e:
            print(f"❌ Erro ao verificar AWS: {e}")
            return False
    
    def check_docker(self):
        """Verifica Docker"""
        print("\n🐳 Verificando Docker...")
        
        try:
            # Verificar Docker
            docker_version_result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True
            )
            
            if docker_version_result.returncode == 0:
                print(f"✅ Docker: {docker_version_result.stdout.strip()}")
                
                # Verificar Docker Compose
                compose_version_result = subprocess.run(
                    ["docker-compose", "--version"], 
                    capture_output=True, 
                    text=True
                )
                
                if compose_version_result.returncode == 0:
                    print(f"✅ Docker Compose: {compose_version_result.stdout.strip()}")
                    self.monitoring_data['docker'] = {
                        'docker_installed': True,
                        'compose_installed': True
                    }
                    return True
                else:
                    print("❌ Docker Compose não instalado")
                    self.monitoring_data['docker'] = {
                        'docker_installed': True,
                        'compose_installed': False
                    }
                    return False
            else:
                print("❌ Docker não instalado")
                self.monitoring_data['docker'] = {
                    'docker_installed': False,
                    'compose_installed': False
                }
                return False
                
        except Exception as e:
            print(f"❌ Erro ao verificar Docker: {e}")
            return False
    
    def generate_report(self):
        """Gera relatório de monitoramento"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE MONITORAMENTO")
        print("=" * 60)
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Projeto: {self.project_root.name}")
        
        # Estrutura de arquivos
        fs = self.monitoring_data.get('file_structure', {})
        print(f"\n📁 Estrutura de Arquivos: {fs.get('coverage', 'N/A')}")
        print(f"   Total: {fs.get('total_required', 0)} | Encontrados: {fs.get('existing', 0)} | Faltando: {fs.get('missing', 0)}")
        
        # Dependências
        deps = self.monitoring_data.get('dependencies', {})
        print(f"\n📦 Dependências: {deps.get('coverage', 'N/A')}")
        print(f"   Total: {deps.get('total_required', 0)} | Encontradas: {deps.get('found', 0)} | Faltando: {deps.get('missing', 0)}")
        
        # Git
        git = self.monitoring_data.get('git_status', {})
        if git.get('is_repo'):
            print(f"\n🔧 Git: ✅ Repositório configurado")
            print(f"   Branch: {git.get('current_branch', 'N/A')}")
            print(f"   Mudanças: {'Sim' if git.get('has_changes') else 'Não'}")
        else:
            print(f"\n🔧 Git: ❌ Não é um repositório")
        
        # AWS
        aws = self.monitoring_data.get('aws_config', {})
        if aws.get('cli_installed'):
            print(f"\n☁️  AWS: ✅ CLI instalado")
            if aws.get('credentials_configured'):
                print(f"   Account: {aws.get('account_id', 'N/A')}")
            else:
                print(f"   Credenciais: ❌ Não configuradas")
        else:
            print(f"\n☁️  AWS: ❌ CLI não instalado")
        
        # Docker
        docker = self.monitoring_data.get('docker', {})
        if docker.get('docker_installed'):
            print(f"\n🐳 Docker: ✅ Instalado")
            if docker.get('compose_installed'):
                print(f"   Compose: ✅ Instalado")
            else:
                print(f"   Compose: ❌ Não instalado")
        else:
            print(f"\n🐳 Docker: ❌ Não instalado")
        
        print("=" * 60)
        
        # Salvar relatório em arquivo
        report_file = self.project_root / "monitoring_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.monitoring_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório salvo em: {report_file}")
    
    def run_monitoring(self):
        """Executa monitoramento completo"""
        print("🔍 Iniciando monitoramento do projeto...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Executar todas as verificações
        checks = [
            ("Estrutura de Arquivos", self.check_file_structure),
            ("Dependências Python", self.check_dependencies),
            ("Status Git", self.check_git_status),
            ("Configuração AWS", self.check_aws_config),
            ("Docker", self.check_docker)
        ]
        
        for check_name, check_func in checks:
            print(f"\n{'='*20} {check_name} {'='*20}")
            try:
                check_func()
            except Exception as e:
                print(f"❌ Erro na verificação {check_name}: {e}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n⏱️  Tempo total de monitoramento: {execution_time:.2f} segundos")
        
        # Gerar relatório
        self.generate_report()
        
        return True

def main():
    """Função principal"""
    monitor = ProjectMonitor()
    
    try:
        success = monitor.run_monitoring()
        
        if success:
            print("✅ Monitoramento concluído com sucesso!")
            sys.exit(0)
        else:
            print("❌ Monitoramento falhou!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Monitoramento interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
