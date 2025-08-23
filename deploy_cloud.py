#!/usr/bin/env python3
"""
Script de Deploy Automatizado na Nuvem - CloudDataOrchestrator v2.0
Deploy completo para AWS usando Terraform e Docker
"""

import os
import sys
import subprocess
import json
import time
import requests
from datetime import datetime
from pathlib import Path
import argparse

class CloudDeployManager:
    """Gerenciador de deploy na nuvem"""
    
    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.project_name = "clouddataorchestrator"
        self.aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.tf_dir = Path("infrastructure")
        
        # Configurações por ambiente
        self.config = {
            "staging": {
                "instance_count": 1,
                "cpu": 512,
                "memory": 1024,
                "domain": None
            },
            "production": {
                "instance_count": 3,
                "cpu": 1024,
                "memory": 2048,
                "domain": "api.clouddataorchestrator.com"
            }
        }
        
        print(f"🚀 CloudDataOrchestrator Deploy Manager")
        print(f"📦 Ambiente: {environment}")
        print(f"🌍 Região AWS: {self.aws_region}")
        print("=" * 60)
    
    def run_command(self, command: str, cwd: str = None) -> subprocess.CompletedProcess:
        """Executa comando no shell"""
        try:
            print(f"🔧 Executando: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro no comando: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            raise
    
    def check_prerequisites(self) -> bool:
        """Verifica pré-requisitos para deploy"""
        print("🔍 Verificando pré-requisitos...")
        
        prerequisites = [
            ("docker", "Docker não encontrado. Instale: https://docs.docker.com/get-docker/"),
            ("terraform", "Terraform não encontrado. Instale: https://terraform.io/downloads"),
            ("aws", "AWS CLI não encontrado. Instale: https://aws.amazon.com/cli/"),
            ("git", "Git não encontrado.")
        ]
        
        missing = []
        for cmd, error_msg in prerequisites:
            try:
                self.run_command(f"which {cmd}")
                print(f"✅ {cmd} encontrado")
            except subprocess.CalledProcessError:
                print(f"❌ {error_msg}")
                missing.append(cmd)
        
        if missing:
            print(f"\n❌ Pré-requisitos faltando: {', '.join(missing)}")
            return False
        
        # Verificar credenciais AWS
        try:
            self.run_command("aws sts get-caller-identity")
            print("✅ Credenciais AWS configuradas")
        except subprocess.CalledProcessError:
            print("❌ Credenciais AWS não configuradas. Execute: aws configure")
            return False
        
        # Verificar variáveis de ambiente
        required_env = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
        missing_env = [var for var in required_env if not os.getenv(var)]
        
        if missing_env:
            print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_env)}")
            return False
        
        print("✅ Todos os pré-requisitos atendidos")
        return True
    
    def build_and_push_image(self) -> str:
        """Build e push da imagem Docker"""
        print("🐳 Building e pushing imagem Docker...")
        
        # Tag da imagem
        commit_hash = self.run_command("git rev-parse --short HEAD").stdout.strip()
        image_tag = f"{self.environment}-{commit_hash}"
        image_name = f"ghcr.io/ssilvestres/{self.project_name}:{image_tag}"
        
        print(f"📦 Imagem: {image_name}")
        
        # Build
        self.run_command(f"docker build -t {image_name} -f docker/Dockerfile .")
        
        # Login no GitHub Container Registry
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            print("🔐 Fazendo login no GitHub Container Registry...")
            self.run_command(f"echo {github_token} | docker login ghcr.io -u USERNAME --password-stdin")
        
        # Push
        self.run_command(f"docker push {image_name}")
        
        print(f"✅ Imagem {image_name} enviada com sucesso!")
        return image_tag
    
    def setup_terraform_backend(self):
        """Configura backend do Terraform"""
        print("🏗️ Configurando backend do Terraform...")
        
        bucket_name = f"{self.project_name}-terraform-state-{self.aws_region}"
        
        # Criar bucket se não existir
        try:
            self.run_command(f"aws s3 ls s3://{bucket_name}")
            print(f"✅ Bucket {bucket_name} já existe")
        except subprocess.CalledProcessError:
            print(f"📦 Criando bucket {bucket_name}...")
            self.run_command(f"aws s3 mb s3://{bucket_name} --region {self.aws_region}")
            
            # Habilitar versionamento
            self.run_command(f"aws s3api put-bucket-versioning --bucket {bucket_name} --versioning-configuration Status=Enabled")
            
            # Habilitar criptografia
            self.run_command(f"""aws s3api put-bucket-encryption --bucket {bucket_name} --server-side-encryption-configuration '{{"Rules":[{{"ApplyServerSideEncryptionByDefault":{{"SSEAlgorithm":"AES256"}}}}]}}'""")
        
        return bucket_name
    
    def deploy_infrastructure(self, image_tag: str) -> Dict[str, str]:
        """Deploy da infraestrutura com Terraform"""
        print("🏗️ Fazendo deploy da infraestrutura...")
        
        # Configurar backend
        bucket_name = self.setup_terraform_backend()
        
        # Usar arquivos v2
        tf_main = self.tf_dir / "main_v2.tf"
        tf_vars = self.tf_dir / "variables_v2.tf"
        
        if not tf_main.exists():
            raise FileNotFoundError(f"Arquivo {tf_main} não encontrado")
        
        # Configurações do ambiente
        env_config = self.config[self.environment]
        
        # Gerar token de API
        api_token = os.getenv("API_TOKEN", f"{self.project_name}-{self.environment}-{int(time.time())}")
        
        # Variáveis Terraform
        tf_vars_content = {
            "environment": self.environment,
            "project_name": self.project_name,
            "aws_region": self.aws_region,
            "image_tag": image_tag,
            "api_token": api_token,
            "api_instance_count": env_config["instance_count"],
            "api_cpu": env_config["cpu"],
            "api_memory": env_config["memory"]
        }
        
        # Salvar variáveis em arquivo
        vars_file = self.tf_dir / f"{self.environment}.tfvars"
        with open(vars_file, "w") as f:
            for key, value in tf_vars_content.items():
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                else:
                    f.write(f'{key} = {value}\n')
        
        # Comandos Terraform
        tf_commands = [
            f"terraform init -backend-config='bucket={bucket_name}' -backend-config='key={self.environment}/terraform.tfstate' -backend-config='region={self.aws_region}'",
            f"terraform plan -var-file={vars_file.name} -out=tfplan",
            "terraform apply -auto-approve tfplan"
        ]
        
        # Copiar arquivos v2 para arquivos principais
        self.run_command(f"cp {tf_main} {self.tf_dir}/main.tf")
        self.run_command(f"cp {tf_vars} {self.tf_dir}/variables.tf")
        
        for command in tf_commands:
            self.run_command(command, cwd=str(self.tf_dir))
        
        # Obter outputs
        outputs = {}
        try:
            result = self.run_command("terraform output -json", cwd=str(self.tf_dir))
            outputs = json.loads(result.stdout)
            # Extrair valores dos outputs
            outputs = {k: v["value"] for k, v in outputs.items()}
        except Exception as e:
            print(f"⚠️ Erro ao obter outputs: {e}")
        
        print("✅ Infraestrutura deployada com sucesso!")
        return outputs
    
    def health_check(self, api_url: str, max_attempts: int = 20) -> bool:
        """Verifica saúde da aplicação"""
        print(f"🏥 Verificando saúde da aplicação: {api_url}")
        
        api_token = os.getenv("API_TOKEN", f"{self.project_name}-{self.environment}")
        headers = {"Authorization": f"Bearer {api_token}"}
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Health check básico
                response = requests.get(f"{api_url}/health", timeout=10)
                if response.status_code == 200:
                    print(f"✅ Health check básico OK (tentativa {attempt})")
                    
                    # Health check com autenticação
                    response = requests.get(f"{api_url}/status", headers=headers, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ Health check completo OK!")
                        return True
                    else:
                        print(f"⚠️ Status endpoint retornou {response.status_code}")
                
            except requests.RequestException as e:
                print(f"⏳ Tentativa {attempt}/{max_attempts}: {e}")
            
            if attempt < max_attempts:
                time.sleep(30)
        
        print(f"❌ Health check falhou após {max_attempts} tentativas")
        return False
    
    def deploy(self) -> bool:
        """Executa deploy completo"""
        start_time = datetime.now()
        
        try:
            # 1. Verificar pré-requisitos
            if not self.check_prerequisites():
                return False
            
            # 2. Build e push da imagem
            image_tag = self.build_and_push_image()
            
            # 3. Deploy da infraestrutura
            outputs = self.deploy_infrastructure(image_tag)
            
            # 4. Health check
            api_url = outputs.get("api_url")
            if api_url:
                if not self.health_check(api_url):
                    print("❌ Deploy falhou no health check")
                    return False
            else:
                print("⚠️ URL da API não encontrada nos outputs")
            
            # 5. Relatório final
            duration = datetime.now() - start_time
            self._generate_deploy_report(outputs, image_tag, duration)
            
            print(f"\n🎉 Deploy concluído com sucesso em {duration}!")
            print(f"🌐 API URL: {outputs.get('api_url', 'N/A')}")
            print(f"📊 Dashboard URL: {outputs.get('dashboard_url', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Deploy falhou: {e}")
            return False
    
    def _generate_deploy_report(self, outputs: Dict, image_tag: str, duration):
        """Gera relatório de deploy"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "image_tag": image_tag,
            "duration_seconds": duration.total_seconds(),
            "outputs": outputs,
            "status": "success"
        }
        
        report_file = f"deploy_report_{self.environment}_{int(time.time())}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Relatório salvo em: {report_file}")
    
    def rollback(self):
        """Rollback para versão anterior"""
        print("🔄 Iniciando rollback...")
        
        # Obter tag anterior
        try:
            result = self.run_command("git tag --sort=-version:refname | head -2 | tail -1")
            previous_tag = result.stdout.strip()
            
            if not previous_tag:
                print("❌ Nenhuma tag anterior encontrada")
                return False
            
            print(f"🔄 Fazendo rollback para: {previous_tag}")
            
            # Deploy com tag anterior
            outputs = self.deploy_infrastructure(previous_tag)
            
            # Health check
            api_url = outputs.get("api_url")
            if api_url and self.health_check(api_url):
                print("✅ Rollback concluído com sucesso!")
                return True
            else:
                print("❌ Rollback falhou no health check")
                return False
                
        except Exception as e:
            print(f"❌ Erro no rollback: {e}")
            return False
    
    def destroy(self):
        """Destrói toda a infraestrutura"""
        print("🗑️ Destruindo infraestrutura...")
        
        confirmation = input(f"⚠️ Tem certeza que deseja destruir o ambiente {self.environment}? (yes/no): ")
        if confirmation.lower() != "yes":
            print("❌ Operação cancelada")
            return False
        
        try:
            self.run_command("terraform destroy -auto-approve", cwd=str(self.tf_dir))
            print("✅ Infraestrutura destruída com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao destruir infraestrutura: {e}")
            return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Deploy CloudDataOrchestrator na nuvem")
    parser.add_argument("action", choices=["deploy", "rollback", "destroy"], help="Ação a executar")
    parser.add_argument("--environment", choices=["staging", "production"], default="staging", help="Ambiente de deploy")
    
    args = parser.parse_args()
    
    deploy_manager = CloudDeployManager(args.environment)
    
    if args.action == "deploy":
        success = deploy_manager.deploy()
    elif args.action == "rollback":
        success = deploy_manager.rollback()
    elif args.action == "destroy":
        success = deploy_manager.destroy()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
