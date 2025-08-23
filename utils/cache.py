#!/usr/bin/env python3
"""
Sistema de Cache para Cloud Data Orchestrator
Cache em memória com TTL e persistência
"""

import os
import json
import time
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from pathlib import Path
from collections import OrderedDict

class CacheItem:
    """Item individual do cache"""
    
    def __init__(self, key: str, value: Any, ttl: int = 3600):
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.ttl = ttl  # Time to live em segundos
    
    def is_expired(self) -> bool:
        """Verifica se o item expirou"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)
    
    def time_until_expiry(self) -> float:
        """Tempo restante até expiração em segundos"""
        expiry_time = self.created_at + timedelta(seconds=self.ttl)
        return (expiry_time - datetime.now()).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "ttl": self.ttl
        }

class MemoryCache:
    """Cache em memória com TTL"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheItem] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "expirations": 0
        }
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Define um valor no cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        # Remover item existente se houver
        if key in self.cache:
            del self.cache[key]
        
        # Verificar se cache está cheio
        if len(self.cache) >= self.max_size:
            # Remover item mais antigo
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        # Adicionar novo item
        self.cache[key] = CacheItem(key, value, ttl)
        self.cache.move_to_end(key)  # Mover para o final (mais recente)
        
        self.stats["sets"] += 1
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor do cache"""
        if key not in self.cache:
            self.stats["misses"] += 1
            return default
        
        item = self.cache[key]
        
        # Verificar se expirou
        if item.is_expired():
            del self.cache[key]
            self.stats["expirations"] += 1
            self.stats["misses"] += 1
            return default
        
        # Mover para o final (mais recente)
        self.cache.move_to_end(key)
        self.stats["hits"] += 1
        
        return item.value
    
    def delete(self, key: str) -> bool:
        """Remove um item do cache"""
        if key in self.cache:
            del self.cache[key]
            self.stats["deletes"] += 1
            return True
        return False
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        self.cache.clear()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "expirations": 0
        }
    
    def cleanup_expired(self) -> int:
        """Remove itens expirados"""
        expired_keys = [key for key, item in self.cache.items() if item.is_expired()]
        
        for key in expired_keys:
            del self.cache[key]
            self.stats["expirations"] += 1
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def keys(self) -> list:
        """Retorna todas as chaves válidas (não expiradas)"""
        self.cleanup_expired()
        return list(self.cache.keys())
    
    def exists(self, key: str) -> bool:
        """Verifica se uma chave existe e não expirou"""
        if key not in self.cache:
            return False
        
        if self.cache[key].is_expired():
            del self.cache[key]
            return False
        
        return True

class PersistentCache:
    """Cache com persistência em disco"""
    
    def __init__(self, cache_dir: str = "cache", max_size: int = 1000, default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.memory_cache = MemoryCache(max_size, default_ttl)
        self.persistent_file = self.cache_dir / "cache_data.pkl"
        
        # Carregar cache persistente
        self._load_persistent_cache()
    
    def _load_persistent_cache(self) -> None:
        """Carrega cache do disco"""
        try:
            if self.persistent_file.exists():
                with open(self.persistent_file, 'rb') as f:
                    persistent_data = pickle.load(f)
                
                # Restaurar itens válidos
                for key, item_data in persistent_data.items():
                    if isinstance(item_data, dict) and 'value' in item_data:
                        # Reconstruir CacheItem
                        item = CacheItem(
                            key=key,
                            value=item_data['value'],
                            ttl=item_data.get('ttl', self.memory_cache.default_ttl)
                        )
                        item.created_at = datetime.fromisoformat(item_data['created_at'])
                        
                        # Só adicionar se não expirou
                        if not item.is_expired():
                            self.memory_cache.cache[key] = item
                
                print(f"✅ Cache persistente carregado: {len(self.memory_cache.cache)} itens")
                
        except Exception as e:
            print(f"⚠️  Erro ao carregar cache persistente: {e}")
    
    def _save_persistent_cache(self) -> None:
        """Salva cache no disco"""
        try:
            # Converter para formato serializável
            persistent_data = {}
            for key, item in self.memory_cache.cache.items():
                if not item.is_expired():
                    persistent_data[key] = item.to_dict()
            
            # Salvar no disco
            with open(self.persistent_file, 'wb') as f:
                pickle.dump(persistent_data, f)
            
        except Exception as e:
            print(f"⚠️  Erro ao salvar cache persistente: {e}")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Define um valor no cache"""
        self.memory_cache.set(key, value, ttl)
        self._save_persistent_cache()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor do cache"""
        return self.memory_cache.get(key, default)
    
    def delete(self, key: str) -> bool:
        """Remove um item do cache"""
        result = self.memory_cache.delete(key)
        if result:
            self._save_persistent_cache()
        return result
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        self.memory_cache.clear()
        self._save_persistent_cache()
    
    def cleanup_expired(self) -> int:
        """Remove itens expirados"""
        count = self.memory_cache.cleanup_expired()
        if count > 0:
            self._save_persistent_cache()
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        return self.memory_cache.get_stats()
    
    def keys(self) -> list:
        """Retorna todas as chaves válidas"""
        return self.memory_cache.keys()
    
    def exists(self, key: str) -> bool:
        """Verifica se uma chave existe"""
        return self.memory_cache.exists(key)

class CacheDecorator:
    """Decorator para cache automático"""
    
    def __init__(self, cache: Union[MemoryCache, PersistentCache], ttl: int = 3600):
        self.cache = cache
        self.ttl = ttl
    
    def __call__(self, func):
        """Decorator principal"""
        def wrapper(*args, **kwargs):
            # Criar chave única baseada na função e argumentos
            cache_key = f"{func.__module__}.{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Tentar obter do cache
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executar função e armazenar resultado
            result = func(*args, **kwargs)
            self.cache.set(cache_key, result, self.ttl)
            
            return result
        
        return wrapper

class Cache:
    """Classe Cache simples para compatibilidade com sistema v2"""
    
    def __init__(self):
        self.memory_cache = MemoryCache()
        self.persistent_cache = PersistentCache()
    
    def get(self, key: str, default=None):
        """Obtém valor do cache"""
        # Tentar memória primeiro
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Tentar persistente
        return self.persistent_cache.get(key, default)
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Define valor no cache"""
        self.memory_cache.set(key, value, ttl)
        self.persistent_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """Remove valor do cache"""
        self.memory_cache.delete(key)
        self.persistent_cache.delete(key)
    
    def clear(self):
        """Limpa todo o cache"""
        self.memory_cache.clear()
        self.persistent_cache.clear()
    
    def get_stats(self):
        """Retorna estatísticas do cache"""
        return {
            "memory": self.memory_cache.get_stats(),
            "persistent": self.persistent_cache.get_stats()
        }

