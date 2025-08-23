# Dockerfile para o projeto CloudDataOrchestrator v2.0
FROM python:3.9-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt .
COPY lambda/requirements.txt ./lambda_requirements.txt

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r lambda_requirements.txt

# Criar diretórios necessários
RUN mkdir -p models logs cache

# Copiar código da aplicação
COPY . .

# Expor porta para Streamlit
EXPOSE 8501

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Comando padrão
CMD ["streamlit", "run", "dashboard/app_advanced.py"]
