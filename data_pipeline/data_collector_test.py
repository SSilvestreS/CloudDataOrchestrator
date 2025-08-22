import os
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollectorTest:
    """Classe para coleta de dados de APIs públicas (modo teste)"""

    def __init__(self):
        self.openweather_api_key = os.environ.get("OPENWEATHER_API_KEY", "test_key")
        self.cities = ["São Paulo", "Rio de Janeiro", "Brasília"]
        self.test_mode = self.openweather_api_key in [
            "test_key",
            "test_openweather_key",
        ]

    def collect_weather_data(self) -> List[Dict[str, Any]]:
        """Coleta dados de clima"""
        weather_data = []

        if self.test_mode:
            logger.info("Modo teste: simulando dados de clima")
            # Dados simulados para teste
            for city in self.cities:
                weather_item = {
                    "city": city,
                    "temperature": 25.0 + (hash(city) % 10),
                    "humidity": 60 + (hash(city) % 20),
                    "description": "céu limpo",
                    "timestamp": datetime.now().isoformat(),
                }
                weather_data.append(weather_item)
                logger.info(f"Dados simulados de clima para {city}")
            return weather_data

        # Coleta real da API (se API key válida)
        for city in self.cities:
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather"
                params = {
                    "q": city,
                    "appid": self.openweather_api_key,
                    "units": "metric",
                    "lang": "pt_br",
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                weather_item = {
                    "city": city,
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "timestamp": datetime.now().isoformat(),
                }

                weather_data.append(weather_item)
                logger.info(f"Dados de clima coletados para {city}")
                time.sleep(1)

            except Exception as e:
                logger.error(f"Erro ao coletar dados de clima para {city}: {str(e)}")

        return weather_data

    def collect_currency_data(self) -> List[Dict[str, Any]]:
        """Coleta dados de câmbio"""
        try:
            if self.test_mode:
                logger.info("Modo teste: simulando dados de câmbio")
                # Dados simulados para teste
                currencies = ["EUR", "GBP", "JPY", "BRL"]
                currency_data = []

                for currency in currencies:
                    currency_item = {
                        "base_currency": "USD",
                        "target_currency": currency,
                        "rate": 0.8 + (hash(currency) % 100) / 100,
                        "timestamp": datetime.now().isoformat(),
                    }
                    currency_data.append(currency_item)

                logger.info("Dados simulados de câmbio coletados")
                return currency_data

            # Coleta real da API
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            rates = data["rates"]

            currency_data = []
            currencies = ["EUR", "GBP", "JPY", "BRL"]

            for currency in currencies:
                if currency in rates:
                    currency_item = {
                        "base_currency": "USD",
                        "target_currency": currency,
                        "rate": rates[currency],
                        "timestamp": datetime.now().isoformat(),
                    }
                    currency_data.append(currency_item)

            logger.info(f"Dados de câmbio coletados")
            return currency_data

        except Exception as e:
            logger.error(f"Erro ao coletar dados de câmbio: {str(e)}")
            return []

    def save_to_mock_storage(self, data: List[Dict[str, Any]], data_type: str) -> None:
        """Salva dados em armazenamento simulado"""
        try:
            # Simular salvamento
            logger.info(
                f"Simulando salvamento de {len(data)} itens para tipo {data_type}"
            )

            # Salvar em arquivo JSON para verificação
            output_file = f"test_output_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Dados salvos em {output_file}")

        except Exception as e:
            logger.error(f"Erro ao salvar dados: {str(e)}")

    def run_collection(self) -> None:
        """Executa a coleta completa"""
        logger.info("Iniciando coleta de dados (modo teste)...")

        weather_data = self.collect_weather_data()
        if weather_data:
            self.save_to_mock_storage(weather_data, "weather")

        currency_data = self.collect_currency_data()
        if currency_data:
            self.save_to_mock_storage(currency_data, "currency")

        logger.info("Coleta de dados concluída")


def main():
    collector = DataCollectorTest()
    collector.run_collection()


if __name__ == "__main__":
    main()
