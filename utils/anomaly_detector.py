"""
Sistema de Detecção de Anomalias com Machine Learning para CloudDataOrchestrator
Implementa diferentes algoritmos de ML para detecção de anomalias em dados de métricas
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import joblib
import os
import json
from dataclasses import dataclass, asdict
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

from .logger import get_logger
from .metrics import MetricsCollector

logger = get_logger(__name__)


class AnomalyAlgorithm(Enum):
    """Algoritmos de detecção de anomalias disponíveis"""
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    ONE_CLASS_SVM = "one_class_svm"
    ELLIPTIC_ENVELOPE = "elliptic_envelope"
    DBSCAN = "dbscan"
    Z_SCORE = "z_score"
    IQR = "iqr"
    MAHALANOBIS = "mahalanobis"


@dataclass
class AnomalyDetectionConfig:
    """Configuração para detecção de anomalias"""
    algorithm: AnomalyAlgorithm
    window_size: int = 100  # Tamanho da janela para análise
    threshold: float = 0.95  # Threshold para detecção
    contamination: float = 0.1  # Proporção esperada de anomalias
    min_samples: int = 10  # Mínimo de amostras para treinamento
    retrain_interval_hours: int = 24  # Intervalo para retreinamento
    enabled: bool = True
    
    def __post_init__(self):
        if isinstance(self.algorithm, str):
            self.algorithm = AnomalyAlgorithm(self.algorithm)


@dataclass
class AnomalyResult:
    """Resultado da detecção de anomalias"""
    timestamp: datetime
    metric_name: str
    value: float
    is_anomaly: bool
    anomaly_score: float
    algorithm: str
    confidence: float
    threshold: float
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


class AnomalyDetector:
    """Sistema principal de detecção de anomalias"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.metrics = MetricsCollector()
        
        # Configurações padrão
        self.default_config = AnomalyDetectionConfig(
            algorithm=AnomalyAlgorithm.ISOLATION_FOREST,
            window_size=100,
            threshold=0.95,
            contamination=0.1,
            min_samples=10,
            retrain_interval_hours=24
        )
        
        # Estado dos modelos
        self.models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.last_training: Dict[str, datetime] = {}
        
        # Histórico de anomalias detectadas
        self.anomaly_history: List[AnomalyResult] = []
        
        # Carregar configurações customizadas
        self._load_config()
        
        # Inicializar modelos
        self._initialize_models()
        
        self.logger.info("Sistema de detecção de anomalias inicializado com sucesso")
    
    def _load_config(self):
        """Carrega configurações customizadas"""
        custom_configs = self.config.get("anomaly_detection", {})
        for metric, config_data in custom_configs.items():
            try:
                config = AnomalyDetectionConfig(**config_data)
                self.config[metric] = config
            except Exception as e:
                self.logger.error(f"Erro ao carregar configuração para {metric}: {e}")
    
    def _initialize_models(self):
        """Inicializa os modelos de ML"""
        try:
            # Tentar carregar modelos salvos
            self._load_saved_models()
        except Exception as e:
            self.logger.warning(f"Não foi possível carregar modelos salvos: {e}")
            self.logger.info("Modelos serão treinados com dados iniciais")
    
    def _load_saved_models(self):
        """Carrega modelos salvos do disco"""
        models_dir = "models"
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            return
        
        for filename in os.listdir(models_dir):
            if filename.endswith('.joblib'):
                try:
                    model_path = os.path.join(models_dir, filename)
                    model = joblib.load(model_path)
                    
                    # Extrair nome da métrica do nome do arquivo
                    metric_name = filename.replace('.joblib', '')
                    
                    self.models[metric_name] = model
                    self.logger.info(f"Modelo carregado para {metric_name}")
                    
                    # Carregar metadados
                    metadata_path = model_path.replace('.joblib', '_metadata.json')
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            self.model_metadata[metric_name] = json.load(f)
                            
                except Exception as e:
                    self.logger.error(f"Erro ao carregar modelo {filename}: {e}")
    
    def _save_model(self, metric_name: str, model: Any, metadata: Dict[str, Any]):
        """Salva modelo e metadados no disco"""
        try:
            models_dir = "models"
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
            
            # Salvar modelo
            model_path = os.path.join(models_dir, f"{metric_name}.joblib")
            joblib.dump(model, model_path)
            
            # Salvar metadados
            metadata_path = model_path.replace('.joblib', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, default=str)
                
            self.logger.info(f"Modelo salvo para {metric_name}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar modelo para {metric_name}: {e}")
    
    def detect_anomalies(self, metric_name: str, data: Union[List[float], np.ndarray, pd.Series]) -> List[AnomalyResult]:
        """Detecta anomalias em uma série de dados"""
        try:
            # Converter para numpy array
            if isinstance(data, (list, pd.Series)):
                data = np.array(data)
            
            if len(data) < self.default_config.min_samples:
                self.logger.warning(f"Dados insuficientes para {metric_name}: {len(data)} < {self.default_config.min_samples}")
                return []
            
            # Obter configuração para a métrica
            metric_config = self.config.get(metric_name, self.default_config)
            
            # Verificar se precisa treinar/retreinar o modelo
            if self._should_retrain(metric_name, metric_config):
                self._train_model(metric_name, data, metric_config)
            
            # Detectar anomalias
            if metric_name in self.models:
                results = self._detect_with_ml_model(metric_name, data, metric_config)
            else:
                # Usar métodos estatísticos simples
                results = self._detect_with_statistical_methods(metric_name, data, metric_config)
            
            # Adicionar ao histórico
            self.anomaly_history.extend(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erro ao detectar anomalias para {metric_name}: {e}")
            return []
    
    def _should_retrain(self, metric_name: str, config: AnomalyDetectionConfig) -> bool:
        """Verifica se o modelo precisa ser retreinado"""
        if metric_name not in self.models:
            return True
        
        if metric_name not in self.last_training:
            return True
        
        last_training = self.last_training[metric_name]
        retrain_interval = timedelta(hours=config.retrain_interval_hours)
        
        return datetime.now() - last_training > retrain_interval
    
    def _train_model(self, metric_name: str, data: np.ndarray, config: AnomalyDetectionConfig):
        """Treina um novo modelo para a métrica"""
        try:
            self.logger.info(f"Treinando modelo para {metric_name} com {len(data)} amostras")
            
            # Preparar dados para treinamento
            X = self._prepare_features(data, config.window_size)
            
            if len(X) < config.min_samples:
                self.logger.warning(f"Dados insuficientes para treinamento: {len(X)} < {config.min_samples}")
                return
            
            # Criar e treinar modelo
            model = self._create_model(config)
            model.fit(X)
            
            # Salvar modelo
            self.models[metric_name] = model
            self.last_training[metric_name] = datetime.now()
            
            # Salvar metadados
            metadata = {
                "algorithm": config.algorithm.value,
                "trained_at": datetime.now().isoformat(),
                "n_samples": len(X),
                "window_size": config.window_size,
                "threshold": config.threshold,
                "contamination": config.contamination
            }
            self.model_metadata[metric_name] = metadata
            
            # Salvar no disco
            self._save_model(metric_name, model, metadata)
            
            self.logger.info(f"Modelo treinado e salvo para {metric_name}")
            
        except Exception as e:
            self.logger.error(f"Erro ao treinar modelo para {metric_name}: {e}")
    
    def _create_model(self, config: AnomalyDetectionConfig) -> Any:
        """Cria um modelo baseado na configuração"""
        try:
            if config.algorithm == AnomalyAlgorithm.ISOLATION_FOREST:
                from sklearn.ensemble import IsolationForest
                return IsolationForest(
                    contamination=config.contamination,
                    random_state=42,
                    n_estimators=100
                )
            
            elif config.algorithm == AnomalyAlgorithm.LOCAL_OUTLIER_FACTOR:
                from sklearn.neighbors import LocalOutlierFactor
                return LocalOutlierFactor(
                    contamination=config.contamination,
                    novelty=True,
                    n_neighbors=20
                )
            
            elif config.algorithm == AnomalyAlgorithm.ONE_CLASS_SVM:
                from sklearn.svm import OneClassSVM
                return OneClassSVM(
                    nu=config.contamination,
                    kernel='rbf',
                    gamma='scale'
                )
            
            elif config.algorithm == AnomalyAlgorithm.ELLIPTIC_ENVELOPE:
                from sklearn.covariance import EllipticEnvelope
                return EllipticEnvelope(
                    contamination=config.contamination,
                    random_state=42
                )
            
            elif config.algorithm == AnomalyAlgorithm.DBSCAN:
                from sklearn.cluster import DBSCAN
                return DBSCAN(
                    eps=0.5,
                    min_samples=config.min_samples
                )
            
            else:
                # Fallback para Isolation Forest
                from sklearn.ensemble import IsolationForest
                return IsolationForest(
                    contamination=config.contamination,
                    random_state=42
                )
                
        except ImportError as e:
            self.logger.error(f"Erro ao importar bibliotecas de ML: {e}")
            self.logger.warning("Usando métodos estatísticos simples")
            return None
    
    def _prepare_features(self, data: np.ndarray, window_size: int) -> np.ndarray:
        """Prepara features para o modelo de ML"""
        if len(data) < window_size:
            return data.reshape(-1, 1)
        
        # Criar features baseadas em janela deslizante
        features = []
        for i in range(window_size, len(data)):
            window = data[i-window_size:i]
            feature_vector = [
                np.mean(window),      # Média
                np.std(window),       # Desvio padrão
                np.min(window),       # Mínimo
                np.max(window),       # Máximo
                np.median(window),    # Mediana
                np.percentile(window, 25),  # Q1
                np.percentile(window, 75),  # Q3
                data[i]              # Valor atual
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def _detect_with_ml_model(self, metric_name: str, data: np.ndarray, config: AnomalyDetectionConfig) -> List[AnomalyResult]:
        """Detecta anomalias usando modelo de ML treinado"""
        try:
            model = self.models[metric_name]
            X = self._prepare_features(data, config.window_size)
            
            if len(X) == 0:
                return []
            
            # Predição
            if hasattr(model, 'predict'):
                predictions = model.predict(X)
                # Converter para formato padrão (-1 para anomalia, 1 para normal)
                anomaly_scores = np.where(predictions == -1, 1.0, 0.0)
            elif hasattr(model, 'score_samples'):
                # Para modelos que retornam scores
                scores = model.score_samples(X)
                # Normalizar scores para 0-1
                anomaly_scores = 1 - (scores - scores.min()) / (scores.max() - scores.min())
            else:
                # Fallback para métodos estatísticos
                return self._detect_with_statistical_methods(metric_name, data, config)
            
            # Criar resultados
            results = []
            for i, score in enumerate(anomaly_scores):
                if score > config.threshold:
                    # Calcular índice no array original
                    idx = config.window_size + i
                    if idx < len(data):
                        result = AnomalyResult(
                            timestamp=datetime.now(),
                            metric_name=metric_name,
                            value=data[idx],
                            is_anomaly=True,
                            anomaly_score=score,
                            algorithm=config.algorithm.value,
                            confidence=score,
                            threshold=config.threshold,
                            context={
                                "window_size": config.window_size,
                                "feature_index": i
                            }
                        )
                        results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erro ao usar modelo ML para {metric_name}: {e}")
            # Fallback para métodos estatísticos
            return self._detect_with_statistical_methods(metric_name, data, config)
    
    def _detect_with_statistical_methods(self, metric_name: str, data: np.ndarray, config: AnomalyDetectionConfig) -> List[AnomalyResult]:
        """Detecta anomalias usando métodos estatísticos simples"""
        results = []
        
        try:
            if config.algorithm == AnomalyAlgorithm.Z_SCORE:
                results = self._z_score_detection(metric_name, data, config)
            elif config.algorithm == AnomalyAlgorithm.IQR:
                results = self._iqr_detection(metric_name, data, config)
            elif config.algorithm == AnomalyAlgorithm.MAHALANOBIS:
                results = self._mahalanobis_detection(metric_name, data, config)
            else:
                # Fallback para Z-score
                results = self._z_score_detection(metric_name, data, config)
                
        except Exception as e:
            self.logger.error(f"Erro em detecção estatística para {metric_name}: {e}")
        
        return results
    
    def _z_score_detection(self, metric_name: str, data: np.ndarray, config: AnomalyDetectionConfig) -> List[AnomalyResult]:
        """Detecção usando Z-score"""
        results = []
        
        if len(data) < 2:
            return results
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return results
        
        z_scores = np.abs((data - mean) / std)
        threshold = 2.5  # Z-score threshold
        
        for i, z_score in enumerate(z_scores):
            if z_score > threshold:
                result = AnomalyResult(
                    timestamp=datetime.now(),
                    metric_name=metric_name,
                    value=data[i],
                    is_anomaly=True,
                    anomaly_score=z_score / threshold,
                    algorithm="z_score",
                    confidence=min(z_score / threshold, 1.0),
                    threshold=threshold,
                    context={
                        "z_score": z_score,
                        "mean": mean,
                        "std": std
                    }
                )
                results.append(result)
        
        return results
    
    def _iqr_detection(self, metric_name: str, data: np.ndarray, config: AnomalyDetectionConfig) -> List[AnomalyResult]:
        """Detecção usando IQR (Interquartile Range)"""
        results = []
        
        if len(data) < 4:
            return results
        
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        if iqr == 0:
            return results
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                # Calcular score baseado na distância do limite
                distance = max(abs(value - lower_bound), abs(value - upper_bound))
                score = min(distance / iqr, 1.0)
                
                result = AnomalyResult(
                    timestamp=datetime.now(),
                    metric_name=metric_name,
                    value=value,
                    is_anomaly=True,
                    anomaly_score=score,
                    algorithm="iqr",
                    confidence=score,
                    threshold=1.5,
                    context={
                        "q1": q1,
                        "q3": q3,
                        "iqr": iqr,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound
                    }
                )
                results.append(result)
        
        return results
    
    def _mahalanobis_detection(self, metric_name: str, data: np.ndarray, config: AnomalyDetectionConfig) -> List[AnomalyResult]:
        """Detecção usando distância de Mahalanobis"""
        results = []
        
        if len(data) < 2:
            return results
        
        # Reshape para 2D
        X = data.reshape(-1, 1)
        
        # Calcular matriz de covariância
        try:
            cov_matrix = np.cov(X.T)
            inv_cov_matrix = np.linalg.inv(cov_matrix)
            
            # Calcular distâncias de Mahalanobis
            mean = np.mean(X, axis=0)
            mahal_distances = []
            
            for point in X:
                diff = point - mean
                distance = np.sqrt(diff.T @ inv_cov_matrix @ diff)
                mahal_distances.append(distance[0])
            
            # Threshold baseado no percentil 95
            threshold = np.percentile(mahal_distances, 95)
            
            for i, distance in enumerate(mahal_distances):
                if distance > threshold:
                    score = min(distance / threshold, 1.0)
                    
                    result = AnomalyResult(
                        timestamp=datetime.now(),
                        metric_name=metric_name,
                        value=data[i],
                        is_anomaly=True,
                        anomaly_score=score,
                        algorithm="mahalanobis",
                        confidence=score,
                        threshold=threshold,
                        context={
                            "mahalanobis_distance": distance,
                            "threshold": threshold
                        }
                    )
                    results.append(result)
                    
        except Exception as e:
            self.logger.error(f"Erro no cálculo de Mahalanobis: {e}")
        
        return results
    
    def get_anomaly_history(self, metric_name: str = None, limit: int = 100) -> List[AnomalyResult]:
        """Retorna histórico de anomalias detectadas"""
        if metric_name:
            return [a for a in self.anomaly_history if a.metric_name == metric_name][-limit:]
        return self.anomaly_history[-limit:]
    
    def get_anomaly_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das anomalias detectadas"""
        if not self.anomaly_history:
            return {}
        
        total_anomalies = len(self.anomaly_history)
        metrics_with_anomalies = set(a.metric_name for a in self.anomaly_history)
        
        # Estatísticas por algoritmo
        algorithm_counts = {}
        for result in self.anomaly_history:
            algo = result.algorithm
            algorithm_counts[algo] = algorithm_counts.get(algo, 0) + 1
        
        # Estatísticas por métrica
        metric_counts = {}
        for result in self.anomaly_history:
            metric = result.metric_name
            metric_counts[metric] = metric_counts.get(metric, 0) + 1
        
        return {
            "total_anomalies": total_anomalies,
            "metrics_with_anomalies": len(metrics_with_anomalies),
            "algorithm_distribution": algorithm_counts,
            "metric_distribution": metric_counts,
            "last_anomaly": self.anomaly_history[-1].timestamp if self.anomaly_history else None,
            "models_trained": len(self.models)
        }
    
    def cleanup_old_anomalies(self, days: int = 30):
        """Remove anomalias antigas do histórico"""
        cutoff_date = datetime.now() - timedelta(days=days)
        self.anomaly_history = [
            anomaly for anomaly in self.anomaly_history 
            if anomaly.timestamp > cutoff_date
        ]
        self.logger.info(f"Histórico de anomalias limpo (mantidos últimos {days} dias)")


# Função de conveniência para criar instância padrão
def create_anomaly_detector(config: Dict[str, Any] = None) -> AnomalyDetector:
    """Cria uma instância padrão do detector de anomalias"""
    if config is None:
        config = {
            "anomaly_detection": {
                "system.cpu_percent": {
                    "algorithm": "isolation_forest",
                    "window_size": 50,
                    "threshold": 0.9,
                    "contamination": 0.05
                },
                "system.memory_percent": {
                    "algorithm": "local_outlier_factor",
                    "window_size": 100,
                    "threshold": 0.95,
                    "contamination": 0.1
                }
            }
        }
    
    return AnomalyDetector(config)


if __name__ == "__main__":
    # Teste do sistema de detecção de anomalias
    detector = create_anomaly_detector()
    
    # Simular dados
    np.random.seed(42)
    normal_data = np.random.normal(50, 10, 100)
    anomaly_data = np.concatenate([normal_data, [100, 0, 150]])  # Adicionar anomalias
    
    print("Sistema de detecção de anomalias inicializado!")
    print(f"Algoritmos disponíveis: {[algo.value for algo in AnomalyAlgorithm]}")
    
    # Detectar anomalias
    results = detector.detect_anomalies("test_metric", anomaly_data)
    print(f"Anomalias detectadas: {len(results)}")
    
    # Estatísticas
    stats = detector.get_anomaly_stats()
    print(f"Estatísticas: {stats}")
