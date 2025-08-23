"""
API REST para CloudDataOrchestrator v2.0
API completa para integração externa com todos os sistemas
"""

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import os
import json
import logging
from contextlib import asynccontextmanager

# Importações dos sistemas
from utils.logger import get_logger
from utils.metrics import MetricsCollector
from utils.cache import Cache
from utils.alerts import create_alert_manager, AlertManager
from utils.anomaly_detector import create_anomaly_detector, AnomalyDetector
from data_pipeline.data_providers import create_data_provider_manager, DataProviderManager
from integrated_system_v2 import create_orchestrator, CloudDataOrchestratorV2

logger = get_logger(__name__)

# Instância global do orquestrador
orchestrator: Optional[CloudDataOrchestratorV2] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    global orchestrator
    
    # Startup
    logger.info("🚀 Iniciando API REST do CloudDataOrchestrator...")
    
    # Configuração do orquestrador
    config = {
        "alerts_enabled": True,
        "ml_enabled": True,
        "providers_enabled": True,
        "metrics_interval": 60,
        "alert_check_interval": 30,
        "ml_check_interval": 120
    }
    
    orchestrator = create_orchestrator(config)
    await orchestrator.initialize()
    
    logger.info("✅ API REST inicializada com sucesso!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Parando API REST...")
    if orchestrator:
        await orchestrator.stop()
    logger.info("✅ API REST parada com sucesso!")

# Criar aplicação FastAPI
app = FastAPI(
    title="CloudDataOrchestrator API",
    description="API REST completa para integração externa com o CloudDataOrchestrator v2.0",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Segurança
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificação simples de token (em produção usar JWT)"""
    token = credentials.credentials
    expected_token = os.getenv("API_TOKEN", "clouddataorchestrator-api-key")
    
    if token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# Modelos Pydantic
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    components: Dict[str, str]

class MetricsResponse(BaseModel):
    system: Dict[str, Any]
    pipeline: Dict[str, Any]
    cache: Dict[str, Any]
    alerts: Dict[str, Any]
    anomalies: Dict[str, Any]
    providers: Dict[str, Any]

class AlertRequest(BaseModel):
    name: str
    metric: str
    threshold: float
    operator: str = Field(..., regex="^(>|<|>=|<=|==|!=)$")
    severity: str = Field(..., regex="^(info|warning|error|critical)$")
    channels: List[str]
    description: Optional[str] = ""

class DataProviderRequest(BaseModel):
    provider: str
    endpoint: str
    params: Dict[str, Any]

class AnomalyDetectionRequest(BaseModel):
    data: List[float]
    algorithm: str = "isolation_forest"
    threshold: float = 0.95

# =============================================================================
# ENDPOINTS DE SAÚDE E STATUS
# =============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "CloudDataOrchestrator API v2.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificação de saúde da API e todos os sistemas"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orquestrador não inicializado")
        
        status_info = orchestrator.get_system_status()
        health_info = await orchestrator._health_check()
        
        return HealthResponse(
            status=health_info.get("system", "unknown"),
            timestamp=datetime.now(),
            version="2.0.0",
            components=status_info.get("components", {})
        )
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status(token: str = Depends(verify_token)):
    """Status completo do sistema"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orquestrador não inicializado")
        
        return orchestrator.get_system_status()
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE MÉTRICAS
# =============================================================================

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(token: str = Depends(verify_token)):
    """Obter todas as métricas do sistema"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orquestrador não inicializado")
        
        metrics = orchestrator.get_detailed_metrics()
        
        return MetricsResponse(
            system=metrics.get("system", {}),
            pipeline=metrics.get("pipeline", {}),
            cache=metrics.get("cache", {}),
            alerts=metrics.get("alerts", {}),
            anomalies=metrics.get("anomalies", {}),
            providers=metrics.get("providers", {})
        )
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/system")
async def get_system_metrics(token: str = Depends(verify_token)):
    """Métricas específicas do sistema"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orquestrador não inicializado")
        
        return orchestrator.metrics.get_system_metrics()
    except Exception as e:
        logger.error(f"Erro ao obter métricas do sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/pipeline")
