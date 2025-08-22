#!/usr/bin/env python3
"""
Sistema de Configuração Avançado para Cloud Data Orchestrator
Gerencia todas as configurações do projeto de forma centralizada
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class AWSSettings:
    """Configurações AWS"""
    region: str = "us-east-1"
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    profile_name: Optional[str] = None
    
    def __post_init__(self):
        # Carregar de variáveis de ambiente se não definidas
        if not self.access_key_id:
            self.access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        if not self.secret_access_key:
            self.secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        if not self.session_token:
            self.session_token = os.environ.get("AWS_SESSION_TOKEN")
        if not self.profile_name:
            self.profile_name = os.environ.get("AWS_PROFILE")
        if not self.region:
            self.region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

@dataclass
class DatabaseSettings:
    """Configurações do banco de dados"""
    table_name: str = "data-pipeline-table"
    billing_mode: str = "PAY_PER_REQUEST"
    read_capacity: int = 5
    write_capacity: int = 5
    
    def __post_init__(self):
        self.table_name = os.environ.get("DYNAMODB_TABLE", self.table_name)

@dataclass
class APISettings:
    """Configurações das APIs externas"""
    openweather_api_key: Optional[str] = None
    exchangerate_api_key: Optional[str] = None
    github_api_key: Optional[str] = None
    
    def __post_init__(self):
        self.openweather_api_key = os.environ.get("OPENWEATHER_API_KEY", self.openweather_api_key)
        self.exchangerate_api_key = os.environ.get("EXCHANGERATE_API_KEY", self.exchangerate_api_key)
        self.github_api_key = os.environ.get("GITHUB_API_KEY", self.github_api_key)

@dataclass
class LambdaSettings:
    """Configurações das funções Lambda"""
    function_name: str = "data-pipeline-handler"
    runtime: str = "python3.9"
    timeout: int = 30
    memory_size: int = 128
    environment_variables: Dict[str, str] = None
    
    def __post_init__(self):
        if self.environment_variables is None:
            self.environment_variables = {
                "DYNAMODB_TABLE": os.environ.get("DYNAMODB_TABLE", "data-pipeline-table"),
                "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
            }

@dataclass
class DashboardSettings:
    """Configurações do dashboard"""
    host: str = "0.0.0.0"
    port: int = 8501
    debug: bool = False
    theme: str = "light"
    
    def __post_init__(self):
        self.host = os.environ.get("STREAMLIT_HOST", self.host)
        self.port = int(os.environ.get("STREAMLIT_PORT", self.port))
        self.debug = os.environ.get("STREAMLIT_DEBUG", "false").lower() == "true"

@dataclass
class LoggingSettings:
    """Configurações de logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    
    def __post_init__(self):
        self.level = os.environ.get("LOG_LEVEL", self.level)
        self.file_path = os.environ.get("LOG_FILE", self.file_path)

@dataclass
class ProjectSettings:
    """Configurações gerais do projeto"""
    name: str = "Cloud Data Orchestrator"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    def __post_init__(self):
        self.environment = os.environ.get("ENVIRONMENT", self.environment)
        self.debug = os.environ.get("DEBUG", "false").lower() == "true"

