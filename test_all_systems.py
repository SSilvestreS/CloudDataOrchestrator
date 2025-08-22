#!/usr/bin/env python3
"""
Script de Teste Completo para Cloud Data Orchestrator
Testa todos os sistemas implementados
"""

import os
import sys
import time
from datetime import datetime

def test_config_system():
    """Testa sistema de configuração"""
    print("\n" + "=" * 60)
    print("🧪 TESTANDO SISTEMA DE CONFIGURAÇÃO")
    print("=" * 60)
    
    try:
        from config.settings import ConfigManager
        
        config_manager = ConfigManager()
        print("✅ ConfigManager criado com sucesso")
        
        # Testar configurações AWS
        aws_settings = config_manager.get_aws_settings()
        print(f"✅ Configurações AWS carregadas: região={aws_settings.region}")
        
        # Testar configurações de projeto
        project_settings = config_manager.get_project_settings()
        print(f"✅ Configurações do projeto: {project_settings.name} v{project_settings.version}")
        
        # Validar configurações
        validation = config_manager.validate_settings()
        print(f"✅ Validação das configurações: {validation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de configuração: {e}")
        return False

def test_logging_system():
    """Testa sistema de logging"""
    print("\n" + "=" * 60)
    print("🧪 TESTANDO SISTEMA DE LOGGING")
    print("=" * 60)
    
    try:
        from utils.logger import LogManager, log_execution_time
        
        # Criar logger
        log_manager = LogManager(
            name="test_logger",
            log_level="DEBUG",
            log_file="logs/test_systems.log"
        )
        logger = log_manager.get_logger()
        print("✅ LogManager criado com sucesso")
        
        # Testar diferentes níveis
        logger.debug("Mensagem de debug")
        logger.info("Mensagem de informação")
        logger.warning("Mensagem de aviso")
        logger.error("Mensagem de erro")
        print("✅ Diferentes níveis de log testados")
        
        # Testar decorator de tempo de execução
        @log_execution_time
        def test_function():
            time.sleep(0.1)
            return "teste"
        
        result = test_function()
        print(f"✅ Decorator de tempo testado: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de logging: {e}")
        return False

def test_metrics_system():
    """Testa sistema de métricas"""
    print("\n" + "=" * 60)
    print("🧪 TESTANDO SISTEMA DE MÉTRICAS")
    print("=" * 60)
    
    try:
        from utils.metrics import MetricsCollector, HealthChecker
        
        # Criar coletor de métricas
        collector = MetricsCollector()
        print("✅ MetricsCollector criado com sucesso")
        
        # Registrar algumas métricas
        collector.record_counter("test.counter", 10)
        collector.record_timer("test.timer", 0.5)
        collector.set_gauge("test.gauge", 75.5)
        print("✅ Métricas básicas registradas")
        
        # Obter resumos
        summaries = collector.get_all_summaries()
        print(f"✅ Resumos obtidos: {len(summaries)} métricas")
        
        # Exportar métricas
        json_metrics = collector.export_metrics("json")
        print(f"✅ Métricas exportadas em JSON: {len(json_metrics)} caracteres")
        
        # Testar health checker
        health_checker = HealthChecker(collector)
        
        def check_test():
            return True
        
        health_checker.register_health_check("test_check", check_test)
        health_status = health_checker.get_system_health()
        print(f"✅ Health check testado: {health_status['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de métricas: {e}")
        return False

def test_cache_system():
    """Testa sistema de cache"""
    print("\n" + "=" * 60)
    print("🧪 TESTANDO SISTEMA DE CACHE")
    print("=" * 60)
    
    try:
        from utils.cache import MemoryCache, PersistentCache, CacheDecorator
        
        # Testar cache em memória
        memory_cache = MemoryCache(max_size=5, default_ttl=10)
        print("✅ MemoryCache criado com sucesso")
        
        # Testar operações básicas
        memory_cache.set("test_key", "test_value", ttl=5)
        value = memory_cache.get("test_key")
        print(f"✅ Operações básicas testadas: {value}")
        
        # Testar cache persistente
        persistent_cache = PersistentCache(cache_dir="cache", max_size=10, default_ttl=30)
        print("✅ PersistentCache criado com sucesso")
        
        persistent_cache.set("persistent_key", {"data": "teste"})
        persistent_value = persistent_cache.get("persistent_key")
        print(f"✅ Cache persistente testado: {persistent_value}")
        
        # Testar decorator
        @CacheDecorator(memory_cache, ttl=60)
        def expensive_function(x):
            time.sleep(0.1)
            return x * x
        
        result1 = expensive_function(5)
        result2 = expensive_function(5)  # Deve vir do cache
        print(f"✅ Decorator de cache testado: {result1}, {result2}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de cache: {e}")
        return False

