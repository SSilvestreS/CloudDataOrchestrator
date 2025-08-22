import os
import json
import time
import logging
import requests
import boto3
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """Classe para coleta de dados de APIs públicas"""

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = os.environ.get("DYNAMODB_TABLE", "data-pipeline-table")
        self.table = self.dynamodb.Table(self.table_name)

        self.openweather_api_key = os.environ.get("OPENWEATHER_API_KEY")
        self.cities = ["São Paulo", "Rio de Janeiro", "Brasília"]

    def collect_weather_data(self) -> List[Dict[str, Any]]:
        """Coleta dados de clima"""
        weather_data = []

        if not self.openweather_api_key:
            logger.warning("API key do OpenWeather não configurada")
            return weather_data

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

    def save_to_dynamodb(self, data: List[Dict[str, Any]], data_type: str) -> None:
        """Salva dados no DynamoDB"""
        try:
            for item in data:
                item_id = f"{data_type}_{datetime.now().isoformat()}_{hash(str(item))}"

                dynamo_item = {
                    "id": item_id,
                    "type": data_type,
                    "data": item,
                    "timestamp": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                }

                self.table.put_item(Item=dynamo_item)

            logger.info(f"{len(data)} itens salvos no DynamoDB para tipo {data_type}")

        except Exception as e:
            logger.error(f"Erro ao salvar dados no DynamoDB: {str(e)}")

    def run_collection(self) -> None:
        """Executa a coleta completa"""
        logger.info("Iniciando coleta de dados...")

        weather_data = self.collect_weather_data()
        if weather_data:
            self.save_to_dynamodb(weather_data, "weather")

        currency_data = self.collect_currency_data()
        if currency_data:
            self.save_to_dynamodb(currency_data, "currency")

        logger.info("Coleta de dados concluída")


def main():
    collector = DataCollector()
    collector.run_collection()


if __name__ == "__main__":
    main()
