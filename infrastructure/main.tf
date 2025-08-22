# Configuração do provider AWS
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "data-pipeline-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "data-pipeline"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC e recursos de rede
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "data-pipeline-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = true
  
  tags = {
    Environment = var.environment
  }
}

# DynamoDB
resource "aws_dynamodb_table" "data_pipeline_table" {
  name           = "data-pipeline-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  
  attribute {
    name = "id"
    type = "S"
  }
  
  attribute {
    name = "type"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "S"
  }
  
  global_secondary_index {
    name            = "TypeTimestampIndex"
    hash_key        = "type"
    range_key       = "timestamp"
    projection_type = "ALL"
  }
  
  tags = {
    Environment = var.environment
  }
}

# IAM Role para Lambda
resource "aws_iam_role" "lambda_role" {
  name = "data-pipeline-lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy para Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "data-pipeline-lambda-policy"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.data_pipeline_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "data_handler" {
  filename         = "../lambda/data_handler.zip"
  function_name    = "data-pipeline-handler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "data_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30
  
  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.data_pipeline_table.name
    }
  }
  
  depends_on = [aws_iam_role_policy.lambda_policy]
}

# API Gateway
resource "aws_api_gateway_rest_api" "data_pipeline_api" {
  name = "data-pipeline-api"
  description = "API para o Data Pipeline"
}

# API Gateway Resource
resource "aws_api_gateway_resource" "data_resource" {
  rest_api_id = aws_api_gateway_rest_api.data_pipeline_api.id
  parent_id   = aws_api_gateway_rest_api.data_pipeline_api.root_resource_id
  path_part   = "data"
}

# API Gateway Method - GET
resource "aws_api_gateway_method" "get_data" {
  rest_api_id   = aws_api_gateway_rest_api.data_pipeline_api.id
  resource_id   = aws_api_gateway_resource.data_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

# API Gateway Method - POST
resource "aws_api_gateway_method" "post_data" {
  rest_api_id   = aws_api_gateway_rest_api.data_pipeline_api.id
  resource_id   = aws_api_gateway_resource.data_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway Integration - GET
resource "aws_api_gateway_integration" "get_integration" {
  rest_api_id = aws_api_gateway_rest_api.data_pipeline_api.id
  resource_id = aws_api_gateway_resource.data_resource.id
  http_method = aws_api_gateway_method.get_data.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.data_handler.invoke_arn
}

# API Gateway Integration - POST
resource "aws_api_gateway_integration" "post_integration" {
  rest_api_id = aws_api_gateway_rest_api.data_pipeline_api.id
  resource_id = aws_api_gateway_resource.data_resource.id
  http_method = aws_api_gateway_method.post_data.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.data_handler.invoke_arn
}

# Lambda Permission para API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.data_pipeline_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "data_pipeline_deployment" {
  depends_on = [
    aws_api_gateway_integration.get_integration,
    aws_api_gateway_integration.post_integration
  ]
  
  rest_api_id = aws_api_gateway_rest_api.data_pipeline_api.id
  stage_name  = "prod"
}

# Outputs
output "api_gateway_url" {
  value = "${aws_api_gateway_deployment.data_pipeline_deployment.invoke_url}/data"
  description = "URL da API Gateway"
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.data_pipeline_table.name
  description = "Nome da tabela DynamoDB"
}

output "lambda_function_name" {
  value = aws_lambda_function.data_handler.function_name
  description = "Nome da função Lambda"
}
