"""
Sistema de Integração com Múltiplos Provedores de Dados para CloudDataOrchestrator
Implementa integração com APIs financeiras, climáticas, redes sociais e outros provedores
"""

import requests
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
from abc import ABC, abstractmethod

from utils.logger import get_logger
from utils.cache import Cache
from utils.resilience import CircuitBreaker, RetryHandler

logger = get_logger(__name__)


class DataProviderType(Enum):
    """Tipos de provedores de dados disponíveis"""
    FINANCIAL = "financial"
    WEATHER = "weather"
    SOCIAL_MEDIA = "social_media"
    NEWS = "news"
    CRYPTO = "crypto"
    STOCK_MARKET = "stock_market"
    ECONOMIC_INDICATORS = "economic_indicators"
    TRANSPORT = "transport"
    HEALTH = "health"
    TECHNOLOGY = "technology"


@dataclass
class DataProviderConfig:
    """Configuração para um provedor de dados"""
    name: str
    type: DataProviderType
    base_url: str
    api_key: str
    rate_limit: int = 100  # requests per minute
    timeout: int = 30
    retry_attempts: int = 3
    cache_ttl: int = 300  # seconds
    enabled: bool = True
    headers: Dict[str, str] = None
    params: Dict[str, str] = None
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = DataProviderType(self.type)
        if self.headers is None:
            self.headers = {}
        if self.params is None:
            self.params = {}


@dataclass
class DataRequest:
    """Requisição de dados para um provedor"""
    provider: str
    endpoint: str
    params: Dict[str, Any]
    timestamp: datetime
    request_id: str = None
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = hashlib.md5(
                f"{self.provider}{self.endpoint}{json.dumps(self.params, sort_keys=True)}".encode()
            ).hexdigest()


@dataclass
class DataResponse:
    """Resposta de dados de um provedor"""
    request_id: str
    provider: str
    data: Any
    timestamp: datetime
    status: str = "success"
    error_message: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseDataProvider(ABC):
    """Classe base abstrata para provedores de dados"""
    
    def __init__(self, config: DataProviderConfig):
        self.config = config
        self.logger = get_logger(f"provider.{config.name}")
        self.cache = Cache()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=requests.RequestException
        )
        self.retry_handler = RetryHandler(
            max_attempts=config.retry_attempts,
            base_delay=1,
            max_delay=30
        )
        
        # Rate limiting
        self.request_times: List[datetime] = []
        
        self.logger.info(f"Provedor {config.name} inicializado")
    
    @abstractmethod
    async def fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> DataResponse:
        """Método abstrato para buscar dados"""
        pass
    
    def _check_rate_limit(self) -> bool:
        """Verifica se a requisição está dentro do limite de taxa"""
        now = datetime.now()
        # Remover requisições antigas (mais de 1 minuto)
        self.request_times = [t for t in self.request_times if now - t < timedelta(minutes=1)]
        
        if len(self.request_times) >= self.config.rate_limit:
            return False
        
        self.request_times.append(now)
        return True
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """Gera chave de cache para a requisição"""
        param_str = json.dumps(params or {}, sort_keys=True)
        return f"{self.config.name}:{endpoint}:{hashlib.md5(param_str.encode()).hexdigest()}"
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers para a requisição"""
        headers = {
            "User-Agent": "CloudDataOrchestrator/2.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        headers.update(self.config.headers)
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        return headers
    
    def _get_params(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Retorna parâmetros para a requisição"""
        request_params = self.config.params.copy() if self.config.params else {}
        if params:
            request_params.update(params)
        return request_params


class FinancialDataProvider(BaseDataProvider):
    """Provedor de dados financeiros"""
    
    async def fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> DataResponse:
        """Busca dados financeiros"""
        try:
            # Verificar cache
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return DataResponse(
                    request_id=cache_key,
                    provider=self.config.name,
                    data=cached_data,
                    timestamp=datetime.now(),
                    metadata={"source": "cache"}
                )
            
            # Verificar rate limit
            if not self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            # Fazer requisição
            url = f"{self.config.base_url}/{endpoint}"
            headers = self._get_headers()
            request_params = self._get_params(params)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers, 
                    params=request_params,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Salvar no cache
                        self.cache.set(cache_key, data, ttl=self.config.cache_ttl)
                        
                        return DataResponse(
                            request_id=cache_key,
                            provider=self.config.name,
                            data=data,
                            timestamp=datetime.now(),
                            metadata={
                                "status_code": response.status,
                                "source": "api"
                            }
                        )
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados financeiros: {e}")
            return DataResponse(
                request_id=hashlib.md5(f"{endpoint}{params}".encode()).hexdigest(),
                provider=self.config.name,
                data=None,
                timestamp=datetime.now(),
                status="error",
                error_message=str(e)
            )


