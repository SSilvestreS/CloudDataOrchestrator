import pytest
import unittest.mock as mock
from data_pipeline.data_collector import DataCollector


class TestDataCollector:
    """Testes para a classe DataCollector"""

    @pytest.fixture
    def collector(self):
        """Fixture para criar instância do DataCollector"""
        with mock.patch("boto3.resource"):
            return DataCollector()

    def test_init(self, collector):
        """Testa inicialização do coletor"""
        assert collector.cities == ["São Paulo", "Rio de Janeiro", "Brasília"]
        assert collector.table_name == "data-pipeline-table"

    @mock.patch("requests.get")
    def test_collect_weather_data_success(self, mock_get, collector):
        """Testa coleta bem-sucedida de dados de clima"""
        # Mock da resposta da API
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 25.5, "humidity": 70},
            "weather": [{"description": "céu limpo"}],
        }
        mock_get.return_value = mock_response

        # Mock da API key
        collector.openweather_api_key = "test_key"

        result = collector.collect_weather_data()

        assert len(result) == 3  # 3 cidades
        assert result[0]["city"] == "São Paulo"
        assert result[0]["temperature"] == 25.5
        assert result[0]["humidity"] == 70

    @mock.patch("requests.get")
    def test_collect_weather_data_no_api_key(self, mock_get, collector):
        """Testa coleta sem API key configurada"""
        collector.openweather_api_key = None

        result = collector.collect_weather_data()

        assert result == []
        mock_get.assert_not_called()

    @mock.patch("requests.get")
    def test_collect_currency_data_success(self, mock_get, collector):
        """Testa coleta bem-sucedida de dados de câmbio"""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rates": {"EUR": 0.85, "GBP": 0.73, "JPY": 110.5, "BRL": 5.2}
        }
        mock_get.return_value = mock_response

        result = collector.collect_currency_data()

        assert len(result) == 4  # 4 moedas
        assert result[0]["base_currency"] == "USD"
        assert result[0]["target_currency"] == "EUR"
        assert result[0]["rate"] == 0.85

    @mock.patch("requests.get")
    def test_collect_currency_data_api_error(self, mock_get, collector):
        """Testa erro na API de câmbio"""
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = collector.collect_currency_data()

        assert result == []

    def test_save_to_dynamodb(self, collector):
        """Testa salvamento no DynamoDB"""
        test_data = [
            {"city": "São Paulo", "temp": 25},
            {"city": "Rio de Janeiro", "temp": 30},
        ]

        with mock.patch.object(collector.table, "put_item") as mock_put:
            collector.save_to_dynamodb(test_data, "weather")

            # Verifica se put_item foi chamado 2 vezes
            assert mock_put.call_count == 2

            # Verifica se os dados foram passados corretamente
            calls = mock_put.call_args_list
            assert "weather" in calls[0][1]["Item"]["type"]
            assert "weather" in calls[1][1]["Item"]["type"]

    def test_run_collection(self, collector):
        """Testa execução completa da coleta"""
        with (
            mock.patch.object(collector, "collect_weather_data") as mock_weather,
            mock.patch.object(collector, "collect_currency_data") as mock_currency,
            mock.patch.object(collector, "save_to_dynamodb") as mock_save,
        ):

            mock_weather.return_value = [{"city": "SP", "temp": 25}]
            mock_currency.return_value = [{"currency": "EUR", "rate": 0.85}]

            collector.run_collection()

            # Verifica se todos os métodos foram chamados
            mock_weather.assert_called_once()
            mock_currency.assert_called_once()
            assert mock_save.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])
