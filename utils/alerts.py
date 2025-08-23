"""
Sistema de Alertas Avançado para CloudDataOrchestrator
Implementa diferentes tipos de alertas, thresholds configuráveis e múltiplos canais de notificação
"""

import json
import time
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .logger import get_logger
from .metrics import MetricsCollector

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Níveis de severidade dos alertas"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Canais de notificação disponíveis"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    DASHBOARD = "dashboard"


@dataclass
class AlertRule:
    """Regra de alerta configurável"""
    name: str
    metric: str
    threshold: float
    operator: str  # >, <, >=, <=, ==, !=
    severity: AlertSeverity
    channels: List[AlertChannel]
    cooldown_minutes: int = 5
    enabled: bool = True
    description: str = ""
    
    def __post_init__(self):
        if isinstance(self.severity, str):
            self.severity = AlertSeverity(self.severity)
        if isinstance(self.channels, list) and all(isinstance(c, str) for c in self.channels):
            self.channels = [AlertChannel(c) for c in self.channels]


@dataclass
class Alert:
    """Instância de alerta disparada"""
    id: str
    rule_name: str
    metric: str
    value: float
    threshold: float
    operator: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    status: str = "active"  # active, acknowledged, resolved
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if isinstance(self.severity, str):
            self.severity = AlertSeverity(self.severity)


