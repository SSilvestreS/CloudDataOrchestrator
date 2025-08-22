# 🚀 Cloud Data Orchestrator

Sistema avançado e robusto para orquestração de dados em nuvem, implementando padrões de resiliência, monitoramento e qualidade de dados.

## ✨ **Características Principais**

- 🔧 **Sistema de Configuração Avançado** - Gerenciamento centralizado e validação automática
- 📝 **Logging Estruturado** - Logs coloridos para console e estruturados em JSON
- 📊 **Métricas e Monitoramento** - Coleta em tempo real com análise estatística
- 💾 **Cache Inteligente** - Cache em memória e persistente com TTL
- 🔍 **Validação de Dados** - Regras configuráveis e score de qualidade
- 🛡️ **Sistema de Resiliência** - Circuit breaker, retry e fallback patterns
- 🔄 **Pipeline de Dados** - Coleta, validação e armazenamento automatizado
- 🏥 **Health Checks** - Monitoramento de saúde do sistema

## 🏗️ **Arquitetura do Sistema**

```
Cloud Data Orchestrator
├── 📋 config/           # Sistema de configuração
├── 🔧 utils/            # Utilitários do sistema
│   ├── logger.py        # Sistema de logging
│   ├── metrics.py       # Coleta de métricas
│   ├── cache.py         # Sistema de cache
│   ├── validator.py     # Validação de dados
│   └── resilience.py    # Padrões de resiliência
├── 🔄 data_pipeline/    # Pipeline de dados
├── 🚀 integrated_system.py  # Sistema integrado
└── 🧪 test_all_systems.py   # Testes automatizados
```

## 🚀 **Instalação e Configuração**

### **Pré-requisitos**
- Python 3.8+
- Dependências listadas em `requirements.txt`

### **Configuração**
1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure o arquivo `config/config.json`
4. Execute os testes: `python test_all_systems.py`

## 📊 **Sistemas Implementados**

### **1. Sistema de Configuração (`config/settings.py`)**
- Gerenciamento centralizado de configurações
- Validação automática de parâmetros
- Suporte a múltiplos ambientes
- Configurações AWS, banco de dados e APIs

### **2. Sistema de Logging (`utils/logger.py`)**
- Logging colorido para console
- Logging estruturado em JSON
- Rotação automática de arquivos
- Decorators para logging de tempo de execução

### **3. Sistema de Métricas (`utils/metrics.py`)**
- Coleta de métricas em tempo real
- Análise estatística (P95, P99)
- Export para JSON e Prometheus
- Health checks automatizados

### **4. Sistema de Cache (`utils/cache.py`)**
- Cache em memória com TTL
- Cache persistente em disco
- Decorator para cache automático
- Estatísticas de performance

### **5. Sistema de Validação (`utils/validator.py`)**
- Regras de validação configuráveis
- Validação em lote
- Score de qualidade dos dados
- Recomendações automáticas

### **6. Sistema de Resiliência (`utils/resilience.py`)**
- Circuit Breaker pattern
- Retry com backoff exponencial
- Fallback automático
- Gerenciamento centralizado

### **7. Data Collector (`data_pipeline/data_collector_enhanced.py`)**
- Coleta de dados com métricas
- Integração com todos os sistemas
- Tratamento de erros robusto
- Dados simulados para teste

### **8. Sistema Integrado (`integrated_system.py`)**
- Orquestração de todos os componentes
- Pipeline completo de dados
- Manutenção automática
- Monitoramento integrado

## 🧪 **Testes**

Execute todos os testes com:
```bash
python test_all_systems.py
```

Ou teste sistemas individuais:
```bash
python utils/cache.py          # Teste do sistema de cache
python utils/validator.py      # Teste do sistema de validação
python utils/resilience.py     # Teste do sistema de resiliência
python integrated_system.py    # Teste do sistema integrado
```

## 📈 **Monitoramento e Métricas**

### **Métricas Coletadas**
- Tempo de execução de operações
- Taxa de sucesso/erro
- Uso de cache (hits/misses)
- Qualidade dos dados validados
- Health checks do sistema

### **Health Checks**
- Status do cache
- Validação de configurações
- Disponibilidade de métricas
- Estado dos circuit breakers

## 🔧 **Manutenção**

O sistema inclui funcionalidades automáticas de manutenção:
- Limpeza de dados antigos
- Verificação de saúde
- Validação de configurações
- Monitoramento de performance

## 🚀 **Uso em Produção**

### **Configurações Recomendadas**
- Ajustar TTLs de cache conforme necessidade
- Configurar thresholds de circuit breaker
- Definir estratégias de retry apropriadas
- Configurar rotação de logs

### **Monitoramento**
- Configurar alertas para métricas críticas
- Monitorar health checks
- Acompanhar qualidade dos dados
- Verificar performance do cache

## 📝 **Logs e Debugging**

### **Níveis de Log**
- `DEBUG`: Informações detalhadas para debugging
- `INFO`: Informações gerais do sistema
- `WARNING`: Avisos sobre situações não críticas
- `ERROR`: Erros que precisam de atenção

### **Arquivos de Log**
- `logs/*.log`: Logs em formato texto
- `logs/*_structured.json`: Logs estruturados em JSON

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature
3. Implemente e teste suas mudanças
4. Execute todos os testes
5. Faça commit e push
6. Abra um Pull Request

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🎯 **Roadmap Futuro**

- [ ] Interface web para monitoramento
- [ ] Integração com mais provedores de dados
- [ ] Sistema de alertas avançado
- [ ] Machine Learning para detecção de anomalias
- [ ] API REST para integração externa
- [ ] Dashboard de métricas em tempo real

## 📞 **Suporte**

Para dúvidas ou suporte:
- Abra uma issue no GitHub
- Consulte a documentação
- Execute os testes para verificar funcionamento

---

**🎉 Sistema funcionando perfeitamente com 8/8 testes passando!**
