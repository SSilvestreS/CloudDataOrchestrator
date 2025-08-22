#!/usr/bin/env python3
"""
Sistema de Resiliência para Cloud Data Orchestrator
Implementa retry, circuit breaker e fallback patterns
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional, List
from functools import wraps
from enum import Enum

class CircuitState(Enum):
    """Estados do circuit breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Falhando, não tenta
    HALF_OPEN = "half_open"  # Testando se recuperou

class RetryStrategy:
    """Estratégias de retry"""
    
    @staticmethod
    def fixed_delay(delay: float = 1.0):
        """Delay fixo entre tentativas"""
        def strategy(attempt: int, max_attempts: int) -> float:
            return delay
        return strategy
    
    @staticmethod
    def exponential_backoff(base_delay: float = 1.0, max_delay: float = 60.0):
        """Backoff exponencial com jitter"""
        def strategy(attempt: int, max_attempts: int) -> float:
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            # Adicionar jitter para evitar thundering herd
            jitter = random.uniform(0, 0.1 * delay)
            return delay + jitter
        return strategy
    
    @staticmethod
    def linear_backoff(base_delay: float = 1.0, increment: float = 1.0):
        """Backoff linear"""
        def strategy(attempt: int, max_attempts: int) -> float:
            return base_delay + (increment * (attempt - 1))
        return strategy

class RetryHandler:
    """Manipulador de retry"""
    
    def __init__(self, 
                 max_attempts: int = 3,
                 strategy: Callable = None,
                 exceptions: tuple = (Exception,),
                 on_retry: Callable = None):
        
        self.max_attempts = max_attempts
        self.strategy = strategy or RetryStrategy.exponential_backoff()
        self.exceptions = exceptions
        self.on_retry = on_retry
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator para retry automático"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, self.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except self.exceptions as e:
                    last_exception = e
                    
                    if attempt == self.max_attempts:
                        # Última tentativa falhou
                        raise last_exception
                    
                    # Calcular delay para próxima tentativa
                    delay = self.strategy(attempt, self.max_attempts)
                    
                    # Callback de retry
                    if self.on_retry:
                        self.on_retry(attempt, delay, e, func.__name__)
                    
                    # Aguardar antes da próxima tentativa
                    time.sleep(delay)
            
            # Nunca deve chegar aqui
            raise last_exception
        
        return wrapper

class CircuitBreaker:
    """Implementação de circuit breaker"""
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: tuple = (Exception,),
                 name: str = "default"):
        
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executa função com circuit breaker"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Chamado quando função executa com sucesso"""
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Chamado quando função falha"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar reset"""
        if self.last_failure_time is None:
            return False
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do circuit breaker"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }
    
    def reset(self):
        """Reseta o circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

class FallbackHandler:
    """Manipulador de fallback"""
    
    def __init__(self, fallback_func: Callable = None, fallback_value: Any = None):
        self.fallback_func = fallback_func
        self.fallback_value = fallback_value
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator para fallback automático"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self.fallback_func:
                    return self.fallback_func(*args, **kwargs)
                elif self.fallback_value is not None:
                    return self.fallback_value
                else:
                    raise e
        
        return wrapper

class ResilienceManager:
    """Gerenciador de resiliência"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.fallback_handlers: Dict[str, FallbackHandler] = {}
    
    def create_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Cria um circuit breaker"""
        circuit_breaker = CircuitBreaker(name=name, **kwargs)
        self.circuit_breakers[name] = circuit_breaker
        return circuit_breaker
    
    def create_retry_handler(self, name: str, **kwargs) -> RetryHandler:
        """Cria um retry handler"""
        retry_handler = RetryHandler(**kwargs)
        self.retry_handlers[name] = retry_handler
        return retry_handler
    
    def create_fallback_handler(self, name: str, **kwargs) -> FallbackHandler:
        """Cria um fallback handler"""
        fallback_handler = FallbackHandler(**kwargs)
        self.fallback_handlers[name] = fallback_handler
        return fallback_handler
    
    def resilient_call(self, 
                      func: Callable,
                      circuit_breaker_name: str = None,
                      retry_handler_name: str = None,
                      fallback_handler_name: str = None,
                      *args, **kwargs) -> Any:
        """Executa função com todas as proteções de resiliência"""
        
        # Aplicar fallback se especificado
        if fallback_handler_name and fallback_handler_name in self.fallback_handlers:
            func = self.fallback_handlers[fallback_handler_name](func)
        
        # Aplicar retry se especificado
        if retry_handler_name and retry_handler_name in self.retry_handlers:
            func = self.retry_handlers[retry_handler_name](func)
        
        # Aplicar circuit breaker se especificado
        if circuit_breaker_name and circuit_breaker_name in self.circuit_breakers:
            return self.circuit_breakers[circuit_breaker_name].call(func, *args, **kwargs)
        
        # Executar função sem proteções
        return func(*args, **kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status de todos os componentes"""
        return {
            "circuit_breakers": {
                name: cb.get_status() for name, cb in self.circuit_breakers.items()
            },
            "retry_handlers": {
                name: {
                    "max_attempts": rh.max_attempts,
                    "exceptions": str(rh.exceptions)
                } for name, rh in self.retry_handlers.items()
            },
            "fallback_handlers": {
                name: {
                    "has_fallback_func": rh.fallback_func is not None,
                    "has_fallback_value": rh.fallback_value is not None
                } for name, rh in self.fallback_handlers.items()
            }
        }

