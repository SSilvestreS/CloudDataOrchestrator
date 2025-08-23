"""
Sistema Integrado CloudDataOrchestrator v2.0
Integra todas as funcionalidades: alertas, ML, provedores de dados e dashboard
"""

import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os

from utils.logger import get_logger
from utils.metrics import MetricsCollector
from utils.cache import Cache
from utils.validator import DataValidator
from utils.resilience import CircuitBreaker, RetryHandler
from utils.alerts import create_alert_manager, AlertManager
from utils.anomaly_detector import create_anomaly_detector, AnomalyDetector
from data_pipeline.data_providers import create_data_provider_manager, DataProviderManager

logger = get_logger(__name__)


class CloudDataOrchestratorV2:
    """Sistema integrado principal da versão 2.0"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # Componentes principais
        self.metrics = MetricsCollector()
        self.cache = Cache()
        self.validator = DataValidator()
        
        # Novos componentes v2.0
        self.alert_manager: Optional[AlertManager] = None
        self.anomaly_detector: Optional[AnomalyDetector] = None
        self.data_provider_manager: Optional[DataProviderManager] = None
        
        # Estado do sistema
        self.is_running = False
        self.start_time = None
        self.health_status = "healthy"
        
        # Threads de monitoramento
        self.monitoring_thread = None
        self.alert_thread = None
        self.ml_thread = None
        
        # Estatísticas
        self.stats = {
            "start_time": None,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "alerts_triggered": 0,
            "anomalies_detected": 0,
            "data_providers_active": 0
        }
        
        self.logger.info("CloudDataOrchestrator v2.0 inicializando...")
    
    async def initialize(self):
        """Inicializa todos os componentes do sistema"""
        try:
            self.logger.info("Inicializando componentes do sistema...")
            
            # Inicializar sistema de alertas
            if self.config.get("alerts_enabled", True):
                self.alert_manager = create_alert_manager(self.config)
                self.logger.info("✅ Sistema de alertas inicializado")
            
            # Inicializar detector de anomalias
            if self.config.get("ml_enabled", True):
                self.anomaly_detector = create_anomaly_detector(self.config)
                self.logger.info("✅ Sistema de ML inicializado")
            
            # Inicializar gerenciador de provedores
            if self.config.get("providers_enabled", True):
                self.data_provider_manager = create_data_provider_manager(self.config)
                self.logger.info("✅ Gerenciador de provedores inicializado")
            
            # Verificar saúde dos componentes
            await self._health_check()
            
            self.logger.info("🎉 CloudDataOrchestrator v2.0 inicializado com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização: {e}")
            self.health_status = "unhealthy"
            return False
    
    async def start(self):
        """Inicia o sistema integrado"""
        if self.is_running:
            self.logger.warning("Sistema já está rodando")
            return
        
        try:
            self.logger.info("🚀 Iniciando CloudDataOrchestrator v2.0...")
            
            # Inicializar componentes
            if not await self.initialize():
                raise Exception("Falha na inicialização")
            
            self.is_running = True
            self.start_time = datetime.now()
            self.stats["start_time"] = self.start_time
            
            # Iniciar threads de monitoramento
            self._start_monitoring_threads()
            
            # Loop principal
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar sistema: {e}")
            self.health_status = "error"
            raise
    
    async def stop(self):
        """Para o sistema integrado"""
        self.logger.info("🛑 Parando CloudDataOrchestrator v2.0...")
        
        self.is_running = False
        
        # Parar threads de monitoramento
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        if self.alert_thread and self.alert_thread.is_alive():
            self.alert_thread.join(timeout=5)
        
        if self.ml_thread and self.ml_thread.is_alive():
            self.ml_thread.join(timeout=5)
        
        self.logger.info("✅ Sistema parado com sucesso")
    
    def _start_monitoring_threads(self):
        """Inicia threads de monitoramento em background"""
        # Thread de monitoramento geral
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_worker,
            daemon=True
        )
        self.monitoring_thread.start()
        
        # Thread de verificação de alertas
        if self.alert_manager:
            self.alert_thread = threading.Thread(
                target=self._alert_worker,
                daemon=True
            )
            self.alert_thread.start()
        
        # Thread de detecção de anomalias
        if self.anomaly_detector:
            self.ml_thread = threading.Thread(
                target=self._ml_worker,
                daemon=True
            )
            self.ml_thread.start()
        
        self.logger.info("Threads de monitoramento iniciados")
    
    def _monitoring_worker(self):
        """Worker para monitoramento contínuo"""
        while self.is_running:
            try:
                # Coletar métricas do sistema
                system_metrics = self.metrics.get_system_metrics()
                pipeline_metrics = self.metrics.get_pipeline_metrics()
                cache_metrics = self.metrics.get_cache_metrics()
                
                # Verificar saúde do sistema
                self._check_system_health(system_metrics)
                
                # Atualizar estatísticas
                self._update_stats()
                
                # Aguardar próximo ciclo
                time.sleep(self.config.get("metrics_interval", 60))
                
            except Exception as e:
                self.logger.error(f"Erro no worker de monitoramento: {e}")
                time.sleep(10)
    
    def _alert_worker(self):
        """Worker para verificação de alertas"""
        while self.is_running and self.alert_manager:
            try:
                # Verificar alertas
                triggered_alerts = self.alert_manager.check_alerts()
                
                if triggered_alerts:
                    self.logger.info(f"🚨 {len(triggered_alerts)} alertas disparados")
                    self.stats["alerts_triggered"] += len(triggered_alerts)
                
                # Aguardar próximo ciclo
                time.sleep(self.config.get("alert_check_interval", 30))
                
            except Exception as e:
                self.logger.error(f"Erro no worker de alertas: {e}")
                time.sleep(10)
    
    def _ml_worker(self):
        """Worker para detecção de anomalias"""
        while self.is_running and self.anomaly_detector:
            try:
                # Obter métricas para análise
                system_metrics = self.metrics.get_system_metrics()
                
                # Detectar anomalias em métricas principais
                metrics_to_check = [
                    ("system.cpu_percent", [system_metrics["cpu_percent"]]),
                    ("system.memory_percent", [system_metrics["memory_percent"]]),
                    ("system.disk_percent", [system_metrics.get("disk_percent", 0)])
                ]
                
                for metric_name, values in metrics_to_check:
                    if values and values[0] is not None:
                        anomalies = self.anomaly_detector.detect_anomalies(metric_name, values)
                        if anomalies:
                            self.logger.info(f"🔍 {len(anomalies)} anomalias detectadas em {metric_name}")
                            self.stats["anomalies_detected"] += len(anomalies)
                
                # Aguardar próximo ciclo
                time.sleep(self.config.get("ml_check_interval", 120))
                
            except Exception as e:
                self.logger.error(f"Erro no worker de ML: {e}")
                time.sleep(10)
    
    def _check_system_health(self, system_metrics: Dict[str, Any]):
        """Verifica a saúde do sistema baseado nas métricas"""
        try:
            # Verificar CPU
            cpu_percent = system_metrics.get("cpu_percent", 0)
            if cpu_percent > self.config.get("alert_cpu_threshold", 80):
                self.health_status = "warning"
                self.logger.warning(f"CPU alto: {cpu_percent}%")
            
            # Verificar memória
            memory_percent = system_metrics.get("memory_percent", 0)
            if memory_percent > self.config.get("alert_memory_threshold", 85):
                self.health_status = "warning"
                self.logger.warning(f"Memória alta: {memory_percent}%")
            
            # Verificar pipeline
            pipeline_metrics = self.metrics.get_pipeline_metrics()
            error_rate = pipeline_metrics.get("error_rate", 0)
            if error_rate > self.config.get("alert_error_rate_threshold", 5):
                self.health_status = "warning"
                self.logger.warning(f"Taxa de erro alta: {error_rate}%")
            
            # Se tudo estiver OK, marcar como saudável
            if self.health_status != "error":
                self.health_status = "healthy"
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar saúde do sistema: {e}")
            self.health_status = "error"
    
    def _update_stats(self):
        """Atualiza estatísticas do sistema"""
        try:
            # Atualizar contadores de requisições
            if self.data_provider_manager:
                provider_stats = self.data_provider_manager.get_request_stats()
                self.stats["total_requests"] = provider_stats.get("total_requests", 0)
                self.stats["successful_requests"] = provider_stats.get("successful_requests", 0)
                self.stats["failed_requests"] = provider_stats.get("failed_requests", 0)
                self.stats["data_providers_active"] = len(self.data_provider_manager.providers)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar estatísticas: {e}")
    
    async def _main_loop(self):
        """Loop principal do sistema"""
        self.logger.info("🔄 Loop principal iniciado")
        
        while self.is_running:
            try:
                # Executar pipeline de dados
                await self._execute_data_pipeline()
                
                # Executar manutenção
                await self._maintenance()
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.config.get("main_cycle_interval", 300))
                
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                await asyncio.sleep(60)
    
    async def _execute_data_pipeline(self):
        """Executa o pipeline de dados"""
        try:
            self.logger.info("📊 Executando pipeline de dados...")
            
            if self.data_provider_manager:
                # Executar coleta de dados de múltiplos provedores
                requests = [
                    {"provider": "alpha_vantage", "endpoint": "TIME_SERIES_DAILY", "params": {"symbol": "AAPL"}},
                    {"provider": "openweather", "endpoint": "weather", "params": {"q": "São Paulo,BR"}},
                    {"provider": "newsapi", "endpoint": "top-headlines", "params": {"country": "br"}}
                ]
                
                responses = await self.data_provider_manager.fetch_multiple_providers(requests)
                
                # Processar respostas
                for response in responses:
                    if response.status == "success":
                        # Validar dados
                        if self.validator.validate_data(response.data):
                            # Salvar no cache
                            cache_key = f"provider_data_{response.provider}_{response.timestamp.isoformat()}"
                            self.cache.set(cache_key, response.data, ttl=3600)
                            
                            # Detectar anomalias se habilitado
                            if self.anomaly_detector and response.data:
                                # Extrair valores numéricos para análise
                                numeric_values = self._extract_numeric_values(response.data)
                                if numeric_values:
                                    anomalies = self.anomaly_detector.detect_anomalies(
                                        f"provider.{response.provider}", 
                                        numeric_values
                                    )
                                    if anomalies:
                                        self.logger.info(f"🔍 {len(anomalies)} anomalias detectadas em dados de {response.provider}")
                        
                        self.stats["successful_requests"] += 1
                    else:
                        self.stats["failed_requests"] += 1
                        self.logger.error(f"Erro na requisição para {response.provider}: {response.error_message}")
            
            self.logger.info("✅ Pipeline de dados executado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao executar pipeline de dados: {e}")
    
    def _extract_numeric_values(self, data: Any) -> List[float]:
        """Extrai valores numéricos de dados para análise de anomalias"""
        numeric_values = []
        
        try:
            if isinstance(data, dict):
                for value in data.values():
                    if isinstance(value, (int, float)):
                        numeric_values.append(float(value))
                    elif isinstance(value, dict):
                        numeric_values.extend(self._extract_numeric_values(value))
                    elif isinstance(value, list):
                        numeric_values.extend(self._extract_numeric_values(value))
            
            elif isinstance(data, list):
                for item in data:
                    numeric_values.extend(self._extract_numeric_values(item))
            
            elif isinstance(data, (int, float)):
                numeric_values.append(float(data))
                
        except Exception as e:
            self.logger.error(f"Erro ao extrair valores numéricos: {e}")
        
        return numeric_values
    
    async def _maintenance(self):
        """Executa tarefas de manutenção"""
        try:
            self.logger.info("🔧 Executando manutenção...")
            
            # Limpar cache antigo
            self.cache.cleanup()
            
            # Limpar logs antigos
            self._cleanup_old_logs()
            
            # Limpar dados antigos de alertas e anomalias
            if self.alert_manager:
                self.alert_manager.cleanup_old_alerts(days=7)
            
            if self.anomaly_detector:
                self.anomaly_detector.cleanup_old_anomalies(days=7)
            
            # Limpar dados antigos de provedores
            if self.data_provider_manager:
                self.data_provider_manager.cleanup_old_data(days=7)
            
            self.logger.info("✅ Manutenção concluída")
            
        except Exception as e:
            self.logger.error(f"Erro na manutenção: {e}")
    
    def _cleanup_old_logs(self):
        """Remove logs antigos"""
        try:
            logs_dir = "logs"
            if not os.path.exists(logs_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for filename in os.listdir(logs_dir):
                file_path = os.path.join(logs_dir, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        self.logger.info(f"Log antigo removido: {filename}")
                        
        except Exception as e:
            self.logger.error(f"Erro ao limpar logs: {e}")
    
    async def _health_check(self):
        """Verifica a saúde de todos os componentes"""
        try:
            health_status = {
                "system": "healthy",
                "components": {}
            }
            
            # Verificar métricas
            try:
                self.metrics.get_system_metrics()
                health_status["components"]["metrics"] = "healthy"
            except Exception as e:
                health_status["components"]["metrics"] = f"unhealthy: {e}"
                health_status["system"] = "unhealthy"
            
            # Verificar cache
            try:
                self.cache.get("health_check")
                health_status["components"]["cache"] = "healthy"
            except Exception as e:
                health_status["components"]["cache"] = f"unhealthy: {e}"
                health_status["system"] = "unhealthy"
            
            # Verificar validador
            try:
                self.validator.validate_data({"test": "data"})
                health_status["components"]["validator"] = "healthy"
            except Exception as e:
                health_status["components"]["validator"] = f"unhealthy: {e}"
                health_status["system"] = "unhealthy"
            
            # Verificar sistema de alertas
            if self.alert_manager:
                try:
                    self.alert_manager.get_alert_stats()
                    health_status["components"]["alerts"] = "healthy"
                except Exception as e:
                    health_status["components"]["alerts"] = f"unhealthy: {e}"
                    health_status["system"] = "unhealthy"
            
            # Verificar detector de anomalias
            if self.anomaly_detector:
                try:
                    self.anomaly_detector.get_anomaly_stats()
                    health_status["components"]["ml"] = "healthy"
                except Exception as e:
                    health_status["components"]["ml"] = f"unhealthy: {e}"
                    health_status["system"] = "unhealthy"
            
            # Verificar gerenciador de provedores
            if self.data_provider_manager:
                try:
                    self.data_provider_manager.get_provider_status()
                    health_status["components"]["providers"] = "healthy"
                except Exception as e:
                    health_status["components"]["providers"] = f"unhealthy: {e}"
                    health_status["system"] = "unhealthy"
            
            self.health_status = health_status["system"]
            
            if health_status["system"] == "healthy":
                self.logger.info("✅ Health check: Todos os componentes saudáveis")
            else:
                self.logger.warning(f"⚠️ Health check: Sistema com problemas - {health_status}")
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Erro no health check: {e}")
            self.health_status = "error"
            return {"system": "error", "error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema"""
        return {
            "version": "2.0.0",
            "status": "running" if self.is_running else "stopped",
            "health": self.health_status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": str(datetime.now() - self.start_time) if self.start_time else None,
            "stats": self.stats,
            "components": {
                "alerts": "enabled" if self.alert_manager else "disabled",
                "ml": "enabled" if self.anomaly_detector else "disabled",
                "providers": "enabled" if self.data_provider_manager else "disabled"
            }
        }
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Retorna métricas detalhadas do sistema"""
        try:
            return {
                "system": self.metrics.get_system_metrics(),
                "pipeline": self.metrics.get_pipeline_metrics(),
                "cache": self.metrics.get_cache_metrics(),
                "alerts": self.alert_manager.get_alert_stats() if self.alert_manager else {},
                "anomalies": self.anomaly_detector.get_anomaly_stats() if self.anomaly_detector else {},
                "providers": self.data_provider_manager.get_request_stats() if self.data_provider_manager else {}
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter métricas detalhadas: {e}")
            return {}


# Função de conveniência para criar instância
def create_orchestrator(config: Dict[str, Any] = None) -> CloudDataOrchestratorV2:
    """Cria uma instância do CloudDataOrchestrator v2.0"""
    if config is None:
        config = {
            "alerts_enabled": True,
            "ml_enabled": True,
            "providers_enabled": True,
            "metrics_interval": 60,
            "alert_check_interval": 30,
            "ml_check_interval": 120,
            "main_cycle_interval": 300,
            "alert_cpu_threshold": 80,
            "alert_memory_threshold": 85,
            "alert_error_rate_threshold": 5
        }
    
    return CloudDataOrchestratorV2(config)


async def main():
    """Função principal para execução"""
    try:
        # Criar e configurar o orquestrador
        config = {
            "alerts_enabled": True,
            "ml_enabled": True,
            "providers_enabled": True,
            "metrics_interval": 30,
            "alert_check_interval": 15,
            "ml_check_interval": 60,
            "main_cycle_interval": 180
        }
        
        orchestrator = create_orchestrator(config)
        
        # Iniciar o sistema
        await orchestrator.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupção recebida, parando sistema...")
        if 'orchestrator' in locals():
            await orchestrator.stop()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        if 'orchestrator' in locals():
            await orchestrator.stop()


if __name__ == "__main__":
    print("🚀 Iniciando CloudDataOrchestrator v2.0...")
    asyncio.run(main())
