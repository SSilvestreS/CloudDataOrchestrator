#!/usr/bin/env python3
"""
Sistema de Logging Avançado para Cloud Data Orchestrator
Sistema de logging estruturado com diferentes níveis e formatos
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from functools import wraps

class StructuredFormatter(logging.Formatter):
    """Formatador estruturado para logs"""
    
    def __init__(self, include_timestamp: bool = True, include_level: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o registro de log"""
        log_data = {
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if self.include_timestamp:
            log_data["timestamp"] = datetime.fromtimestamp(record.created).isoformat()
        
        if self.include_level:
            log_data["level"] = record.levelname
        
        # Adicionar campos extras se existirem
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Adicionar exceção se existir
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class ColoredFormatter(logging.Formatter):
    """Formatador colorido para console"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o registro com cores"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Formato: [LEVEL] Message (Module:Function:Line)
        formatted = f"{color}[{record.levelname}]{reset} {record.getMessage()}"
        
        if record.module and record.funcName:
            formatted += f" ({record.module}:{record.funcName}:{record.lineno})"
        
        return formatted

class LogManager:
    """Gerenciador de logging do projeto"""
    
    def __init__(self, 
                 name: str = "cloud_data_orchestrator",
                 log_level: str = "INFO",
                 log_file: Optional[str] = None,
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Configurar logger principal
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        
        # Evitar duplicação de handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Configura os handlers de logging"""
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_formatter = ColoredFormatter()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Handler para arquivo (se especificado)
        if self.log_file:
            self._setup_file_handler()
        
        # Handler para arquivo estruturado (JSON)
        self._setup_structured_handler()
    
    def _setup_file_handler(self) -> None:
        """Configura handler para arquivo de texto"""
        try:
            # Criar diretório se não existir
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handler com rotação
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            
            # Formato para arquivo
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.info(f"Logging para arquivo configurado: {self.log_file}")
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar logging para arquivo: {e}")
    
    def _setup_structured_handler(self) -> None:
        """Configura handler para logs estruturados (JSON)"""
        try:
            # Arquivo para logs estruturados
            structured_log_file = self.log_file.replace('.log', '_structured.json') if self.log_file else 'logs/structured.json'
            
            # Criar diretório se não existir
            log_path = Path(structured_log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handler com rotação
            structured_handler = logging.handlers.RotatingFileHandler(
                structured_log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            structured_handler.setLevel(self.log_level)
            
            # Formato estruturado
            structured_formatter = StructuredFormatter()
            structured_handler.setFormatter(structured_formatter)
            
            self.logger.addHandler(structured_handler)
            self.logger.info(f"Logging estruturado configurado: {structured_log_file}")
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar logging estruturado: {e}")
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Retorna um logger configurado"""
        if name:
            return logging.getLogger(f"{self.name}.{name}")
        return self.logger
    
    def set_level(self, level: str) -> None:
        """Define o nível de logging"""
        log_level = getattr(logging, level.upper())
        self.logger.setLevel(log_level)
        
        # Atualizar nível de todos os handlers
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
        
        self.logger.info(f"Nível de logging alterado para: {level}")
    
    def add_context(self, **kwargs) -> None:
        """Adiciona contexto aos logs"""
        for key, value in kwargs.items():
            setattr(self.logger, key, value)
    
    def log_with_context(self, level: str, message: str, **context) -> None:
        """Log com contexto adicional"""
        extra_fields = {"extra_fields": context}
        self.logger.log(getattr(logging, level.upper()), message, extra=extra_fields)

def log_function_call(func):
    """Decorator para logar chamadas de função"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = LogManager().get_logger(func.__module__)
        
        # Log da entrada
        logger.debug(f"Chamando {func.__name__} com args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} retornou: {result}")
            return result
        except Exception as e:
            logger.error(f"Erro em {func.__name__}: {e}", exc_info=True)
            raise
    
    return wrapper

def log_execution_time(func):
    """Decorator para logar tempo de execução"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = LogManager().get_logger(func.__module__)
        start_time = datetime.now()
        
        logger.debug(f"Iniciando execução de {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"{func.__name__} executado em {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} falhou após {execution_time:.2f}s: {e}")
            raise
    
    return wrapper

class PerformanceLogger:
    """Logger para métricas de performance"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = LogManager().get_logger(logger_name)
        self.metrics = {}
    
    def start_timer(self, operation: str) -> None:
        """Inicia timer para uma operação"""
        self.metrics[operation] = {"start": datetime.now()}
        self.logger.debug(f"Timer iniciado para: {operation}")
    
    def end_timer(self, operation: str, success: bool = True) -> None:
        """Finaliza timer para uma operação"""
        if operation in self.metrics:
            start_time = self.metrics[operation]["start"]
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.metrics[operation]["end"] = datetime.now()
            self.metrics[operation]["duration"] = execution_time
            self.metrics[operation]["success"] = success
            
            if success:
                self.logger.info(f"Operação {operation} concluída em {execution_time:.3f}s")
            else:
                self.logger.warning(f"Operação {operation} falhou após {execution_time:.3f}s")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas coletadas"""
        return self.metrics
    
    def log_metrics_summary(self) -> None:
        """Loga resumo das métricas"""
        if not self.metrics:
            self.logger.info("Nenhuma métrica coletada")
            return
        
        total_operations = len(self.metrics)
        successful_operations = sum(1 for m in self.metrics.values() if m.get("success", False))
        total_time = sum(m.get("duration", 0) for m in self.metrics.values())
        avg_time = total_time / total_operations if total_operations > 0 else 0
        
        self.logger.info(f"Resumo de Performance:")
        self.logger.info(f"  Total de operações: {total_operations}")
        self.logger.info(f"  Operações bem-sucedidas: {successful_operations}")
        self.logger.info(f"  Taxa de sucesso: {(successful_operations/total_operations)*100:.1f}%")
        self.logger.info(f"  Tempo total: {total_time:.3f}s")
        self.logger.info(f"  Tempo médio: {avg_time:.3f}s")

def main():
    """Função principal para teste"""
    # Configurar logging
    log_manager = LogManager(
        name="test_logger",
        log_level="DEBUG",
        log_file="logs/test.log"
    )
    
    logger = log_manager.get_logger()
    
    # Testar diferentes níveis
    logger.debug("Mensagem de debug")
    logger.info("Mensagem de informação")
    logger.warning("Mensagem de aviso")
    logger.error("Mensagem de erro")
    
    # Testar logging com contexto
    log_manager.log_with_context("INFO", "Operação iniciada", user_id="123", operation="data_collection")
    
    # Testar performance logger
    perf_logger = PerformanceLogger()
    perf_logger.start_timer("test_operation")
    
    import time
    time.sleep(1)  # Simular operação
    
    perf_logger.end_timer("test_operation", success=True)
    perf_logger.log_metrics_summary()

if __name__ == "__main__":
    main()

# Função global para compatibilidade
def get_logger(name: str = None) -> logging.Logger:
    """Função global para obter um logger configurado"""
    log_manager = LogManager()
    return log_manager.get_logger(name)

# Instância global para uso direto
default_logger = LogManager().get_logger()
