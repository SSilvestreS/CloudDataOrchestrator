#!/usr/bin/env python3
"""
Data Collector Melhorado para Cloud Data Orchestrator
"""

import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, Any, List

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ConfigManager
from utils.logger import LogManager, log_execution_time
from utils.metrics import MetricsCollector

class EnhancedDataCollector:
    """Data Collector com sistemas avançados integrados"""
    
    def __init__(self):
        # Inicializar sistemas
        self.config_manager = ConfigManager()
        self.log_manager = LogManager(
            name="data_collector",
            log_level="INFO",
            log_file="logs/data_collector.log"
        )
        self.logger = self.log_manager.get_logger()
        self.metrics_collector = MetricsCollector()
        
        # Carregar configurações
        self.aws_settings = self.config_manager.get_aws_settings()
        self.api_settings = self.config_manager.get_api_settings()
        
        # Configurar cidades
        self.cities = ["São Paulo", "Rio de Janeiro", "Brasília"]
        
        self.logger.info("Data Collector inicializado com sucesso")
    
    @log_execution_time
    def collect_weather_data(self) -> List[Dict[str, Any]]:
        """Coleta dados de clima com métricas"""
        self.logger.info("Iniciando coleta de dados de clima")
        self.metrics_collector.record_counter("weather_collection.started", 1)
        
        weather_data = []
        start_time = time.time()
        
        for city in self.cities:
            try:
                city_start_time = time.time()
                
                # Verificar API key
                if not self.api_settings.openweather_api_key or self.api_settings.openweather_api_key in ["test_key", "test_openweather_key"]:
                    self.logger.warning(f"API key inválida para {city}, usando dados simulados")
                    weather_item = self._generate_mock_weather_data(city)
                else:
                    weather_item = self._collect_real_weather_data(city)
                
                city_duration = time.time() - city_start_time
                self.metrics_collector.record_timer(f"weather_collection.city.{city}", city_duration)
                
                weather_data.append(weather_item)
                self.logger.info(f"Dados coletados para {city}")
                
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Erro ao coletar dados para {city}: {str(e)}")
                self.metrics_collector.record_counter("weather_collection.errors", 1)
        
        total_duration = time.time() - start_time
        self.metrics_collector.record_timer("weather_collection.total_duration", total_duration)
        self.metrics_collector.record_counter("weather_collection.completed", 1)
        
        self.logger.info(f"Coleta de clima concluída: {len(weather_data)} cidades")
        return weather_data
    
    def _collect_real_weather_data(self, city: str) -> Dict[str, Any]:
        """Coleta dados reais da API"""
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": self.api_settings.openweather_api_key,
            "units": "metric",
            "lang": "pt_br"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "timestamp": datetime.now().isoformat(),
            "source": "openweather_api"
        }
    
    def _generate_mock_weather_data(self, city: str) -> Dict[str, Any]:
        """Gera dados simulados para teste"""
        return {
            "city": city,
            "temperature": 20.0 + (hash(city) % 15),
            "humidity": 60 + (hash(city) % 30),
            "description": "céu limpo",
            "timestamp": datetime.now().isoformat(),
            "source": "mock_data"
        }
    
    def run_collection(self) -> Dict[str, Any]:
        """Executa coleta completa"""
        self.logger.info("🚀 Iniciando coleta completa de dados")
        
        collection_start = time.time()
        results = {}
        
        # Coletar dados de clima
        try:
            weather_data = self.collect_weather_data()
            results["weather"] = {
                "count": len(weather_data),
                "data": weather_data
            }
        except Exception as e:
            self.logger.error(f"Erro na coleta de clima: {e}")
            results["weather"] = {"error": str(e)}
        
        # Calcular métricas finais
        total_duration = time.time() - collection_start
        total_records = results.get("weather", {}).get("count", 0)
        
        self.metrics_collector.record_timer("full_collection.total_duration", total_duration)
        self.metrics_collector.record_counter("full_collection.total_records", total_records)
        
        self.logger.info(f"🎉 Coleta completa concluída em {total_duration:.2f}s")
        return results

def main():
    """Função principal para teste"""
    try:
        collector = EnhancedDataCollector()
        results = collector.run_collection()
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DA COLETA")
        print("=" * 60)
        
        for data_type, data_info in results.items():
            if "error" in data_info:
                print(f"❌ {data_type.upper()}: Erro - {data_info['error']}")
            else:
                print(f"✅ {data_type.upper()}: {data_info['count']} registros")
        
    except Exception as e:
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    main()