class WeatherDataProvider(BaseDataProvider):
    """Provedor de dados climáticos"""
    
    async def fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> DataResponse:
        """Busca dados climáticos"""
        try:
            # Verificar cache
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return DataResponse(
                    request_id=cache_key,
                    provider=self.config.name,
                    data=cached_data,
                    timestamp=datetime.now(),
                    metadata={"source": "cache"}
                )
            
            # Verificar rate limit
            if not self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            # Fazer requisição
            url = f"{self.config.base_url}/{endpoint}"
            headers = self._get_headers()
            request_params = self._get_params(params)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers, 
                    params=request_params,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Salvar no cache
                        self.cache.set(cache_key, data, ttl=self.config.cache_ttl)
                        
                        return DataResponse(
                            request_id=cache_key,
                            provider=self.config.name,
                            data=data,
                            timestamp=datetime.now(),
                            metadata={
                                "status_code": response.status,
                                "source": "api"
                            }
                        )
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados climáticos: {e}")
            return DataResponse(
                request_id=hashlib.md5(f"{endpoint}{params}".encode()).hexdigest(),
                provider=self.config.name,
                data=None,
                timestamp=datetime.now(),
                status="error",
                error_message=str(e)
            )


class SocialMediaDataProvider(BaseDataProvider):
    """Provedor de dados de redes sociais"""
    
    async def fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> DataResponse:
        """Busca dados de redes sociais"""
        try:
            # Verificar cache
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return DataResponse(
                    request_id=cache_key,
                    provider=self.config.name,
                    data=cached_data,
                    timestamp=datetime.now(),
                    metadata={"source": "cache"}
                )
            
            # Verificar rate limit
            if not self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            # Fazer requisição
            url = f"{self.config.base_url}/{endpoint}"
            headers = self._get_headers()
            request_params = self._get_params(params)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers, 
                    params=request_params,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Salvar no cache
                        self.cache.set(cache_key, data, ttl=self.config.cache_ttl)
                        
                        return DataResponse(
                            request_id=cache_key,
                            provider=self.config.name,
                            data=data,
                            timestamp=datetime.now(),
                            metadata={
                                "status_code": response.status,
                                "source": "api"
                            }
                        )
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados de redes sociais: {e}")
            return DataResponse(
                request_id=hashlib.md5(f"{endpoint}{params}".encode()).hexdigest(),
                provider=self.config.name,
                data=None,
                timestamp=datetime.now(),
                status="error",
                error_message=str(e)
            )


class NewsDataProvider(BaseDataProvider):
    """Provedor de dados de notícias"""
    
    async def fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> DataResponse:
        """Busca dados de notícias"""
        try:
            # Verificar cache
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return DataResponse(
                    request_id=cache_key,
                    provider=self.config.name,
                    data=cached_data,
                    timestamp=datetime.now(),
                    metadata={"source": "cache"}
                )
            
            # Verificar rate limit
            if not self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            # Fazer requisição
            url = f"{self.config.base_url}/{endpoint}"
            headers = self._get_headers()
            request_params = self._get_params(params)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers, 
                    params=request_params,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Salvar no cache
                        self.cache.set(cache_key, data, ttl=self.config.cache_ttl)
                        
                        return DataResponse(
                            request_id=cache_key,
                            provider=self.config.name,
                            data=data,
                            timestamp=datetime.now(),
                            metadata={
                                "status_code": response.status,
                                "source": "api"
                            }
                        )
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados de notícias: {e}")
            return DataResponse(
                request_id=hashlib.md5(f"{endpoint}{params}".encode()).hexdigest(),
                provider=self.config.name,
                data=None,
                timestamp=datetime.now(),
                status="error",
                error_message=str(e)
            )