class ConfigManager:
    """Gerenciador de configurações do projeto"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.json"
        self.config_dir = Path(__file__).parent
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Carrega configurações do arquivo ou cria padrões"""
        config_path = self.config_dir / self.config_file
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                print(f"✅ Configurações carregadas de {config_path}")
                return config_data
            except Exception as e:
                print(f"⚠️  Erro ao carregar configurações: {e}")
                print("📝 Criando configurações padrão...")
        
        # Criar configurações padrão
        default_config = {
            "aws": asdict(AWSSettings()),
            "database": asdict(DatabaseSettings()),
            "api": asdict(APISettings()),
            "lambda": asdict(LambdaSettings()),
            "dashboard": asdict(DashboardSettings()),
            "logging": asdict(LoggingSettings()),
            "project": asdict(ProjectSettings())
        }
        
        # Salvar configurações padrão
        self._save_settings(default_config)
        return default_config
    
    def _save_settings(self, config_data: Dict[str, Any]) -> None:
        """Salva configurações no arquivo"""
        config_path = self.config_dir / self.config_file
        
        try:
            # Criar diretório se não existir
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Configurações salvas em {config_path}")
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")
    
    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """Obtém uma configuração específica"""
        try:
            return self.settings.get(section, {}).get(key, default)
        except KeyError:
            return default
    
    def set_setting(self, section: str, key: str, value: Any) -> None:
        """Define uma configuração específica"""
        if section not in self.settings:
            self.settings[section] = {}
        
        self.settings[section][key] = value
        self._save_settings(self.settings)
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Atualiza múltiplas configurações"""
        for section, section_data in new_settings.items():
            if section not in self.settings:
                self.settings[section] = {}
            
            for key, value in section_data.items():
                self.settings[section][key] = value
        
        self._save_settings(self.settings)
    
    def get_aws_settings(self) -> AWSSettings:
        """Retorna configurações AWS"""
        return AWSSettings(**self.settings.get("aws", {}))
    
    def get_database_settings(self) -> DatabaseSettings:
        """Retorna configurações do banco"""
        return DatabaseSettings(**self.settings.get("database", {}))
    
    def get_api_settings(self) -> APISettings:
        """Retorna configurações das APIs"""
        return APISettings(**self.settings.get("api", {}))
    
    def get_lambda_settings(self) -> LambdaSettings:
        """Retorna configurações Lambda"""
        return LambdaSettings(**self.settings.get("lambda", {}))
    
    def get_dashboard_settings(self) -> DashboardSettings:
        """Retorna configurações do dashboard"""
        return DashboardSettings(**self.settings.get("dashboard", {}))
    
    def get_logging_settings(self) -> LoggingSettings:
        """Retorna configurações de logging"""
        return LoggingSettings(**self.settings.get("logging", {}))
    
    def get_project_settings(self) -> ProjectSettings:
        """Retorna configurações do projeto"""
        return ProjectSettings(**self.settings.get("project", {}))
    
    def validate_settings(self) -> Dict[str, bool]:
        """Valida todas as configurações"""
        validation_results = {}
        
        # Validar AWS
        aws_settings = self.get_aws_settings()
        validation_results["aws"] = bool(
            aws_settings.access_key_id and 
            aws_settings.secret_access_key and 
            aws_settings.region
        )
        
        # Validar Database
        db_settings = self.get_database_settings()
        validation_results["database"] = bool(db_settings.table_name)
        
        # Validar APIs
        api_settings = self.get_api_settings()
        validation_results["api"] = bool(
            api_settings.openweather_api_key or 
            api_settings.exchangerate_api_key
        )
        
        # Validar Lambda
        lambda_settings = self.get_lambda_settings()
        validation_results["lambda"] = bool(lambda_settings.function_name)
        
        return validation_results
    
    def print_summary(self) -> None:
        """Imprime resumo das configurações"""
        print("\n" + "=" * 60)
        print("📋 RESUMO DAS CONFIGURAÇÕES")
        print("=" * 60)
        
        # Projeto
        project = self.get_project_settings()
        print(f"🏗️  Projeto: {project.name} v{project.version}")
        print(f"🌍 Ambiente: {project.environment}")
        print(f"🐛 Debug: {project.debug}")
        
        # AWS
        aws = self.get_aws_settings()
        print(f"\n☁️  AWS:")
        print(f"   Região: {aws.region}")
        print(f"   Access Key: {'✅ Configurada' if aws.access_key_id else '❌ Não configurada'}")
        print(f"   Secret Key: {'✅ Configurada' if aws.secret_access_key else '❌ Não configurada'}")
        
        # Database
        db = self.get_database_settings()
        print(f"\n🗄️  Database:")
        print(f"   Tabela: {db.table_name}")
        print(f"   Billing: {db.billing_mode}")
        
        # APIs
        api = self.get_api_settings()
        print(f"\n🔌 APIs:")
        print(f"   OpenWeather: {'✅ Configurada' if api.openweather_api_key else '❌ Não configurada'}")
        print(f"   Exchange Rate: {'✅ Configurada' if api.exchangerate_api_key else '❌ Não configurada'}")
        
        # Dashboard
        dashboard = self.get_dashboard_settings()
        print(f"\n📊 Dashboard:")
        print(f"   Host: {dashboard.host}:{dashboard.port}")
        print(f"   Tema: {dashboard.theme}")
        
        # Validação
        validation = self.validate_settings()
        print(f"\n✅ Validação:")
        for section, is_valid in validation.items():
            status = "✅ OK" if is_valid else "❌ Problemas"
            print(f"   {section}: {status}")
        
        print("=" * 60)

def main():
    """Função principal para teste"""
    config_manager = ConfigManager()
    config_manager.print_summary()

if __name__ == "__main__":
    main()