class AlertManager:
    """Gerenciador central de alertas"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = MetricsCollector()
        
        # Configurações de canais
        self.email_config = config.get("email", {})
        self.slack_config = config.get("slack", {})
        self.webhook_config = config.get("webhook", {})
        
        # Estado dos alertas
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.rule_cooldowns: Dict[str, datetime] = {}
        
        # Carregar regras de alerta
        self.alert_rules = self._load_alert_rules()
        
        self.logger.info("Sistema de alertas inicializado com sucesso")
    
    def _load_alert_rules(self) -> List[AlertRule]:
        """Carrega regras de alerta da configuração"""
        default_rules = [
            AlertRule(
                name="High CPU Usage",
                metric="system.cpu_percent",
                threshold=80.0,
                operator=">",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.DASHBOARD, AlertChannel.EMAIL],
                cooldown_minutes=10,
                description="CPU usage above 80%"
            ),
            AlertRule(
                name="High Memory Usage",
                metric="system.memory_percent",
                threshold=85.0,
                operator=">",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.DASHBOARD, AlertChannel.EMAIL],
                cooldown_minutes=10,
                description="Memory usage above 85%"
            ),
            AlertRule(
                name="Data Pipeline Error",
                metric="pipeline.error_rate",
                threshold=5.0,
                operator=">",
                severity=AlertSeverity.ERROR,
                channels=[AlertChannel.DASHBOARD, AlertChannel.EMAIL, AlertChannel.SLACK],
                cooldown_minutes=5,
                description="Error rate above 5%"
            ),
            AlertRule(
                name="Cache Miss Rate",
                metric="cache.miss_rate",
                threshold=20.0,
                operator=">",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.DASHBOARD],
                cooldown_minutes=15,
                description="Cache miss rate above 20%"
            ),
            AlertRule(
                name="API Response Time",
                metric="api.response_time_p95",
                threshold=2000.0,
                operator=">",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.DASHBOARD, AlertChannel.EMAIL],
                cooldown_minutes=10,
                description="API response time P95 above 2 seconds"
            )
        ]
        
        # Carregar regras customizadas da configuração
        custom_rules = self.config.get("alert_rules", [])
        for rule_data in custom_rules:
            try:
                rule = AlertRule(**rule_data)
                default_rules.append(rule)
            except Exception as e:
                self.logger.error(f"Erro ao carregar regra de alerta: {e}")
        
        return default_rules
    
    def check_alerts(self) -> List[Alert]:
        """Verifica todas as regras de alerta e dispara alertas quando necessário"""
        triggered_alerts = []
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
                
            # Verificar cooldown
            if self._is_in_cooldown(rule):
                continue
            
            # Obter valor atual da métrica
            current_value = self._get_metric_value(rule.metric)
            if current_value is None:
                continue
            
            # Verificar se o threshold foi ultrapassado
            if self._evaluate_threshold(current_value, rule.threshold, rule.operator):
                # Disparar alerta
                alert = self._create_alert(rule, current_value)
                triggered_alerts.append(alert)
                
                # Enviar notificações
                self._send_notifications(alert, rule.channels)
                
                # Atualizar cooldown
                self.rule_cooldowns[rule.name] = datetime.now()
        
        return triggered_alerts
    
    def _is_in_cooldown(self, rule: AlertRule) -> bool:
        """Verifica se a regra está em cooldown"""
        if rule.name not in self.rule_cooldowns:
            return False
        
        last_triggered = self.rule_cooldowns[rule.name]
        cooldown_end = last_triggered + timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.now() < cooldown_end
    
    def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Obtém o valor atual de uma métrica"""
        try:
            # Mapear nomes de métricas para funções de coleta
            metric_mapping = {
                "system.cpu_percent": lambda: self.metrics.get_system_metrics()["cpu_percent"],
                "system.memory_percent": lambda: self.metrics.get_system_metrics()["memory_percent"],
                "pipeline.error_rate": lambda: self.metrics.get_pipeline_metrics()["error_rate"],
                "cache.miss_rate": lambda: self.metrics.get_cache_metrics()["miss_rate"],
                "api.response_time_p95": lambda: self.metrics.get_api_metrics()["response_time_p95"]
            }
            
            if metric_name in metric_mapping:
                return metric_mapping[metric_name]()
            else:
                # Tentar obter da coleta geral de métricas
                return self.metrics.get_metric(metric_name)
                
        except Exception as e:
            self.logger.error(f"Erro ao obter métrica {metric_name}: {e}")
            return None
    
    def _evaluate_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Avalia se o valor ultrapassou o threshold baseado no operador"""
        operators = {
            ">": lambda v, t: v > t,
            "<": lambda v, t: v < t,
            ">=": lambda v, t: v >= t,
            "<=": lambda v, t: v <= t,
            "==": lambda v, t: v == t,
            "!=": lambda v, t: v != t
        }
        
        if operator not in operators:
            self.logger.warning(f"Operador inválido: {operator}")
            return False
        
        return operators[operator](value, threshold)
    
    def _create_alert(self, rule: AlertRule, current_value: float) -> Alert:
        """Cria uma nova instância de alerta"""
        alert_id = f"{rule.name}_{int(time.time())}"
        
        # Criar mensagem do alerta
        message = f"{rule.description or rule.name}: {current_value} {rule.operator} {rule.threshold}"
        
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            metric=rule.metric,
            value=current_value,
            threshold=rule.threshold,
            operator=rule.operator,
            severity=rule.severity,
            message=message,
            timestamp=datetime.now()
        )
        
        # Adicionar à lista de alertas ativos
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        self.logger.info(f"Alerta disparado: {alert.message}")
        return alert
    
    def _send_notifications(self, alert: Alert, channels: List[AlertChannel]):
        """Envia notificações pelos canais especificados"""
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    self._send_email_alert(alert)
                elif channel == AlertChannel.SLACK:
                    self._send_slack_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook_alert(alert)
                elif channel == AlertChannel.SMS:
                    self._send_sms_alert(alert)
                # DASHBOARD é tratado automaticamente
                
            except Exception as e:
                self.logger.error(f"Erro ao enviar notificação via {channel.value}: {e}")
    
    def _send_email_alert(self, alert: Alert):
        """Envia alerta por email"""
        if not self.email_config:
            return
        
        try:
            # Configuração do servidor SMTP
            smtp_server = self.email_config.get("smtp_server")
            smtp_port = self.email_config.get("smtp_port", 587)
            username = self.email_config.get("username")
            password = self.email_config.get("password")
            from_email = self.email_config.get("from_email")
            to_emails = self.email_config.get("to_emails", [])
            
            if not all([smtp_server, username, password, from_email, to_emails]):
                self.logger.warning("Configuração de email incompleta")
                return
            
            # Criar mensagem
            subject = f"[{alert.severity.value.upper()}] {alert.rule_name}"
            body = f"""
            Alerta: {alert.rule_name}
            Severidade: {alert.severity.value}
            Métrica: {alert.metric}
            Valor Atual: {alert.value}
            Threshold: {alert.threshold} {alert.operator}
            Mensagem: {alert.message}
            Timestamp: {alert.timestamp}
            """
            
            # Enviar email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                
                for to_email in to_emails:
                    message = f"Subject: {subject}\n\n{body}"
                    server.sendmail(from_email, to_email, message)
            
            self.logger.info(f"Alerta enviado por email para {len(to_emails)} destinatários")
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {e}")
    
    def _send_slack_alert(self, alert: Alert):
        """Envia alerta para Slack"""
        if not self.slack_config:
            return
        
        try:
            webhook_url = self.slack_config.get("webhook_url")
            if not webhook_url:
                return
            
            # Criar payload do Slack
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff8c00",
                AlertSeverity.ERROR: "#ff0000",
                AlertSeverity.CRITICAL: "#8b0000"
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.severity, "#000000"),
                    "title": f"🚨 {alert.rule_name}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Severidade",
                            "value": alert.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Métrica",
                            "value": alert.metric,
                            "short": True
                        },
                        {
                            "title": "Valor Atual",
                            "value": str(alert.value),
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": f"{alert.operator} {alert.threshold}",
                            "short": True
                        }
                    ],
                    "footer": f"CloudDataOrchestrator • {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                }]
            }
            
            # Enviar para Slack
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Alerta enviado para Slack com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar para Slack: {e}")
    
    def _send_webhook_alert(self, alert: Alert):
        """Envia alerta para webhook customizado"""
        if not self.webhook_config:
            return
        
        try:
            webhook_url = self.webhook_config.get("url")
            if not webhook_url:
                return
            
            # Preparar payload
            payload = {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "severity": alert.severity.value,
                "metric": alert.metric,
                "value": alert.value,
                "threshold": alert.threshold,
                "operator": alert.operator,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "source": "CloudDataOrchestrator"
            }
            
            # Enviar webhook
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Alerta enviado para webhook com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar webhook: {e}")
    
    def _send_sms_alert(self, alert: Alert):
        """Envia alerta por SMS (implementação básica)"""
        # Implementar integração com serviço de SMS
        # Por exemplo: Twilio, AWS SNS, etc.
        self.logger.info(f"Alerta SMS seria enviado: {alert.message}")
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Marca um alerta como reconhecido"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].status = "acknowledged"
            self.active_alerts[alert_id].acknowledged_by = user
            self.logger.info(f"Alerta {alert_id} reconhecido por {user}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Marca um alerta como resolvido"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].status = "resolved"
            self.active_alerts[alert_id].resolved_at = datetime.now()
            # Mover para histórico
            resolved_alert = self.active_alerts.pop(alert_id)
            self.logger.info(f"Alerta {alert_id} resolvido")
            return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Retorna lista de alertas ativos"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Retorna histórico de alertas"""
        return self.alert_history[-limit:]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Retorna alertas por severidade"""
        return [alert for alert in self.active_alerts.values() if alert.severity == severity]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos alertas"""
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)
        
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len(self.get_alerts_by_severity(severity))
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": total_alerts - active_alerts,
            "severity_distribution": severity_counts,
            "last_alert": self.alert_history[-1].timestamp if self.alert_history else None
        }
    
    def cleanup_old_alerts(self, days: int = 30):
        """Remove alertas antigos do histórico"""
        cutoff_date = datetime.now() - timedelta(days=days)
        self.alert_history = [
            alert for alert in self.alert_history 
            if alert.timestamp > cutoff_date
        ]
        self.logger.info(f"Histórico de alertas limpo (mantidos últimos {days} dias)")


# Função de conveniência para criar instância padrão
def create_alert_manager(config: Dict[str, Any] = None) -> AlertManager:
    """Cria uma instância padrão do gerenciador de alertas"""
    if config is None:
        config = {
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your-email@gmail.com",
                "password": "your-app-password",
                "from_email": "your-email@gmail.com",
                "to_emails": ["admin@company.com"]
            },
            "slack": {
                "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
            },
            "webhook": {
                "url": "https://your-webhook-endpoint.com/alerts"
            }
        }
    
    return AlertManager(config)


if __name__ == "__main__":
    # Teste do sistema de alertas
    config = {
        "email": {},
        "slack": {},
        "webhook": {}
    }
    
    alert_manager = create_alert_manager(config)
    
    # Simular verificação de alertas
    print("Sistema de alertas inicializado!")
    print(f"Regras carregadas: {len(alert_manager.alert_rules)}")
    
    # Verificar alertas
    alerts = alert_manager.check_alerts()
    print(f"Alertas disparados: {len(alerts)}")
    
    # Estatísticas
    stats = alert_manager.get_alert_stats()
    print(f"Estatísticas: {stats}")
