#!/usr/bin/env python3
"""
Script para executar a API REST do CloudDataOrchestrator v2.0
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Função principal para executar a API"""
    
    # Configurar variáveis de ambiente
    os.environ.setdefault("API_TOKEN", "clouddataorchestrator-api-key")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    # Configurações da API
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    workers = int(os.getenv("API_WORKERS", "1"))
    
    print("🚀 Iniciando CloudDataOrchestrator API v2.0")
    print(f"📡 Host: {host}")
    print(f"🔌 Porta: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"👥 Workers: {workers}")
    print(f"🔑 Token: {os.getenv('API_TOKEN')}")
    print("=" * 50)
    
    # Executar API
    try:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
            access_log=True,
            use_colors=True
        )
    except KeyboardInterrupt:
        print("\n🛑 API interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
