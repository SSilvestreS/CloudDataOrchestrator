# Projeto AWS Serverless + Data Pipeline + DevOps

Este projeto demonstra uma arquitetura completa de integração AWS com data pipeline e dashboard, incluindo CI/CD automatizado.

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Lambda        │
│   (Streamlit)   │◄──►│                 │◄──►│   Functions     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   DynamoDB      │    │   Data Pipeline │
                       │   (Storage)     │    │   (Scheduler)   │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Componentes

### 1. Serviço Serverless
- **AWS Lambda**: Funções para CRUD de dados
- **API Gateway**: Endpoints REST para comunicação
- **DynamoDB**: Banco de dados NoSQL

### 2. Data Pipeline
- **Coleta**: APIs de clima, moedas e GitHub
- **Processamento**: Limpeza e estruturação dos dados
- **Armazenamento**: DynamoDB com particionamento otimizado

### 3. Dashboard
- **Streamlit**: Interface web responsiva
- **Plotly**: Gráficos interativos
- **Visualizações**: Dados em tempo real

### 4. DevOps
- **Docker**: Containerização da aplicação
- **GitHub Actions**: Pipeline CI/CD automatizado
- **Infraestrutura**: Terraform para recursos AWS

## 📁 Estrutura do Projeto

```
├── lambda/                 # Funções AWS Lambda
├── api/                   # Definições API Gateway
├── data_pipeline/         # Scripts de coleta de dados
├── dashboard/             # Aplicação Streamlit
├── infrastructure/        # Terraform e configurações AWS
├── docker/               # Dockerfiles e docker-compose
├── .github/              # GitHub Actions workflows
├── requirements.txt       # Dependências Python
└── README.md             # Este arquivo
```

## 🛠️ Pré-requisitos

- Python 3.9+
- Docker e Docker Compose
- AWS CLI configurado
- Terraform
- Conta GitHub

## 🚀 Como Executar

### 1. Configuração Local
```bash
# Clone o repositório
git clone <seu-repo>
cd nova-pasta

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais AWS
```

### 2. Executar com Docker
```bash
# Build e execução
docker-compose up --build

# Dashboard disponível em: http://localhost:8501
```

### 3. Deploy na AWS
```bash
# Deploy da infraestrutura
cd infrastructure
terraform init
terraform plan
terraform apply

# Deploy das funções Lambda
cd ../lambda
./deploy.sh
```

## 📊 APIs Utilizadas

- **Clima**: OpenWeatherMap API
- **Moedas**: Exchange Rate API
- **GitHub**: GitHub REST API

## 🔧 Configuração AWS

1. Configure suas credenciais AWS
2. Crie um bucket S3 para armazenar dados
3. Configure DynamoDB com as tabelas necessárias
4. Deploy das funções Lambda via API Gateway

## 📈 Monitoramento

- CloudWatch Logs para Lambda
- CloudWatch Metrics para DynamoDB
- X-Ray para tracing distribuído

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

Para dúvidas ou problemas, abra uma issue no GitHub ou entre em contato com a equipe.
