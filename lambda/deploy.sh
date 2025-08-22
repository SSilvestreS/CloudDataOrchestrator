#!/bin/bash

# Script de deploy para funções Lambda
set -e

echo "🚀 Iniciando deploy das funções Lambda..."

# Configurações
FUNCTION_NAME="data-pipeline-handler"
REGION=${AWS_DEFAULT_REGION:-"us-east-1"}
ZIP_FILE="data_handler.zip"

# Verificar se AWS CLI está configurado
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI não está instalado ou configurado"
    exit 1
fi

# Verificar se as credenciais AWS estão configuradas
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Credenciais AWS não estão configuradas"
    exit 1
fi

echo "✅ Credenciais AWS verificadas"

# Criar arquivo ZIP para deploy
echo "📦 Criando pacote de deploy..."
cd "$(dirname "$0")"

# Remover ZIP anterior se existir
if [ -f "$ZIP_FILE" ]; then
    rm "$ZIP_FILE"
fi

# Instalar dependências
echo "📥 Instalando dependências..."
pip install -r requirements.txt -t .

# Criar ZIP
echo "🗜️ Criando arquivo ZIP..."
zip -r "$ZIP_FILE" . -x "*.pyc" "__pycache__/*" "*.git*" "deploy.sh" "requirements.txt"

echo "✅ Arquivo ZIP criado: $ZIP_FILE"

# Verificar se a função Lambda existe
echo "🔍 Verificando se a função Lambda existe..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &> /dev/null; then
    echo "📝 Atualizando função Lambda existente..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION"
    
    echo "✅ Função Lambda atualizada com sucesso!"
else
    echo "❌ Função Lambda '$FUNCTION_NAME' não encontrada"
    echo "💡 Execute primeiro o Terraform para criar a infraestrutura"
    exit 1
fi

# Limpar arquivos temporários
echo "🧹 Limpando arquivos temporários..."
rm -rf *.pyc __pycache__ *.dist-info

echo "🎉 Deploy concluído com sucesso!"
echo "📊 Função: $FUNCTION_NAME"
echo "🌍 Região: $REGION"
