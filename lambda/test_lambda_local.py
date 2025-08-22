import json
import os
from data_handler import lambda_handler

# Configurar variáveis de ambiente para teste
os.environ["DYNAMODB_TABLE"] = "data-pipeline-table"


def test_lambda_function():
    """Testa a função Lambda localmente"""

    print("🧪 Testando função Lambda localmente...")

    # Teste 1: GET sem parâmetros
    print("\n1️⃣ Teste GET sem parâmetros:")
    event_get = {"httpMethod": "GET", "path": "/data", "queryStringParameters": None}

    try:
        response = get_response = lambda_handler(event_get, None)
        print(f"Status: {response['statusCode']}")
        print(f"Body: {response['body'][:200]}...")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

    # Teste 2: POST com dados válidos
    print("\n2️⃣ Teste POST com dados válidos:")
    event_post = {
        "httpMethod": "POST",
        "path": "/data",
        "body": json.dumps(
            {
                "type": "weather",
                "data": {"city": "São Paulo", "temperature": 25.5, "humidity": 70},
            }
        ),
    }

    try:
        response = lambda_handler(event_post, None)
        print(f"Status: {response['statusCode']}")
        print(f"Body: {response['body']}")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

    # Teste 3: GET com ID específico
    print("\n3️⃣ Teste GET com ID específico:")
    event_get_id = {
        "httpMethod": "GET",
        "path": "/data",
        "queryStringParameters": {"id": "weather_2025-08-21T21:17:11.632706"},
    }

    try:
        response = lambda_handler(event_get_id, None)
        print(f"Status: {response['statusCode']}")
        print(f"Body: {response['body']}")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

    # Teste 4: PUT para atualizar
    print("\n4️⃣ Teste PUT para atualizar:")
    event_put = {
        "httpMethod": "PUT",
        "path": "/data",
        "body": json.dumps(
            {
                "id": "weather_2025-08-21T21:17:11.632706",
                "type": "weather",
                "data": {"city": "São Paulo", "temperature": 26.0, "humidity": 75},
            }
        ),
    }

    try:
        response = lambda_handler(event_put, None)
        print(f"Status: {response['statusCode']}")
        print(f"Body: {response['body']}")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

    # Teste 5: DELETE
    print("\n5️⃣ Teste DELETE:")
    event_delete = {
        "httpMethod": "DELETE",
        "path": "/data",
        "queryStringParameters": {"id": "weather_2025-08-21T21:17:11.632706"},
    }

    try:
        response = lambda_handler(event_delete, None)
        print(f"Status: {response['statusCode']}")
        print(f"Body: {response['body']}")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

    print("\n✅ Testes concluídos!")


if __name__ == "__main__":
    test_lambda_function()
