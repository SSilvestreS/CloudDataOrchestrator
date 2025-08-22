import json
from datetime import datetime


# Mock simples da função Lambda
def lambda_handler_mock(event, context):
    """Handler principal da função Lambda para operações CRUD (modo teste)"""

    print(f"Requisição recebida: {event.get('httpMethod')} {event.get('path')}")

    # Roteamento baseado no método HTTP
    http_method = event.get("httpMethod", "GET")

    if http_method == "GET":
        return handle_get_mock(event)
    elif http_method == "POST":
        return handle_post_mock(event)
    elif http_method == "PUT":
        return handle_post_mock(event)  # Simplificado
    elif http_method == "DELETE":
        return handle_post_mock(event)  # Simplificado
    else:
        return create_response(405, {"error": "Método não permitido"})


def handle_get_mock(event):
    """Handler para requisições GET"""
    return create_response(
        200,
        {
            "items": [
                {"id": "test_1", "type": "weather", "data": {"city": "São Paulo"}},
                {"id": "test_2", "type": "currency", "data": {"currency": "EUR"}},
            ],
            "count": 2,
        },
    )


def handle_post_mock(event):
    """Handler para requisições POST"""
    try:
        body = json.loads(event.get("body", "{}"))
        item_id = f"{body.get('type', 'unknown')}_{datetime.now().isoformat()}"

        return create_response(
            201, {"message": "Item criado com sucesso", "id": item_id}
        )
    except:
        return create_response(400, {"error": "JSON inválido"})


def create_response(status_code, body):
    """Cria resposta padronizada"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def test_lambda_function():
    """Testa a função Lambda localmente"""

    print("🧪 Testando função Lambda localmente (modo mock)...")

    # Teste 1: GET
    print("\n1️⃣ Teste GET:")
    event_get = {"httpMethod": "GET", "path": "/data"}
    response = lambda_handler_mock(event_get, None)
    print(f"Status: {response['statusCode']}")
    print(f"Body: {response['body']}")

    # Teste 2: POST
    print("\n2️⃣ Teste POST:")
    event_post = {
        "httpMethod": "POST",
        "path": "/data",
        "body": json.dumps({"type": "weather", "data": {"city": "SP"}}),
    }
    response = lambda_handler_mock(event_post, None)
    print(f"Status: {response['statusCode']}")
    print(f"Body: {response['body']}")

    print("\n✅ Testes concluídos!")


if __name__ == "__main__":
    test_lambda_function()
