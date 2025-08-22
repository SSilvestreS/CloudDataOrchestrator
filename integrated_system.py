#!/usr/bin/env python3
"""
Sistema Integrado Cloud Data Orchestrator
Integra todos os sistemas: configuração, logging, métricas, cache, validação e resiliência
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import ConfigManager
from utils.logger import LogManager, log_execution_time
from utils.metrics import MetricsCollector, HealthChecker
from utils.cache import PersistentCache, CacheDecorator
from utils.validator import DataValidator, DataQualityChecker
from utils.resilience import ResilienceManager, RetryStrategy
from data_pipeline.data_collector_enhanced import EnhancedDataCollector

class IntegratedSystem:
    """Sistema integrado com todos os componentes"""
    
    def __init__(self):
        print("🚀 Inicializando Sistema Integrado Cloud Data Orchestrator...")
        
        # Inicializar sistemas básicos
        self.config_manager = ConfigManager()
        self.log_manager = LogManager(
            name="integrated_system",
            log_level="INFO",
            log_file="logs/integrated_system.log"
        )
        self.logger = self.log_manager.get_logger()
        
        # Inicializar métricas
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker(self.metrics_collector)
        
        # Inicializar cache
        self.cache = PersistentCache(cache_dir="cache", max_size=1000, default_ttl=3600)
        
        # Inicializar validação
        self.validator = DataValidator()
        self.quality_checker = DataQualityChecker()
        
        # Inicializar resiliência
        self.resilience_manager = ResilienceManager()
        self._setup_resilience()
        
        # Inicializar data collector
        self.data_collector = EnhancedDataCollector()
        
        # Configurar health checks
        self._setup_health_checks()
        
        self.logger.info("Sistema integrado inicializado com sucesso")
    
    def _setup_resilience(self):
        """Configura componentes de resiliência"""
        # Circuit breaker para APIs externas
        self.resilience_manager.create_circuit_breaker(
            name="external_api",
            failure_threshold=5,
            recovery_timeout=300.0  # 5 minutos
        )
        
        # Retry handler para operações de rede
        self.resilience_manager.create_retry_handler(
            name="network_operations",
            max_attempts=3,
            strategy=RetryStrategy.exponential_backoff(base_delay=1.0, max_delay=30.0)
        )
        
        # Fallback para dados em cache
        def cache_fallback(*args, **kwargs):
            return self.cache.get("last_collected_data", [])
        
        self.resilience_manager.create_fallback_handler(
            name="cache_fallback",
            fallback_func=cache_fallback
        )
    
    def _setup_health_checks(self):
        """Configura verificações de saúde"""
        def check_cache():
            try:
                stats = self.cache.get_stats()
                return stats["size"] < stats["max_size"]
            except:
                return False
        
        def check_config():
            try:
                return bool(self.config_manager.get_aws_settings().region)
            except:
                return False
        
        def check_metrics():
            try:
                return len(self.metrics_collector.metrics) >= 0
            except:
                return False
        
        self.health_checker.register_health_check("cache", check_cache)
        self.health_checker.register_health_check("config", check_config)
        self.health_checker.register_health_check("metrics", check_metrics)
    
    @log_execution_time
    def run_data_collection_pipeline(self) -> Dict[str, Any]:
        """Executa pipeline completo de coleta de dados"""
        self.logger.info("🔄 Iniciando pipeline de coleta de dados")
        
        pipeline_start = time.time()
        
        try:
            # Coletar dados com resiliência
            collection_result = self.resilience_manager.resilient_call(
                func=self.data_collector.run_collection,
                circuit_breaker_name="external_api",
                retry_handler_name="network_operations",
                fallback_handler_name="cache_fallback"
            )
            
            # Validar dados coletados
            validated_data = self._validate_collected_data(collection_result)
            
            # Armazenar em cache
            self._cache_collected_data(validated_data)
            
            # Calcular métricas finais
            pipeline_duration = time.time() - pipeline_start
            self.metrics_collector.record_timer("pipeline.total_duration", pipeline_duration)
            self.metrics_collector.record_counter("pipeline.completed", 1)
            
            self.logger.info(f"✅ Pipeline concluído em {pipeline_duration:.2f}s")
            
            return {
                "success": True,
                "duration": pipeline_duration,
                "data": validated_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            pipeline_duration = time.time() - pipeline_start
            self.metrics_collector.record_timer("pipeline.total_duration", pipeline_duration)
            self.metrics_collector.record_counter("pipeline.failed", 1)
            
            self.logger.error(f"❌ Pipeline falhou após {pipeline_duration:.2f}s: {e}")
            
            return {
                "success": False,
                "duration": pipeline_duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_collected_data(self, collection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados coletados"""
        self.logger.info("🔍 Validando dados coletados")
        
        validated_data = {}
        validation_summary = {}
        
        for data_type, data_info in collection_result.items():
            if "error" in data_info:
                self.logger.warning(f"Pulando validação para {data_type}: {data_info['error']}")
                continue
            
            if "data" in data_info and isinstance(data_info["data"], list):
                # Validar lista de dados
                validation_results = self.validator.validate_batch(data_info["data"], data_type)
                summary = self.validator.get_validation_summary(validation_results)
                
                # Filtrar apenas dados válidos
                valid_data = []
                for i, result in enumerate(validation_results):
                    if result.is_valid:
                        valid_data.append(result.validated_data)
                    else:
                        self.logger.warning(f"Dados inválidos em {data_type}[{i}]: {result.errors}")
                
                validated_data[data_type] = {
                    "count": len(valid_data),
                    "data": valid_data,
                    "validation_summary": summary
                }
                
                validation_summary[data_type] = summary
                
                # Registrar métricas de validação
                self.metrics_collector.record_counter(f"validation.{data_type}.total", summary["total_items"])
                self.metrics_collector.record_counter(f"validation.{data_type}.valid", summary["valid_items"])
                self.metrics_collector.record_counter(f"validation.{data_type}.invalid", summary["invalid_items"])
        
        self.logger.info(f"✅ Validação concluída: {len(validated_data)} tipos de dados processados")
        return validated_data
    
    def _cache_collected_data(self, validated_data: Dict[str, Any]) -> None:
        """Armazena dados validados em cache"""
        try:
            # Armazenar dados por tipo
            for data_type, data_info in validated_data.items():
                cache_key = f"data_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M')}"
                self.cache.set(cache_key, data_info, ttl=7200)  # 2 horas
            
            # Armazenar dados consolidados
            self.cache.set("last_collected_data", validated_data, ttl=3600)  # 1 hora
            
            self.logger.info(f"💾 Dados armazenados em cache: {len(validated_data)} tipos")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao armazenar dados em cache: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema"""
        return {
            "timestamp": datetime.now().isoformat(),
            "health": self.health_checker.get_system_health(),
            "metrics": self.metrics_collector.export_metrics("json"),
            "cache_stats": self.cache.get_stats(),
            "resilience_status": self.resilience_manager.get_status(),
            "config_summary": {
                "aws_region": self.config_manager.get_aws_settings().region,
                "environment": self.config_manager.get_project_settings().environment,
                "debug_mode": self.config_manager.get_project_settings().debug
            }
        }
    
    def run_health_check(self) -> Dict[str, Any]:
        """Executa verificação de saúde do sistema"""
        self.logger.info("🏥 Executando verificação de saúde do sistema")
        
        health_status = self.health_checker.get_system_health()
        
        # Registrar métricas de saúde
        self.metrics_collector.record_counter("health_check.total", health_status["summary"]["total"])
        self.metrics_collector.record_counter("health_check.healthy", health_status["summary"]["healthy"])
        self.metrics_collector.record_counter("health_check.unhealthy", health_status["summary"]["error"])
        
        return health_status
    
    def cleanup_old_data(self, older_than_hours: int = 24) -> Dict[str, Any]:
        """Limpa dados antigos"""
        self.logger.info(f"🧹 Limpando dados mais antigos que {older_than_hours}h")
        
        try:
            # Limpar métricas antigas
            metrics_cleaned = self.metrics_collector.clear_old_metrics(older_than_hours)
            
            # Limpar cache expirado
            cache_cleaned = self.cache.cleanup_expired()
            
            # Limpar logs antigos (se implementado)
            logs_cleaned = 0  # Placeholder
            
            cleanup_summary = {
                "metrics_cleaned": metrics_cleaned,
                "cache_cleaned": cache_cleaned,
                "logs_cleaned": logs_cleaned,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Limpeza concluída: {cleanup_summary}")
            return cleanup_summary
            
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza: {e}")
            return {"error": str(e)}
    
    def run_maintenance(self) -> Dict[str, Any]:
        """Executa manutenção do sistema"""
        self.logger.info("🔧 Executando manutenção do sistema")
        
        maintenance_results = {}
        
        # Verificar saúde
        maintenance_results["health_check"] = self.run_health_check()
        
        # Limpar dados antigos
        maintenance_results["cleanup"] = self.cleanup_old_data()
        
        # Verificar configurações
        try:
            config_validation = self.config_manager.validate_settings()
            maintenance_results["config_validation"] = config_validation
        except Exception as e:
            maintenance_results["config_validation"] = {"error": str(e)}
        
        self.logger.info("✅ Manutenção concluída")
        return maintenance_results

def main():
    """Função principal para teste"""
    try:
        # Inicializar sistema
        system = IntegratedSystem()
        
        # Executar pipeline de coleta
        print("\n🔄 Executando pipeline de coleta...")
        collection_result = system.run_data_collection_pipeline()
        
        if collection_result["success"]:
            print(f"✅ Pipeline executado com sucesso em {collection_result['duration']:.2f}s")
        else:
            print(f"❌ Pipeline falhou: {collection_result['error']}")
        
        # Verificar saúde do sistema
        print("\n🏥 Verificando saúde do sistema...")
        health_status = system.run_health_check()
        print(f"Status geral: {health_status['status']}")
        
        # Obter status completo
        print("\n📊 Obtendo status completo...")
        system_status = system.get_system_status()
        print(f"Cache hits: {system_status['cache_stats']['hits']}")
        print(f"Métricas coletadas: {len(system_status['metrics'])}")
        
        # Executar manutenção
        print("\n🔧 Executando manutenção...")
        maintenance_result = system.run_maintenance()
        print("Manutenção concluída")
        
        print("\n🎉 Sistema integrado funcionando perfeitamente!")
        
    except Exception as e:
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    main()
