import json
import boto3
import logging
from typing import Dict, Any, List
from datetime import datetime
import os

# Configuração de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicialização do cliente DynamoDB
dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("DYNAMODB_TABLE", "data-pipeline-table")
table = dynamodb.Table(table_name)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal da função Lambda para operações CRUD no DynamoDB
    """
    try:
        # Extrair informações da requisição
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "/")

        logger.info(f"Requisição recebida: {http_method} {path}")

        # Roteamento baseado no método HTTP
        if http_method == "GET":
            return handle_get(event)
        elif http_method == "POST":
            return handle_post(event)
        elif http_method == "PUT":
            return handle_put(event)
        elif http_method == "DELETE":
            return handle_delete(event)
        else:
            return create_response(405, {"error": "Método não permitido"})

    except Exception as e:
        logger.error(f"Erro na execução: {str(e)}")
        return create_response(500, {"error": "Erro interno do servidor"})


def handle_get(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handler para requisições GET"""
    try:
        # Extrair parâmetros da query string
        query_params = event.get("queryStringParameters", {}) or {}

        if "id" in query_params:
            # Buscar item específico por ID
            response = table.get_item(Key={"id": query_params["id"]})

            if "Item" in response:
                return create_response(200, response["Item"])
            else:
                return create_response(404, {"error": "Item não encontrado"})
        else:
            # Listar todos os itens (com paginação)
            scan_kwargs = {}
            if "limit" in query_params:
                scan_kwargs["Limit"] = int(query_params["limit"])

            response = table.scan(**scan_kwargs)
            items = response.get("Items", [])

            return create_response(200, {"items": items, "count": len(items)})

    except Exception as e:
        logger.error(f"Erro no GET: {str(e)}")
        return create_response(500, {"error": "Erro ao buscar dados"})


def handle_post(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handler para requisições POST (criar novo item)"""
    try:
        # Extrair corpo da requisição
        body = json.loads(event.get("body", "{}"))

        # Validar dados obrigatórios
        if "type" not in body or "data" not in body:
            return create_response(400, {"error": "Campos obrigatórios: type, data"})

        # Gerar ID único
        item_id = f"{body['type']}_{datetime.now().isoformat()}"

        # Preparar item para DynamoDB
        item = {
            "id": item_id,
            "type": body["type"],
            "data": body["data"],
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        # Inserir no DynamoDB
        table.put_item(Item=item)

        logger.info(f"Item criado com sucesso: {item_id}")
        return create_response(
            201, {"message": "Item criado com sucesso", "id": item_id, "item": item}
        )

    except json.JSONDecodeError:
        return create_response(400, {"error": "JSON inválido no corpo da requisição"})
    except Exception as e:
        logger.error(f"Erro no POST: {str(e)}")
        return create_response(500, {"error": "Erro ao criar item"})


def handle_put(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handler para requisições PUT (atualizar item existente)"""
    try:
        # Extrair corpo da requisição
        body = json.loads(event.get("body", "{}"))

        if "id" not in body:
            return create_response(400, {"error": "ID é obrigatório para atualização"})

        # Verificar se o item existe
        existing_item = table.get_item(Key={"id": body["id"]})
        if "Item" not in existing_item:
            return create_response(404, {"error": "Item não encontrado"})

        # Preparar atualizações
        update_expression = "SET "
        expression_values = {}

        for key, value in body.items():
            if key != "id" and key != "created_at":
                update_expression += f"#{key} = :{key}, "
                expression_values[f":{key}"] = value
                expression_values[f"#{key}"] = key

        # Adicionar timestamp de atualização
        update_expression += "#updated_at = :updated_at"
        expression_values[":updated_at"] = datetime.now().isoformat()
        expression_values["#updated_at"] = "updated_at"

        # Remover vírgula extra
        update_expression = update_expression.rstrip(", ")

        # Atualizar no DynamoDB
        table.update_item(
            Key={"id": body["id"]},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames={
                k: v for k, v in expression_values.items() if k.startswith("#")
            },
        )

        logger.info(f"Item atualizado com sucesso: {body['id']}")
        return create_response(
            200, {"message": "Item atualizado com sucesso", "id": body["id"]}
        )

    except json.JSONDecodeError:
        return create_response(400, {"error": "JSON inválido no corpo da requisição"})
    except Exception as e:
        logger.error(f"Erro no PUT: {str(e)}")
        return create_response(500, {"error": "Erro ao atualizar item"})


def handle_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handler para requisições DELETE"""
    try:
        # Extrair ID da query string
        query_params = event.get("queryStringParameters", {}) or {}

        if "id" not in query_params:
            return create_response(400, {"error": "ID é obrigatório para exclusão"})

        # Verificar se o item existe
        existing_item = table.get_item(Key={"id": query_params["id"]})
        if "Item" not in existing_item:
            return create_response(404, {"error": "Item não encontrado"})

        # Excluir do DynamoDB
        table.delete_item(Key={"id": query_params["id"]})

        logger.info(f"Item excluído com sucesso: {query_params['id']}")
        return create_response(
            200, {"message": "Item excluído com sucesso", "id": query_params["id"]}
        )

    except Exception as e:
        logger.error(f"Erro no DELETE: {str(e)}")
        return create_response(500, {"error": "Erro ao excluir item"})


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Cria resposta padronizada para API Gateway"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }
