import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Data Pipeline Dashboard", layout="wide")

# Título
st.title("📊 Data Pipeline Dashboard")

# Sidebar
st.sidebar.header("⚙️ Configurações")
api_url = st.sidebar.text_input(
    "URL da API", "https://your-api-gateway-url.amazonaws.com/prod"
)


# Função para buscar dados
@st.cache_data(ttl=300)
def fetch_data(data_type):
    try:
        response = requests.get(f"{api_url}/data?type={data_type}")
        if response.status_code == 200:
            return response.json().get("items", [])
        return []
    except:
        return []


# Dados de clima
st.header("🌤️ Dados de Clima")
weather_data = fetch_data("weather")

if weather_data:
    # Processar dados
    processed_weather = []
    for item in weather_data:
        if "data" in item:
            weather = item["data"]
            processed_weather.append(
                {
                    "city": weather.get("city", "N/A"),
                    "temperature": weather.get("temperature", 0),
                    "humidity": weather.get("humidity", 0),
                    "timestamp": item.get("timestamp", "N/A"),
                }
            )

    weather_df = pd.DataFrame(processed_weather)

    if not weather_df.empty:
        # Gráfico de temperatura
        fig_temp = px.bar(
            weather_df, x="city", y="temperature", title="Temperatura por Cidade (°C)"
        )
        st.plotly_chart(fig_temp, use_container_width=True)

        # Tabela de dados
        st.dataframe(weather_df)
else:
    st.info("Nenhum dado de clima disponível")

# Dados de câmbio
st.header("💱 Dados de Câmbio")
currency_data = fetch_data("currency")

if currency_data:
    processed_currency = []
    for item in currency_data:
        if "data" in item:
            currency = item["data"]
            processed_currency.append(
                {
                    "target_currency": currency.get("target_currency", "N/A"),
                    "rate": currency.get("rate", 0),
                    "timestamp": item.get("timestamp", "N/A"),
                }
            )

    currency_df = pd.DataFrame(processed_currency)

    if not currency_df.empty:
        # Gráfico de taxas
        fig_currency = px.bar(
            currency_df, x="target_currency", y="rate", title="Taxa de Câmbio (USD)"
        )
        st.plotly_chart(fig_currency, use_container_width=True)

        # Tabela de dados
        st.dataframe(currency_df)
else:
    st.info("Nenhum dado de câmbio disponível")

# Estatísticas
st.header("📈 Estatísticas")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total de Registros", len(weather_data) + len(currency_data))

with col2:
    st.metric("Última Atualização", datetime.now().strftime("%H:%M:%S"))

with col3:
    st.metric("Status", "🟢 Ativo")