def main():
    """Função principal para teste"""
    print("🧪 Testando sistema de resiliência...")
    
    # Criar gerenciador
    manager = ResilienceManager()
    
    # Simular função que pode falhar
    def unreliable_function(should_fail: bool = True) -> str:
        if should_fail:
            raise Exception("Falha simulada!")
        return "Sucesso!"
    
    # Função de fallback
    def fallback_function(*args, **kwargs) -> str:
        return "Fallback executado"
    
    # Configurar circuit breaker
    print("\n🔌 Testando Circuit Breaker:")
    cb = manager.create_circuit_breaker(
        name="test_cb",
        failure_threshold=3,
        recovery_timeout=5.0
    )
    
    # Simular falhas
    for i in range(5):
        try:
            cb.call(unreliable_function, should_fail=True)
        except Exception as e:
            print(f"Tentativa {i+1}: {e}")
            print(f"Estado: {cb.get_status()['state']}")
    
    # Testar retry
    print("\n🔄 Testando Retry Handler:")
    retry = manager.create_retry_handler(
        name="test_retry",
        max_attempts=3,
        strategy=RetryStrategy.exponential_backoff(base_delay=0.1),
        on_retry=lambda attempt, delay, error, func_name: 
            print(f"Retry {attempt}: aguardando {delay:.2f}s após {error}")
    )
    
    @retry
    def function_with_retry():
        if random.random() < 0.7:  # 70% chance de falhar
            raise Exception("Falha aleatória")
        return "Sucesso após retry!"
    
    try:
        result = function_with_retry()
        print(f"Resultado: {result}")
    except Exception as e:
        print(f"Falhou após todas as tentativas: {e}")
    
    # Testar fallback
    print("\n🛡️  Testando Fallback Handler:")
    fallback = manager.create_fallback_handler(
        name="test_fallback",
        fallback_func=fallback_function
    )
    
    @fallback
    def function_with_fallback():
        raise Exception("Falha para testar fallback")
    
    result = function_with_fallback()
    print(f"Resultado com fallback: {result}")
    
    # Status geral
    print("\n📊 Status do Sistema de Resiliência:")
    status = manager.get_status()
    for component, details in status.items():
        print(f"\n{component.upper()}:")
        for name, info in details.items():
            print(f"  {name}: {info}")
    
    print("\n✅ Testes de resiliência concluídos!")

if __name__ == "__main__":
    main()