class CryptoDataProvider(BaseDataProvider):
    """Provedor de dados de criptomoedas"""
    
    async def fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> DataResponse:
        """Busca dados de criptomoedas"""
        try:
            # Verificar cache
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return DataResponse(
                    request_id=cache_key,
                    provider=self.config.name,
                    data=cached_data,
                    timestamp=datetime.now(),
                    metadata={"source": "cache"}
                )
            
            # Verificar rate limit
            if not self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            # Fazer requisição
            url = f"{self.config.base_url}/{endpoint}"
            headers = self._get_headers()
            request_params = self._get_params(params)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers, 
                    params=request_params,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Salvar no cache
                        self.cache.set(cache_key, data, ttl=self.config.cache_ttl)
                        
                        return DataResponse(
                            request_id=cache_key,
                            provider=self.config.name,
                            data=data,
                            timestamp=datetime.now(),
                            metadata={
                                "status_code": response.status,
                                "source": "api"
                            }
                        )
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados de criptomoedas: {e}")
            return DataResponse(
                request_id=hashlib.md5(f"{endpoint}{params}".encode()).hexdigest(),
                provider=self.config.name,
                data=None,
                timestamp=datetime.now(),
                status="error",
                error_message=str(e)
            )


class DataProviderManager:
    """Gerenciador central de provedores de dados"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # Provedores registrados
        self.providers: Dict[str, BaseDataProvider] = {}
        
        # Histórico de requisições
        self.request_history: List[DataRequest] = []
        self.response_history: List[DataResponse] = []
        
        # Carregar configurações e inicializar provedores
        self._load_providers()
        
        self.logger.info("Gerenciador de provedores de dados inicializado")
    
    def _load_providers(self):
        """Carrega e inicializa provedores de dados"""
        # Configurações padrão para provedores populares
        default_providers = {
            "alpha_vantage": {
                "name": "Alpha Vantage",
                "type": "financial",
                "base_url": "https://www.alphavantage.co/query",
                "api_key": self.config.get("alpha_vantage_api_key", ""),
                "rate_limit": 5,  # Free tier limit
                "cache_ttl": 600
            },
            "openweather": {
                "name": "OpenWeather",
                "type": "weather",
                "base_url": "https://api.openweathermap.org/data/2.5",
                "api_key": self.config.get("openweather_api_key", ""),
                "rate_limit": 60,
                "cache_ttl": 1800
            },
            "newsapi": {
                "name": "NewsAPI",
                "type": "news",
                "base_url": "https://newsapi.org/v2",
                "api_key": self.config.get("newsapi_api_key", ""),
                "rate_limit": 100,
                "cache_ttl": 3600
            },
            "coinapi": {
                "name": "CoinAPI",
                "type": "crypto",
                "base_url": "https://rest.coinapi.io/v1",
                "api_key": self.config.get("coinapi_api_key", ""),
                "rate_limit": 100,
                "cache_ttl": 60
            },
            "twitter": {
                "name": "Twitter API",
                "type": "social_media",
                "base_url": "https://api.twitter.com/2",
                "api_key": self.config.get("twitter_bearer_token", ""),
                "rate_limit": 300,
                "cache_ttl": 300
            }
        }
        
        # Carregar configurações customizadas
        custom_providers = self.config.get("data_providers", {})
        default_providers.update(custom_providers)
        
        # Inicializar provedores
        for provider_id, provider_config in default_providers.items():
            if provider_config.get("enabled", True) and provider_config.get("api_key"):
                try:
                    config = DataProviderConfig(**provider_config)
                    provider = self._create_provider(config)
                    if provider:
                        self.providers[provider_id] = provider
                        self.logger.info(f"Provedor {provider_id} inicializado")
                except Exception as e:
                    self.logger.error(f"Erro ao inicializar provedor {provider_id}: {e}")
    
    def _create_provider(self, config: DataProviderConfig) -> Optional[BaseDataProvider]:
        """Cria uma instância do provedor baseado no tipo"""
        try:
            if config.type == DataProviderType.FINANCIAL:
                return FinancialDataProvider(config)
            elif config.type == DataProviderType.WEATHER:
                return WeatherDataProvider(config)
            elif config.type == DataProviderType.SOCIAL_MEDIA:
                return SocialMediaDataProvider(config)
            elif config.type == DataProviderType.NEWS:
                return NewsDataProvider(config)
            elif config.type == DataProviderType.CRYPTO:
                return CryptoDataProvider(config)
            else:
                # Fallback para provedor genérico
                return BaseDataProvider(config)
        except Exception as e:
            self.logger.error(f"Erro ao criar provedor {config.name}: {e}")
            return None
    
    async def fetch_data(self, provider_id: str, endpoint: str, params: Dict[str, Any] = None) -> DataResponse:
        """Busca dados de um provedor específico"""
        if provider_id not in self.providers:
            return DataResponse(
                request_id="",
                provider=provider_id,
                data=None,
                timestamp=datetime.now(),
                status="error",
                error_message=f"Provedor {provider_id} não encontrado"
            )
        
        provider = self.providers[provider_id]
        
        # Criar requisição
        request = DataRequest(
            provider=provider_id,
            endpoint=endpoint,
            params=params or {},
            timestamp=datetime.now()
        )
        self.request_history.append(request)
        
        # Buscar dados
        response = await provider.fetch_data(endpoint, params)
        response.request_id = request.request_id
        self.response_history.append(response)
        
        return response
    
    async def fetch_multiple_providers(self, requests: List[Dict[str, Any]]) -> List[DataResponse]:
        """Busca dados de múltiplos provedores em paralelo"""
        tasks = []
        for req in requests:
            provider_id = req.get("provider")
            endpoint = req.get("endpoint")
            params = req.get("params")
            
            if provider_id and endpoint:
                task = self.fetch_data(provider_id, endpoint, params)
                tasks.append(task)
        
        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            # Filtrar exceções
            valid_responses = []
            for response in responses:
                if isinstance(response, DataResponse):
                    valid_responses.append(response)
                else:
                    self.logger.error(f"Erro em requisição paralela: {response}")
            
            return valid_responses
        
        return []
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Retorna status de todos os provedores"""
        status = {}
        for provider_id, provider in self.providers.items():
            status[provider_id] = {
                "enabled": provider.config.enabled,
                "type": provider.config.type.value,
                "rate_limit": provider.config.rate_limit,
                "cache_ttl": provider.config.cache_ttl,
                "circuit_breaker_state": provider.circuit_breaker.state.value,
                "requests_in_window": len(provider.request_times)
            }
        return status
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das requisições"""
        total_requests = len(self.request_history)
        successful_requests = len([r for r in self.response_history if r.status == "success"])
        failed_requests = total_requests - successful_requests
        
        # Estatísticas por provedor
        provider_stats = {}
        for response in self.response_history:
            provider = response.provider
            if provider not in provider_stats:
                provider_stats[provider] = {"total": 0, "success": 0, "failed": 0}
            
            provider_stats[provider]["total"] += 1
            if response.status == "success":
                provider_stats[provider]["success"] += 1
            else:
                provider_stats[provider]["failed"] += 1
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "provider_stats": provider_stats,
            "last_request": self.request_history[-1].timestamp if self.request_history else None
        }
    
    def cleanup_old_data(self, days: int = 7):
        """Remove dados antigos do histórico"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        self.request_history = [
            req for req in self.request_history 
            if req.timestamp > cutoff_date
        ]
        
        self.response_history = [
            resp for resp in self.response_history 
            if resp.timestamp > cutoff_date
        ]
        
        self.logger.info(f"Histórico limpo (mantidos últimos {days} dias)")


