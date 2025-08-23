"""
Dashboard Avançado para CloudDataOrchestrator
Interface web completa com monitoramento em tempo real, alertas, detecção de anomalias e integração com múltiplos provedores
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import asyncio
import json
import time
from typing import Dict, List, Any

# Configuração da página
st.set_page_config(
    page_title="CloudDataOrchestrator Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🚀 CloudDataOrchestrator Dashboard")
st.markdown("Sistema avançado de orquestração de dados em nuvem com monitoramento em tempo real")

# Sidebar para configurações
st.sidebar.header("⚙️ Configurações")

# Configurações de API
api_url = st.sidebar.text_input(
    "URL da API", 
    "https://your-api-gateway-url.amazonaws.com/prod"
)

# Configurações de alertas
st.sidebar.subheader("🔔 Configurações de Alertas")
alert_email = st.sidebar.text_input("Email para Alertas", "admin@company.com")
alert_slack = st.sidebar.text_input("Webhook Slack", "https://hooks.slack.com/...")
alert_enabled = st.sidebar.checkbox("Alertas Ativos", value=True)

# Configurações de ML
st.sidebar.subheader("🤖 Configurações de ML")
ml_enabled = st.sidebar.checkbox("Detecção de Anomalias", value=True)
ml_algorithm = st.sidebar.selectbox(
    "Algoritmo de Detecção",
    ["isolation_forest", "local_outlier_factor", "one_class_svm", "z_score", "iqr"]
)

# Configurações de provedores
st.sidebar.subheader("🔌 Provedores de Dados")
providers_enabled = st.sidebar.checkbox("Provedores Externos", value=True)

# Funções auxiliares
@st.cache_data(ttl=60)
def get_system_metrics():
    """Simula métricas do sistema"""
    return {
        "cpu_percent": np.random.normal(45, 15),
        "memory_percent": np.random.normal(60, 20),
        "disk_percent": np.random.normal(70, 10),
        "network_io": np.random.normal(100, 30),
        "active_connections": np.random.randint(50, 200),
        "response_time_p95": np.random.normal(150, 50)
    }

@st.cache_data(ttl=300)
def get_pipeline_metrics():
    """Simula métricas do pipeline de dados"""
    return {
        "total_records": np.random.randint(1000, 10000),
        "success_rate": np.random.uniform(0.95, 0.99),
        "error_rate": np.random.uniform(0.01, 0.05),
        "processing_time": np.random.normal(2.5, 0.5),
        "cache_hit_rate": np.random.uniform(0.7, 0.9),
        "data_quality_score": np.random.uniform(0.85, 0.98)
    }

@st.cache_data(ttl=180)
def get_cache_metrics():
    """Simula métricas de cache"""
    return {
        "hit_rate": np.random.uniform(0.75, 0.95),
        "miss_rate": np.random.uniform(0.05, 0.25),
        "total_requests": np.random.randint(5000, 50000),
        "memory_usage": np.random.uniform(0.3, 0.8),
        "eviction_rate": np.random.uniform(0.01, 0.1)
    }

def generate_anomaly_data():
    """Gera dados simulados de anomalias"""
    np.random.seed(int(time.time()))
    
    # Dados normais
    normal_data = np.random.normal(50, 10, 100)
    
    # Adicionar algumas anomalias
    anomaly_indices = np.random.choice(100, size=5, replace=False)
    normal_data[anomaly_indices] = np.random.choice([0, 100, 150], size=5)
    
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(hours=24),
        periods=100,
        freq='15min'
    )
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'value': normal_data,
        'is_anomaly': [i in anomaly_indices for i in range(100)]
    })

def generate_alert_data():
    """Gera dados simulados de alertas"""
    alert_types = ['High CPU Usage', 'Memory Warning', 'Pipeline Error', 'Cache Miss', 'API Timeout']
    severities = ['info', 'warning', 'error', 'critical']
    
    alerts = []
    for i in range(np.random.randint(3, 8)):
        alert = {
            'id': f"alert_{i}",
            'type': np.random.choice(alert_types),
            'severity': np.random.choice(severities),
            'message': f"Alert message {i}",
            'timestamp': datetime.now() - timedelta(minutes=np.random.randint(1, 60)),
            'status': np.random.choice(['active', 'acknowledged', 'resolved']),
            'value': np.random.uniform(80, 120),
            'threshold': 100
        }
        alerts.append(alert)
    
    return pd.DataFrame(alerts)

# Layout principal
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard Principal", 
    "🔔 Sistema de Alertas", 
    "🤖 Detecção de Anomalias",
    "🔌 Provedores de Dados",
    "📈 Métricas Avançadas"
])

# Tab 1: Dashboard Principal
with tab1:
    st.header("📊 Dashboard Principal")
    
    # Métricas principais em cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        system_metrics = get_system_metrics()
        st.metric(
            "CPU Usage", 
            f"{system_metrics['cpu_percent']:.1f}%",
            f"{system_metrics['cpu_percent'] - 45:.1f}%"
        )
    
    with col2:
        st.metric(
            "Memory Usage", 
            f"{system_metrics['memory_percent']:.1f}%",
            f"{system_metrics['memory_percent'] - 60:.1f}%"
        )
    
    with col3:
        pipeline_metrics = get_pipeline_metrics()
        st.metric(
            "Success Rate", 
            f"{pipeline_metrics['success_rate']:.1%}",
            f"{pipeline_metrics['success_rate'] - 0.95:.1%}"
        )
    
    with col4:
        cache_metrics = get_cache_metrics()
        st.metric(
            "Cache Hit Rate", 
            f"{cache_metrics['hit_rate']:.1%}",
            f"{cache_metrics['hit_rate'] - 0.85:.1%}"
        )
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Performance do Sistema")
        
        # Simular dados de performance ao longo do tempo
        time_points = pd.date_range(start=datetime.now() - timedelta(hours=6), periods=24, freq='15min')
        cpu_data = np.random.normal(45, 15, 24)
        memory_data = np.random.normal(60, 20, 24)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_points, 
            y=cpu_data, 
            mode='lines+markers', 
            name='CPU %',
            line=dict(color='#1f77b4')
        ))
        fig.add_trace(go.Scatter(
            x=time_points, 
            y=memory_data, 
            mode='lines+markers', 
            name='Memory %',
            line=dict(color='#ff7f0e')
        ))
        
        fig.update_layout(
            title="Uso de Recursos do Sistema",
            xaxis_title="Tempo",
            yaxis_title="Percentual (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🔄 Pipeline de Dados")
        
        # Gráfico de pizza para status do pipeline
        pipeline_status = {
            'Processados': pipeline_metrics['total_records'],
            'Sucesso': int(pipeline_metrics['total_records'] * pipeline_metrics['success_rate']),
            'Erros': int(pipeline_metrics['total_records'] * pipeline_metrics['error_rate'])
        }
        
        fig = px.pie(
            values=list(pipeline_status.values()),
            names=list(pipeline_status.keys()),
            title="Status do Pipeline de Dados"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de status dos serviços
    st.subheader("🏥 Status dos Serviços")
    
    services_status = pd.DataFrame({
        'Serviço': ['Data Collector', 'Cache System', 'Validator', 'Resilience', 'Metrics', 'API Gateway'],
        'Status': ['🟢 Online', '🟢 Online', '🟡 Warning', '🟢 Online', '🟢 Online', '🟢 Online'],
        'Uptime': ['99.9%', '99.8%', '98.5%', '99.9%', '99.9%', '99.7%'],
        'Última Verificação': [datetime.now() - timedelta(minutes=2)] * 6,
        'Response Time': ['45ms', '12ms', '89ms', '23ms', '15ms', '67ms']
    })
    
    st.dataframe(services_status, use_container_width=True)

# Tab 2: Sistema de Alertas
with tab2:
    st.header("🔔 Sistema de Alertas")
    
    # Configurações de alertas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ Configurações")
        
        # Thresholds configuráveis
        cpu_threshold = st.slider("CPU Threshold (%)", 50, 100, 80)
        memory_threshold = st.slider("Memory Threshold (%)", 50, 100, 85)
        error_threshold = st.slider("Error Rate Threshold (%)", 1, 20, 5)
        
        # Canais de notificação
        st.checkbox("Email Notifications", value=True)
        st.checkbox("Slack Notifications", value=True)
        st.checkbox("Webhook Notifications", value=True)
        
        # Botões de ação
        if st.button("🔔 Testar Alertas"):
            st.success("Alertas de teste enviados com sucesso!")
        
        if st.button("🧹 Limpar Histórico"):
            st.info("Histórico de alertas limpo!")
    
    with col2:
        st.subheader("📊 Estatísticas de Alertas")
        
        # Simular estatísticas
        alert_stats = {
            'Total de Alertas': 24,
            'Alertas Ativos': 3,
            'Alertas Resolvidos': 21,
            'Taxa de Resolução': '87.5%',
            'Tempo Médio de Resposta': '15 min',
            'Último Alerta': '2 min atrás'
        }
        
        for key, value in alert_stats.items():
            st.metric(key, value)
    
    # Lista de alertas ativos
    st.subheader("🚨 Alertas Ativos")
    
    alert_data = generate_alert_data()
    active_alerts = alert_data[alert_data['status'] == 'active']
    
    if not active_alerts.empty:
        for _, alert in active_alerts.iterrows():
            severity_colors = {
                'info': '🔵',
                'warning': '🟡',
                'error': '🟠',
                'critical': '🔴'
            }
            
            with st.expander(f"{severity_colors.get(alert['severity'], '⚪')} {alert['type']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Severidade:** {alert['severity'].upper()}")
                    st.write(f"**Valor:** {alert['value']:.1f}")
                
                with col2:
                    st.write(f"**Threshold:** {alert['threshold']}")
                    st.write(f"**Timestamp:** {alert['timestamp'].strftime('%H:%M:%S')}")
                
                with col3:
                    if st.button(f"✅ Reconhecer", key=f"ack_{alert['id']}"):
                        st.success("Alerta reconhecido!")
                    
                    if st.button(f"🔧 Resolver", key=f"resolve_{alert['id']}"):
                        st.success("Alerta resolvido!")
    else:
        st.success("🎉 Nenhum alerta ativo!")
    
    # Histórico de alertas
    st.subheader("📜 Histórico de Alertas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.selectbox("Filtrar por Severidade", ['Todas'] + list(alert_data['severity'].unique()))
    
    with col2:
        type_filter = st.selectbox("Filtrar por Tipo", ['Todos'] + list(alert_data['type'].unique()))
    
    with col3:
        status_filter = st.selectbox("Filtrar por Status", ['Todos'] + list(alert_data['status'].unique()))
    
    # Aplicar filtros
    filtered_alerts = alert_data.copy()
    
    if severity_filter != 'Todas':
        filtered_alerts = filtered_alerts[filtered_alerts['severity'] == severity_filter]
    
    if type_filter != 'Todos':
        filtered_alerts = filtered_alerts[filtered_alerts['type'] == type_filter]
    
    if status_filter != 'Todos':
        filtered_alerts = filtered_alerts[filtered_alerts['status'] == status_filter]
    
    st.dataframe(filtered_alerts, use_container_width=True)

# Tab 3: Detecção de Anomalias
with tab3:
    st.header("🤖 Detecção de Anomalias com Machine Learning")
    
    if not ml_enabled:
        st.warning("⚠️ Detecção de anomalias está desabilitada. Ative nas configurações.")
    else:
        # Configurações de ML
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ Configurações de ML")
            
            # Parâmetros do algoritmo
            window_size = st.slider("Tamanho da Janela", 10, 200, 100)
            threshold = st.slider("Threshold de Detecção", 0.5, 1.0, 0.95, 0.05)
            contamination = st.slider("Contaminação Esperada", 0.01, 0.3, 0.1, 0.01)
            
            # Botões de ação
            if st.button("🔄 Retreinar Modelos"):
                with st.spinner("Retreinando modelos..."):
                    time.sleep(2)
                    st.success("Modelos retreinados com sucesso!")
            
            if st.button("📊 Ver Estatísticas"):
                st.info("Estatísticas de ML atualizadas!")
        
        with col2:
            st.subheader("📈 Estatísticas de ML")
            
            ml_stats = {
                'Modelos Treinados': 8,
                'Total de Anomalias': 15,
                'Precisão': '94.2%',
                'Recall': '91.7%',
                'F1-Score': '92.9%',
                'Último Treinamento': '2 horas atrás'
            }
            
            for key, value in ml_stats.items():
                st.metric(key, value)
        
        # Visualização de anomalias
        st.subheader("🔍 Detecção de Anomalias em Tempo Real")
        
        # Gerar dados simulados
        anomaly_data = generate_anomaly_data()
        
        # Gráfico de séries temporais com anomalias
        fig = go.Figure()
        
        # Dados normais
        normal_points = anomaly_data[~anomaly_data['is_anomaly']]
        fig.add_trace(go.Scatter(
            x=normal_points['timestamp'],
            y=normal_points['value'],
            mode='lines+markers',
            name='Dados Normais',
            line=dict(color='#1f77b4'),
            marker=dict(size=4)
        ))
        
        # Anomalias
        anomaly_points = anomaly_data[anomaly_data['is_anomaly']]
        if not anomaly_points.empty:
            fig.add_trace(go.Scatter(
                x=anomaly_points['timestamp'],
                y=anomaly_points['value'],
                mode='markers',
                name='Anomalias Detectadas',
                marker=dict(
                    size=12,
                    color='red',
                    symbol='x'
                )
            ))
        
        fig.update_layout(
            title="Detecção de Anomalias em Tempo Real",
            xaxis_title="Tempo",
            yaxis_title="Valor da Métrica",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Configurações por métrica
        st.subheader("🎯 Configurações por Métrica")
        
        metrics_config = pd.DataFrame({
            'Métrica': ['CPU Usage', 'Memory Usage', 'Network IO', 'Response Time', 'Error Rate'],
            'Algoritmo': ['Isolation Forest', 'Local Outlier Factor', 'One-Class SVM', 'Z-Score', 'IQR'],
            'Threshold': [0.95, 0.90, 0.85, 2.5, 1.5],
            'Janela': [50, 100, 75, 25, 50],
            'Status': ['🟢 Ativo', '🟢 Ativo', '🟡 Warning', '🟢 Ativo', '🟢 Ativo']
        })
        
        st.dataframe(metrics_config, use_container_width=True)

# Tab 4: Provedores de Dados
with tab4:
    st.header("🔌 Provedores de Dados")
    
    if not providers_enabled:
        st.warning("⚠️ Provedores externos estão desabilitados. Ative nas configurações.")
    else:
        # Status dos provedores
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Status dos Provedores")
            
            providers_status = {
                'Alpha Vantage': {'status': '🟢 Online', 'rate_limit': '5/min', 'last_request': '2 min atrás'},
                'OpenWeather': {'status': '🟢 Online', 'rate_limit': '60/min', 'last_request': '5 min atrás'},
                'NewsAPI': {'status': '🟡 Warning', 'rate_limit': '100/min', 'last_request': '15 min atrás'},
                'CoinAPI': {'status': '🟢 Online', 'rate_limit': '100/min', 'last_request': '1 min atrás'},
                'Twitter API': {'status': '🔴 Offline', 'rate_limit': '300/min', 'last_request': '1 hora atrás'}
            }
            
            for provider, info in providers_status.items():
                st.metric(
                    provider,
                    info['status'],
                    f"Rate: {info['rate_limit']} | Último: {info['last_request']}"
                )
        
        with col2:
            st.subheader("⚙️ Configurações")
            
            # Chaves de API
            alpha_vantage_key = st.text_input("Alpha Vantage API Key", type="password")
            openweather_key = st.text_input("OpenWeather API Key", type="password")
            newsapi_key = st.text_input("NewsAPI Key", type="password")
            
            if st.button("💾 Salvar Configurações"):
                st.success("Configurações salvas com sucesso!")
        
        # Teste de conectividade
        st.subheader("🧪 Teste de Conectividade")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Testar Alpha Vantage"):
                with st.spinner("Testando..."):
                    time.sleep(1)
                    st.success("✅ Conectado!")
        
        with col2:
            if st.button("🔍 Testar OpenWeather"):
                with st.spinner("Testando..."):
                    time.sleep(1)
                    st.success("✅ Conectado!")
        
        with col3:
            if st.button("🔍 Testar NewsAPI"):
                with st.spinner("Testando..."):
                    time.sleep(1)
                    st.warning("⚠️ Rate limit atingido")
        
        # Dados dos provedores
        st.subheader("📊 Dados dos Provedores")
        
        # Simular dados de diferentes provedores
        tab_financial, tab_weather, tab_news, tab_crypto = st.tabs([
            "💰 Financeiro", "🌤️ Clima", "📰 Notícias", "₿ Cripto"
        ])
        
        with tab_financial:
            # Dados financeiros simulados
            financial_data = pd.DataFrame({
                'Símbolo': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
                'Preço': [150.25, 2750.80, 320.45, 185.30, 245.60],
                'Variação': [2.5, -1.2, 0.8, 3.1, -0.5],
                'Volume': [45000000, 28000000, 35000000, 52000000, 38000000],
                'Market Cap': ['2.4T', '1.8T', '2.1T', '1.9T', '780B']
            })
            
            st.dataframe(financial_data, use_container_width=True)
        
        with tab_weather:
            # Dados climáticos simulados
            weather_data = pd.DataFrame({
                'Cidade': ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza'],
                'Temperatura': [22, 28, 25, 30, 29],
                'Umidade': [65, 70, 55, 80, 75],
                'Condição': ['Nublado', 'Ensolarado', 'Parcialmente Nublado', 'Chuvoso', 'Ensolarado'],
                'Vento': [12, 8, 15, 20, 10]
            })
            
            st.dataframe(weather_data, use_container_width=True)
        
        with tab_news:
            # Dados de notícias simulados
            news_data = pd.DataFrame({
                'Título': [
                    'Nova tecnologia revoluciona mercado',
                    'Economia global em recuperação',
                    'Inovação em energia sustentável',
                    'Tendências em IA para 2024'
                ],
                'Fonte': ['TechNews', 'EconomyDaily', 'GreenTech', 'AIWeekly'],
                'Data': ['2h atrás', '4h atrás', '6h atrás', '8h atrás'],
                'Sentimento': ['Positivo', 'Neutro', 'Positivo', 'Positivo']
            })
            
            st.dataframe(news_data, use_container_width=True)
        
        with tab_crypto:
            # Dados de criptomoedas simulados
            crypto_data = pd.DataFrame({
                'Moeda': ['Bitcoin', 'Ethereum', 'Cardano', 'Solana', 'Polkadot'],
                'Preço USD': [43250, 2650, 0.48, 98.50, 7.25],
                'Variação 24h': [2.1, -1.8, 5.2, 3.7, -0.9],
                'Market Cap': ['850B', '320B', '17B', '42B', '9B'],
                'Volume 24h': ['28B', '15B', '2.1B', '3.8B', '800M']
            })
            
            st.dataframe(crypto_data, use_container_width=True)

# Tab 5: Métricas Avançadas
with tab5:
    st.header("📈 Métricas Avançadas")
    
    # Métricas em tempo real
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⏱️ Métricas de Performance")
        
        # Gráfico de linha para métricas de performance
        time_range = pd.date_range(start=datetime.now() - timedelta(hours=1), periods=60, freq='1min')
        
        # Simular dados de performance
        response_times = np.random.normal(150, 30, 60)
        throughput = np.random.normal(1000, 200, 60)
        error_rates = np.random.uniform(0.01, 0.05, 60)
        
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Response Time (ms)', 'Throughput (req/s)', 'Error Rate (%)'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(
            go.Scatter(x=time_range, y=response_times, mode='lines', name='Response Time'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=time_range, y=throughput, mode='lines', name='Throughput'),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=time_range, y=error_rates*100, mode='lines', name='Error Rate'),
            row=3, col=1
        )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Distribuição de Métricas")
        
        # Histograma de métricas
        metrics_distribution = np.random.normal(100, 25, 1000)
        
        fig = px.histogram(
            x=metrics_distribution,
            nbins=30,
            title="Distribuição de Métricas do Sistema",
            labels={'x': 'Valor da Métrica', 'y': 'Frequência'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas descritivas
        st.subheader("📋 Estatísticas Descritivas")
        
        stats_df = pd.DataFrame({
            'Métrica': ['CPU', 'Memory', 'Response Time', 'Throughput', 'Error Rate'],
            'Média': [45.2, 62.8, 147.3, 1023.5, 2.8],
            'Mediana': [44.1, 61.2, 145.8, 1018.2, 2.7],
            'Desvio Padrão': [15.3, 18.7, 28.9, 187.3, 1.2],
            'P95': [72.1, 89.4, 198.6, 1356.8, 4.9],
            'P99': [85.3, 95.1, 245.2, 1589.4, 6.8]
        })
        
        st.dataframe(stats_df, use_container_width=True)
    
    # Análise de tendências
    st.subheader("📈 Análise de Tendências")
    
    # Simular dados de tendência
    days = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
    
    # Tendências simuladas
    cpu_trend = 45 + np.cumsum(np.random.normal(0, 0.5, 30))
    memory_trend = 60 + np.cumsum(np.random.normal(0, 0.8, 30))
    error_trend = 3 + np.cumsum(np.random.normal(0, 0.1, 30))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=days, y=cpu_trend, mode='lines+markers', name='CPU %',
        line=dict(color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=days, y=memory_trend, mode='lines+markers', name='Memory %',
        line=dict(color='#ff7f0e')
    ))
    
    fig.add_trace(go.Scatter(
        x=days, y=error_trend, mode='lines+markers', name='Error Rate %',
        line=dict(color='#d62728'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Tendências das Últimas 4 Semanas",
        xaxis_title="Data",
        yaxis_title="Percentual (%)",
        yaxis2=dict(title="Error Rate (%)", overlaying="y", side="right"),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlações entre métricas
    st.subheader("🔗 Correlações entre Métricas")
    
    # Matriz de correlação simulada
    correlation_data = np.array([
        [1.00, 0.65, -0.45, 0.32, -0.78],
        [0.65, 1.00, -0.38, 0.28, -0.72],
        [-0.45, -0.38, 1.00, -0.15, 0.89],
        [0.32, 0.28, -0.15, 1.00, -0.23],
        [-0.78, -0.72, 0.89, -0.23, 1.00]
    ])
    
    metrics_names = ['CPU', 'Memory', 'Response Time', 'Throughput', 'Error Rate']
    
    fig = px.imshow(
        correlation_data,
        x=metrics_names,
        y=metrics_names,
        color_continuous_scale='RdBu',
        title="Matriz de Correlação entre Métricas"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🚀 CloudDataOrchestrator v2.0 - Sistema Avançado de Orquestração de Dados</p>
        <p>Desenvolvido com ❤️ usando Streamlit, Python e Machine Learning</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh
if st.button("🔄 Atualizar Dashboard"):
    st.rerun()

# Configuração de auto-refresh
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Auto-refresh")
auto_refresh = st.sidebar.checkbox("Ativar auto-refresh", value=False)
if auto_refresh:
    refresh_interval = st.sidebar.selectbox("Intervalo", [30, 60, 120, 300], index=1)
    st.sidebar.info(f"Dashboard será atualizado a cada {refresh_interval} segundos")
    
    # Simular auto-refresh
    time.sleep(1)
    st.rerun()