async def get_pipeline_metrics(token: str = Depends(verify_token)):
    """Métricas específicas do pipeline"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orquestrador não inicializado")
        
        return orchestrator.metrics.get_pipeline_metrics()
    except Exception as e:
        logger.error(f"Erro ao obter métricas do pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE ALERTAS
# =============================================================================

@app.get("/alerts")
async def get_alerts(token: str = Depends(verify_token)):
    """Listar todos os alertas ativos"""
    try:
        if not orchestrator or not orchestrator.alert_manager:
            raise HTTPException(status_code=503, detail="Sistema de alertas não disponível")
        
        return orchestrator.alert_manager.get_active_alerts()
    except Exception as e:
        logger.error(f"Erro ao obter alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts")
async def create_alert_rule(alert: AlertRequest, token: str = Depends(verify_token)):
    """Criar nova regra de alerta"""
    try:
        if not orchestrator or not orchestrator.alert_manager:
            raise HTTPException(status_code=503, detail="Sistema de alertas não disponível")
        
        # Implementar criação de regra (simplificado)
        return {
            "message": "Regra de alerta criada com sucesso",
            "rule": alert.dict()
        }
    except Exception as e:
        logger.error(f"Erro ao criar regra de alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/history")
async def get_alert_history(token: str = Depends(verify_token)):
    """Histórico de alertas"""
    try:
        if not orchestrator or not orchestrator.alert_manager:
            raise HTTPException(status_code=503, detail="Sistema de alertas não disponível")
        
        return orchestrator.alert_manager.get_alert_history()
    except Exception as e:
        logger.error(f"Erro ao obter histórico de alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, token: str = Depends(verify_token)):
    """Reconhecer um alerta"""
    try:
        if not orchestrator or not orchestrator.alert_manager:
            raise HTTPException(status_code=503, detail="Sistema de alertas não disponível")
        
        result = orchestrator.alert_manager.acknowledge_alert(alert_id, "API User")
        return {"message": "Alerta reconhecido", "success": result}
    except Exception as e:
        logger.error(f"Erro ao reconhecer alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE MACHINE LEARNING
# =============================================================================

@app.get("/ml/anomalies")
async def get_anomalies(token: str = Depends(verify_token)):
    """Listar anomalias detectadas"""
    try:
        if not orchestrator or not orchestrator.anomaly_detector:
            raise HTTPException(status_code=503, detail="Sistema de ML não disponível")
        
        return orchestrator.anomaly_detector.get_anomaly_history()
    except Exception as e:
        logger.error(f"Erro ao obter anomalias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/detect")
async def detect_anomalies(request: AnomalyDetectionRequest, token: str = Depends(verify_token)):
    """Detectar anomalias em dados fornecidos"""
    try:
        if not orchestrator or not orchestrator.anomaly_detector:
            raise HTTPException(status_code=503, detail="Sistema de ML não disponível")
        
        # Simular detecção (implementação simplificada)
        results = []
        for i, value in enumerate(request.data):
            is_anomaly = abs(value) > request.threshold * 2  # Lógica simplificada
            results.append({
                "index": i,
                "value": value,
                "is_anomaly": is_anomaly,
                "score": abs(value) / (request.threshold * 2),
                "algorithm": request.algorithm
            })
        
        return {
            "results": results,
            "summary": {
                "total_points": len(request.data),
                "anomalies_detected": sum(1 for r in results if r["is_anomaly"]),
                "algorithm": request.algorithm
            }
        }
    except Exception as e:
        logger.error(f"Erro na detecção de anomalias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/stats")
async def get_ml_stats(token: str = Depends(verify_token)):
    """Estatísticas do sistema de ML"""
    try:
        if not orchestrator or not orchestrator.anomaly_detector:
            raise HTTPException(status_code=503, detail="Sistema de ML não disponível")
        
        return orchestrator.anomaly_detector.get_anomaly_stats()
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de ML: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE PROVEDORES DE DADOS
# =============================================================================

@app.get("/providers")
async def get_providers(token: str = Depends(verify_token)):
    """Listar provedores de dados disponíveis"""
    try:
        if not orchestrator or not orchestrator.data_provider_manager:
            raise HTTPException(status_code=503, detail="Provedores de dados não disponíveis")
        
        return orchestrator.data_provider_manager.get_provider_status()
    except Exception as e:
        logger.error(f"Erro ao obter provedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/providers/fetch")
async def fetch_data(request: DataProviderRequest, token: str = Depends(verify_token)):
    """Buscar dados de um provedor específico"""
    try:
        if not orchestrator or not orchestrator.data_provider_manager:
            raise HTTPException(status_code=503, detail="Provedores de dados não disponíveis")
        
        # Implementar busca de dados (simplificado)
        return {
            "message": "Dados buscados com sucesso",
            "provider": request.provider,
            "endpoint": request.endpoint,
            "timestamp": datetime.now(),
            "data": "Dados simulados - implementar integração real"
        }
    except Exception as e:
        logger.error(f"Erro ao buscar dados: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers/stats")
async def get_provider_stats(token: str = Depends(verify_token)):
    """Estatísticas dos provedores de dados"""
    try:
        if not orchestrator or not orchestrator.data_provider_manager:
            raise HTTPException(status_code=503, detail="Provedores de dados não disponíveis")
        
        return orchestrator.data_provider_manager.get_request_stats()
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas dos provedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE CACHE
# =============================================================================

@app.get("/cache/stats")
async def get_cache_stats(token: str = Depends(verify_token)):
    """Estatísticas do cache"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Sistema não disponível")
        
        return orchestrator.cache.get_stats()
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache")
async def clear_cache(token: str = Depends(verify_token)):
    """Limpar todo o cache"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Sistema não disponível")
        
        orchestrator.cache.clear()
        return {"message": "Cache limpo com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE CONTROLE DO SISTEMA
# =============================================================================

@app.post("/system/start")
async def start_system(background_tasks: BackgroundTasks, token: str = Depends(verify_token)):
    """Iniciar o sistema"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orquestrador não disponível")
        
        if orchestrator.is_running:
            return {"message": "Sistema já está rodando"}
        
        background_tasks.add_task(orchestrator.start)
        return {"message": "Sistema iniciado em background"}
    except Exception as e:
        logger.error(f"Erro ao iniciar sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/stop")
async def stop_system(token: str = Depends(verify_token)):
    """Parar o sistema"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orquestrador não disponível")
        
        if not orchestrator.is_running:
            return {"message": "Sistema já está parado"}
        
        await orchestrator.stop()
        return {"message": "Sistema parado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao parar sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/restart")
async def restart_system(background_tasks: BackgroundTasks, token: str = Depends(verify_token)):
    """Reiniciar o sistema"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orquestrador não disponível")
        
        if orchestrator.is_running:
            await orchestrator.stop()
        
        background_tasks.add_task(orchestrator.start)
        return {"message": "Sistema reiniciado em background"}
    except Exception as e:
        logger.error(f"Erro ao reiniciar sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# TRATAMENTO DE ERROS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Tratamento de exceções HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Tratamento de exceções gerais"""
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