# Função de conveniência para criar instância padrão
def create_data_provider_manager(config: Dict[str, Any] = None) -> DataProviderManager:
    """Cria uma instância padrão do gerenciador de provedores"""
    if config is None:
        config = {
            "alpha_vantage_api_key": "your-api-key",
            "openweather_api_key": "your-api-key",
            "newsapi_api_key": "your-api-key",
            "coinapi_api_key": "your-api-key",
            "twitter_bearer_token": "your-bearer-token"
        }
    
    return DataProviderManager(config)


if __name__ == "__main__":
    # Teste do sistema de provedores de dados
    async def test_providers():
        config = {
            "alpha_vantage_api_key": "demo",
            "openweather_api_key": "demo"
        }
        
        manager = create_data_provider_manager(config)
        
        print("Gerenciador de provedores inicializado!")
        print(f"Provedores disponíveis: {list(manager.providers.keys())}")
        
        # Testar busca de dados
        if "alpha_vantage" in manager.providers:
            response = await manager.fetch_data(
                "alpha_vantage", 
                "TIME_SERIES_DAILY", 
                {"symbol": "AAPL"}
            )
            print(f"Resposta Alpha Vantage: {response.status}")
        
        # Status dos provedores
        status = manager.get_provider_status()
        print(f"Status dos provedores: {status}")
        
        # Estatísticas
        stats = manager.get_request_stats()
        print(f"Estatísticas: {stats}")
    
    # Executar teste
    asyncio.run(test_providers())
