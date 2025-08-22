import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# Configuração da página
st.set_page_config(page_title="Data Pipeline Dashboard - Teste", layout="wide")

# Título
st.title("📊 Data Pipeline Dashboard - Modo Teste")

# Sidebar
st.sidebar.header("⚙️ Configurações")
st.sidebar.info("Modo de teste ativo - usando dados simulados")


# Função para carregar dados de teste
def load_test_data():
    """Carrega dados de teste dos arquivos JSON"""
    test_data = {}

    # Procurar por arquivos de teste
    for file in os.listdir("."):
        if file.startswith("test_output_") and file.endswith(".json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data_type = file.split("_")[2]  # weather ou currency
                    test_data[data_type] = data
            except Exception as e:
                st.error(f"Erro ao carregar {file}: {str(e)}")

    return test_data


# Carregar dados de teste
test_data = load_test_data()

if not test_data:
    st.warning("Nenhum arquivo de teste encontrado. Execute o data collector primeiro.")
    st.stop()

# Dados de clima
if "weather" in test_data:
    st.header("🌤️ Dados de Clima (Teste)")

    weather_df = pd.DataFrame(test_data["weather"])

    if not weather_df.empty:
        # Gráfico de temperatura
        fig_temp = px.bar(
            weather_df,
            x="city",
            y="temperature",
            title="Temperatura por Cidade (°C) - Dados de Teste",
            color="city",
        )
        st.plotly_chart(fig_temp, use_container_width=True)

        # Gráfico de umidade
        fig_humidity = px.bar(
            weather_df,
            x="city",
            y="humidity",
            title="Umidade por Cidade (%) - Dados de Teste",
            color="city",
        )
        st.plotly_chart(fig_humidity, use_container_width=True)

        # Tabela de dados
        st.subheader("📋 Dados Detalhados")
        st.dataframe(weather_df, use_container_width=True)
else:
    st.info("Nenhum dado de clima disponível")

# Dados de câmbio
if "currency" in test_data:
    st.header("💱 Dados de Câmbio (Teste)")

    currency_df = pd.DataFrame(test_data["currency"])

    if not currency_df.empty:
        # Gráfico de taxas
        fig_currency = px.bar(
            currency_df,
            x="target_currency",
            y="rate",
            title="Taxa de Câmbio (USD) - Dados de Teste",
            color="target_currency",
        )
        st.plotly_chart(fig_currency, use_container_width=True)

        # Tabela de dados
        st.subheader("📋 Dados Detalhados")
        st.dataframe(currency_df, use_container_width=True)
else:
    st.info("Nenhum dado de câmbio disponível")

# Estatísticas
st.header("📈 Estatísticas")
col1, col2, col3 = st.columns(3)

total_records = sum(len(data) for data in test_data.values())
with col1:
    st.metric("Total de Registros", total_records)

with col2:
    st.metric("Última Atualização", datetime.now().strftime("%H:%M:%S"))

with col3:
    st.metric("Status", "🟡 Modo Teste")

# Informações sobre os arquivos de teste
st.header("📁 Arquivos de Teste")
test_files = [f for f in os.listdir(".") if f.startswith("test_output_")]
if test_files:
    for file in test_files:
        file_info = os.stat(file)
        st.text(
            f"📄 {file} - {file_info.st_size} bytes - {datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}"
        )
else:
    st.info("Nenhum arquivo de teste encontrado")

# Footer
st.markdown("---")
st.markdown(
    "Dashboard em modo de teste | Dados simulados | Powered by Streamlit + Plotly"
)