def main():
    """Função principal para teste"""
    print("🧪 Testando sistema de cache...")
    
    # Testar cache em memória
    print("\n📦 Testando Memory Cache:")
    memory_cache = MemoryCache(max_size=5, default_ttl=10)
    
    memory_cache.set("test1", "valor1", ttl=5)
    memory_cache.set("test2", "valor2", ttl=15)
    memory_cache.set("test3", "valor3", ttl=20)
    
    print(f"Cache size: {len(memory_cache.cache)}")
    print(f"test1: {memory_cache.get('test1')}")
    print(f"test2: {memory_cache.get('test2')}")
    
    # Aguardar expiração
    print("⏳ Aguardando 6 segundos para expiração...")
    import time
    time.sleep(6)
    
    print(f"test1 após 6s: {memory_cache.get('test1')}")
    print(f"test2 após 6s: {memory_cache.get('test2')}")
    
    # Limpar expirados
    expired_count = memory_cache.cleanup_expired()
    print(f"Expired items removed: {expired_count}")
    
    # Estatísticas
    stats = memory_cache.get_stats()
    print(f"Cache stats: {stats}")
    
    # Testar cache persistente
    print("\n💾 Testando Persistent Cache:")
    persistent_cache = PersistentCache(cache_dir="cache", max_size=10, default_ttl=30)
    
    persistent_cache.set("persistent1", {"data": "teste", "number": 42})
    persistent_cache.set("persistent2", [1, 2, 3, 4, 5])
    
    print(f"persistent1: {persistent_cache.get('persistent1')}")
    print(f"persistent2: {persistent_cache.get('persistent2')}")
    
    # Testar decorator
    print("\n🎯 Testando Cache Decorator:")
    
    @CacheDecorator(memory_cache, ttl=60)
    def expensive_function(x: int) -> int:
        print(f"Executando função cara com x={x}")
        time.sleep(1)  # Simular operação cara
        return x * x
    
    # Primeira execução (cara)
    result1 = expensive_function(5)
    print(f"Resultado 1: {result1}")
    
    # Segunda execução (do cache)
    result2 = expensive_function(5)
    print(f"Resultado 2: {result2}")
    
    print("\n✅ Testes de cache concluídos!")

if __name__ == "__main__":
    main()
