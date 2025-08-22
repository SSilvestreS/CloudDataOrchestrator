#!/usr/bin/env python3
"""
Sistema de Métricas e Monitoramento para Cloud Data Orchestrator
Coleta e analisa métricas de performance e uso do sistema
"""

import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from functools import wraps

@dataclass
class MetricPoint:
    """Ponto de métrica individual"""
    timestamp: datetime
    value: float
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "tags": self.tags
        }

@dataclass
class MetricSummary:
    """Resumo estatístico de uma métrica"""
    count: int
    min_value: float
    max_value: float
    mean: float
    median: float
    std_dev: float
    p95: float
    p99: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)

class MetricsCollector:
    """Coletor de métricas do sistema"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.gauges: Dict[str, float] = {}
    
    def record_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Registra um contador"""
        if tags is None:
            tags = {}
        
        self.counters[name] += value
        
        # Adicionar à história
        metric_point = MetricPoint(
            timestamp=datetime.now(),
            value=float(value),
            tags=tags
        )
        self.metrics[name].append(metric_point)
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Registra um timer"""
        if tags is None:
            tags = {}
        
        self.timers[name].append(duration)
        
        # Manter apenas os últimos valores
        if len(self.timers[name]) > self.max_history:
            self.timers[name] = self.timers[name][-self.max_history:]
        
        # Adicionar à história
        metric_point = MetricPoint(
            timestamp=datetime.now(),
            value=duration,
            tags=tags
        )
        self.metrics[name].append(metric_point)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Define um gauge"""
        if tags is None:
            tags = {}
        
        self.gauges[name] = value
        
        # Adicionar à história
        metric_point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags
        )
        self.metrics[name].append(metric_point)
    
    def get_metric_summary(self, name: str, window_minutes: int = 60) -> Optional[MetricSummary]:
        """Obtém resumo de uma métrica em uma janela de tempo"""
        if name not in self.metrics:
            return None
        
        # Filtrar por janela de tempo
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_metrics = [
            m for m in self.metrics[name] 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        values = [m.value for m in recent_metrics]
        
        return MetricSummary(
            count=len(values),
            min_value=min(values),
            max_value=max(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            p95=statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
            p99=statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
        )
    
    def get_all_summaries(self, window_minutes: int = 60) -> Dict[str, MetricSummary]:
        """Obtém resumos de todas as métricas"""
        summaries = {}
        
        for metric_name in self.metrics.keys():
            summary = self.get_metric_summary(metric_name, window_minutes)
            if summary:
                summaries[metric_name] = summary
        
        return summaries
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Exporta métricas em diferentes formatos"""
        if format_type == "json":
            return self._export_json()
        elif format_type == "prometheus":
            return self._export_prometheus()
        else:
            raise ValueError(f"Formato não suportado: {format_type}")
    
    def _export_json(self) -> str:
        """Exporta métricas em formato JSON"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timers": {name: {
                "count": len(values),
                "mean": statistics.mean(values) if values else 0.0,
                "min": min(values) if values else 0.0,
                "max": max(values) if values else 0.0
            } for name, values in self.timers.items()},
            "summaries": {
                name: summary.to_dict() 
                for name, summary in self.get_all_summaries().items()
            }
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
    
    def _export_prometheus(self) -> str:
        """Exporta métricas em formato Prometheus"""
        lines = []
        
        # Counters
        for name, value in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Gauges
        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        # Histograms (timers)
        for name, values in self.timers.items():
            if values:
                lines.append(f"# TYPE {name} histogram")
                lines.append(f"{name}_count {len(values)}")
                lines.append(f"{name}_sum {sum(values)}")
                lines.append(f"{name}_mean {statistics.mean(values)}")
                lines.append(f"{name}_min {min(values)}")
                lines.append(f"{name}_max {max(values)}")
        
        return "\n".join(lines)
    
    def clear_old_metrics(self, older_than_hours: int = 24) -> int:
        """Remove métricas antigas"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        removed_count = 0
        
        for metric_name in list(self.metrics.keys()):
            original_count = len(self.metrics[metric_name])
            self.metrics[metric_name] = deque(
                [m for m in self.metrics[metric_name] if m.timestamp >= cutoff_time],
                maxlen=self.max_history
            )
            removed_count += original_count - len(self.metrics[metric_name])
        
        return removed_count

class MetricsDecorator:
    """Decorator para métricas automáticas"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Registrar sucesso
                self.collector.record_timer(f"{func.__module__}.{func.__name__}.duration", duration)
                self.collector.record_counter(f"{func.__module__}.{func.__name__}.success", 1)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Registrar falha
                self.collector.record_timer(f"{func.__module__}.{func.__name__}.duration", duration)
                self.collector.record_counter(f"{func.__module__}.{func.__name__}.error", 1)
                
                raise
        
        return wrapper

class HealthChecker:
    """Verificador de saúde do sistema"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.health_checks: Dict[str, Callable] = {}
    
    def register_health_check(self, name: str, check_func: Callable) -> None:
        """Registra uma verificação de saúde"""
        self.health_checks[name] = check_func
    
    def run_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """Executa todas as verificações de saúde"""
        results = {}
        
        for name, check_func in self.health_checks.items():
            start_time = time.time()
            
            try:
                result = check_func()
                duration = time.time() - start_time
                
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                    "details": result if isinstance(result, dict) else {"result": result}
                }
                
                # Registrar métricas
                self.collector.record_timer(f"health_check.{name}.duration", duration)
                self.collector.record_counter(f"health_check.{name}.success", 1 if result else 0)
                
            except Exception as e:
                duration = time.time() - start_time
                
                results[name] = {
                    "status": "error",
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
                
                # Registrar métricas
                self.collector.record_timer(f"health_check.{name}.duration", duration)
                self.collector.record_counter(f"health_check.{name}.error", 1)
        
        return results
    
    def get_system_health(self) -> Dict[str, Any]:
        """Obtém saúde geral do sistema"""
        health_checks = self.run_health_checks()
        
        total_checks = len(health_checks)
        healthy_checks = sum(1 for check in health_checks.values() if check["status"] == "healthy")
        error_checks = sum(1 for check in health_checks.values() if check["status"] == "error")
        
        overall_status = "healthy" if healthy_checks == total_checks else "degraded" if error_checks == 0 else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_checks,
                "healthy": healthy_checks,
                "degraded": total_checks - healthy_checks - error_checks,
                "error": error_checks
            },
            "checks": health_checks
        }

def main():
    """Função principal para teste"""
    # Criar coletor de métricas
    collector = MetricsCollector()
    
    # Registrar algumas métricas de exemplo
    collector.record_counter("requests.total", 100)
    collector.record_counter("requests.success", 95)
    collector.record_counter("requests.error", 5)
    
    collector.record_timer("response.time", 0.15)
    collector.record_timer("response.time", 0.12)
    collector.record_timer("response.time", 0.18)
    
    collector.set_gauge("memory.usage", 75.5)
    collector.set_gauge("cpu.usage", 45.2)
    
    # Obter resumos
    print("📊 Resumos das Métricas:")
    summaries = collector.get_all_summaries()
    for name, summary in summaries.items():
        print(f"\n{name}:")
        print(f"  Count: {summary.count}")
        print(f"  Mean: {summary.mean:.3f}")
        print(f"  P95: {summary.p95:.3f}")
    
    # Exportar métricas
    print("\n📋 Export JSON:")
    print(collector.export_metrics("json"))
    
    print("\n📋 Export Prometheus:")
    print(collector.export_metrics("prometheus"))
    
    # Testar health checker
    health_checker = HealthChecker(collector)
    
    def check_database():
        return True
    
    def check_api():
        return {"status": "ok", "response_time": 0.1}
    
    def check_disk():
        return False
    
    health_checker.register_health_check("database", check_database)
    health_checker.register_health_check("api", check_api)
    health_checker.register_health_check("disk", check_disk)
    
    print("\n🏥 Health Check:")
    health_status = health_checker.get_system_health()
    print(json.dumps(health_status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