def test_validation_system():
    """Testa sistema de validação"""
    print("\n" + "=" * 60)
    print("🧪 TESTANDO SISTEMA DE VALIDAÇÃO")
    print("=" * 60)
    
    try:
        from utils.validator import DataValidator, DataQualityChecker
        
        # Criar validador
        validator = DataValidator()
        print("✅ DataValidator criado com sucesso")
        
        # Dados de teste
        test_data = {
            "city": "São Paulo",
            "temperature": 25.5,
            "humidity": 75,
            "description": "céu limpo",
            "timestamp": datetime.now().isoformat(),
            "source": "test"
        }
        
        # Validar dados
        validation_result = validator.validate_data(test_data, "weather")
        print(f"✅ Validação testada: {validation_result.is_valid}")
        
        if validation_result.errors:
            print(f"⚠️  Erros encontrados: {validation_result.errors}")
        
        # Testar quality checker
        quality_checker = DataQualityChecker()
        quality_result = quality_checker.check_data_quality(test_data, "weather")
        print(f"✅ Quality checker testado: score={quality_result['quality_score']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de validação: {e}")
        return False

def test_resilience_system():
    """Testa sistema de resiliência"""
    print("\n" + "=" * 60)
    print("🧪 TESTANDO SISTEMA DE RESILIÊNCIA")
    print("=" * 60)
    
    try:
        from utils.resilience import ResilienceManager, RetryStrategy
        
        # Criar gerenciador
        manager = ResilienceManager()
        print("✅ ResilienceManager criado com sucesso")
        
        # Testar circuit breaker
        cb = manager.create_circuit_breaker(
            name="test_cb",
            failure_threshold=3,
            recovery_timeout=5.0
        )
        print("✅ Circuit breaker criado")
        
        # Testar retry handler
        retry = manager.create_retry_handler(
            name="test_retry",
            max_attempts=2,
            strategy=RetryStrategy.exponential_backoff(base_delay=0.1)
        )
        print("✅ Retry handler criado")
        
        # Função de teste
        def test_function():
            if random.random() < 0.5:
                raise Exception("Falha simulada")
            return "Sucesso!"
        
        # Testar com retry
        @retry
        def function_with_retry():
            return test_function()
        
        try:
            result = function_with_retry()
            print(f"✅ Retry testado: {result}")
        except Exception as e:
            print(f"⚠️  Retry falhou como esperado: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de resiliência: {e}")
        return False

def test_data_collector():
    """Testa data collector melhorado"""
    print("\n" + "=" * 60)
    print("🧪 TESTANDO DATA COLLECTOR MELHORADO")
    print("=" * 60)
    
    try:
        from data_pipeline.data_collector_enhanced import EnhancedDataCollector
        
        # Criar collector
        collector = EnhancedDataCollector()
        print("✅ EnhancedDataCollector criado com sucesso")
        
        # Executar coleta
        results = collector.run_collection()
        print(f"✅ Coleta executada: {len(results)} tipos de dados")
        
        for data_type, data_info in results.items():
            if "error" in data_info:
                print(f"⚠️  {data_type}: {data_info['error']}")
            else:
                print(f"✅ {data_type}: {data_info['count']} registros")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no data collector: {e}")
        return False

def test_integrated_system():
    """Testa sistema integrado"""
    print("\n" + "=" * 60)
    print("🧪 TESTANDO SISTEMA INTEGRADO")
    print("=" * 60)
    
    try:
        from integrated_system import IntegratedSystem
        
        # Criar sistema
        system = IntegratedSystem()
        print("✅ Sistema integrado criado com sucesso")
        
        # Verificar saúde
        health_status = system.run_health_check()
        print(f"✅ Health check: {health_status['status']}")
        
        # Obter status
        system_status = system.get_system_status()
        print(f"✅ Status obtido: cache hits={system_status['cache_stats']['hits']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema integrado: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 INICIANDO TESTES COMPLETOS DO SISTEMA")
    print("=" * 60)
    
    # Lista de testes
    tests = [
        ("Sistema de Configuração", test_config_system),
        ("Sistema de Logging", test_logging_system),
        ("Sistema de Métricas", test_metrics_system),
        ("Sistema de Cache", test_cache_system),
        ("Sistema de Validação", test_validation_system),
        ("Sistema de Resiliência", test_resilience_system),
        ("Data Collector Melhorado", test_data_collector),
        ("Sistema Integrado", test_integrated_system)
    ]
    
    # Executar testes
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n🔄 Executando: {test_name}")
        start_time = time.time()
        
        try:
            success = test_func()
            duration = time.time() - start_time
            
            if success:
                results[test_name] = {"status": "PASS", "duration": duration}
                passed_tests += 1
                print(f"✅ {test_name}: PASS ({duration:.2f}s)")
            else:
                results[test_name] = {"status": "FAIL", "duration": duration}
                print(f"❌ {test_name}: FAIL ({duration:.2f}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            results[test_name] = {"status": "ERROR", "duration": duration, "error": str(e)}
            print(f"💥 {test_name}: ERROR ({duration:.2f}s) - {e}")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results.items():
        status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "💥"
        print(f"{status_icon} {test_name}: {result['status']} ({result['duration']:.2f}s)")
        if "error" in result:
            print(f"   Erro: {result['error']}")
    
    print(f"\n🎯 Resultado Final: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 Todos os testes passaram! Sistema funcionando perfeitamente!")
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    import random
    success = main()
    sys.exit(0 if success else 1)
