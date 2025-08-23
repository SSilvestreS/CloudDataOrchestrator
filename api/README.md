# 📡 CloudDataOrchestrator API v2.0

API REST completa para integração externa com o CloudDataOrchestrator v2.0.

## 🚀 **Inicialização**

### **Executar API**
```bash
# Método 1: Script dedicado
python run_api.py

# Método 2: Uvicorn direto
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Método 3: Docker
docker-compose up api
```

### **Configuração**
```bash
# Variáveis de ambiente
export API_TOKEN="your-secure-token"
export API_HOST="0.0.0.0"
export API_PORT="8000"
export API_RELOAD="true"
export LOG_LEVEL="INFO"
```

## 📚 **Documentação**

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🔐 **Autenticação**

Todas as rotas (exceto `/` e `/health`) requerem autenticação Bearer Token:

```bash
curl -H "Authorization: Bearer clouddataorchestrator-api-key" \
     http://localhost:8000/status
```

## 📋 **Endpoints Principais**

### **🏥 Saúde e Status**
```
GET  /                    # Informações básicas da API
GET  /health              # Health check completo
GET  /status              # Status detalhado do sistema
```

### **📊 Métricas**
```
GET  /metrics             # Todas as métricas
GET  /metrics/system      # Métricas do sistema
GET  /metrics/pipeline    # Métricas do pipeline
```

### **🚨 Alertas**
```
GET  /alerts              # Alertas ativos
POST /alerts              # Criar regra de alerta
GET  /alerts/history      # Histórico de alertas
POST /alerts/{id}/acknowledge  # Reconhecer alerta
```

### **🤖 Machine Learning**
```
GET  /ml/anomalies        # Anomalias detectadas
POST /ml/detect           # Detectar anomalias
GET  /ml/stats            # Estatísticas de ML
```

### **🔌 Provedores de Dados**
```
GET  /providers           # Listar provedores
POST /providers/fetch     # Buscar dados
GET  /providers/stats     # Estatísticas dos provedores
```

### **💾 Cache**
```
GET    /cache/stats       # Estatísticas do cache
DELETE /cache             # Limpar cache
```

### **⚙️ Controle do Sistema**
```
POST /system/start        # Iniciar sistema
POST /system/stop         # Parar sistema
POST /system/restart      # Reiniciar sistema
```

## 💡 **Exemplos de Uso**

### **Health Check**
```bash
curl http://localhost:8000/health
```

### **Obter Métricas**
```bash
curl -H "Authorization: Bearer clouddataorchestrator-api-key" \
     http://localhost:8000/metrics
```

### **Criar Alerta**
```bash
curl -X POST \
  -H "Authorization: Bearer clouddataorchestrator-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CPU Alto",
    "metric": "cpu_percent",
    "threshold": 80,
    "operator": ">",
    "severity": "warning",
    "channels": ["email", "slack"],
    "description": "CPU usage above 80%"
  }' \
  http://localhost:8000/alerts
```

### **Detectar Anomalias**
```bash
curl -X POST \
  -H "Authorization: Bearer clouddataorchestrator-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [1.2, 1.3, 1.1, 5.6, 1.4, 1.2],
    "algorithm": "isolation_forest",
    "threshold": 0.95
  }' \
  http://localhost:8000/ml/detect
```

## 🐳 **Docker**

### **Dockerfile para API**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_api.py"]
```

### **Docker Compose**
```yaml
api:
  build: .
  ports:
    - "8000:8000"
  environment:
    - API_TOKEN=your-secure-token
  volumes:
    - .:/app
```

## 🔧 **Desenvolvimento**

### **Executar em Modo Desenvolvimento**
```bash
# Com reload automático
python run_api.py

# Ou com uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### **Testes**
```bash
# Instalar dependências de teste
pip install httpx pytest-asyncio

# Executar testes da API
pytest api/tests/
```

## 📈 **Monitoramento**

A API inclui:
- ✅ Health checks automáticos
- 📊 Métricas de performance
- 📝 Logging estruturado
- 🔍 Tratamento de erros
- 🛡️ Middleware de CORS
- 🔐 Autenticação Bearer Token

## 🚨 **Segurança**

- **Autenticação**: Bearer Token obrigatório
- **CORS**: Configurável por ambiente
- **Rate Limiting**: Implementar conforme necessário
- **Validação**: Pydantic models para todos os endpoints
- **Logs**: Todos os acessos são logados

## 🔄 **Integração**

A API pode ser integrada com:
- **Frontend Web**: React, Vue, Angular
- **Mobile Apps**: Flutter, React Native
- **Microserviços**: Outros sistemas internos
- **Ferramentas de Monitoramento**: Grafana, Prometheus
- **CI/CD Pipelines**: GitHub Actions, GitLab CI

## 📞 **Suporte**

- **Documentação**: `/docs` (Swagger UI)
- **Status**: `/health` (Health check)
- **Logs**: Consultar logs da aplicação
- **Issues**: GitHub Issues do projeto
