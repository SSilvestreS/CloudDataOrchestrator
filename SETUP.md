# 🚀 Guia de Configuração

## 📋 Pré-requisitos
- Python 3.9+
- Docker e Docker Compose
- AWS CLI configurado
- Conta AWS com permissões

## 🔧 Configuração

### 1. Variáveis de Ambiente
```bash
cp env.example .env
# Edite .env com suas credenciais AWS
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar com Docker
```bash
docker-compose up --build
```

### 4. Acessar Dashboard
- URL: http://localhost:8501

## ☁️ Deploy AWS

### 1. Infraestrutura
```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

### 2. Lambda Functions
```bash
cd ../lambda
chmod +x deploy.sh
./deploy.sh
```

## 🧪 Testes
```bash
pytest tests/
```

## 📊 Monitoramento
- Dashboard: http://localhost:8501
- Logs: `docker-compose logs -f`
- CloudWatch: Métricas AWS automáticas
