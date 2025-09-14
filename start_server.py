#!/usr/bin/env python3
"""
Script para iniciar o servidor de desenvolvimento do Mail Execute
"""
import uvicorn
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para imports relativos
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("🚀 Iniciando servidor de desenvolvimento...")
    print("📧 Mail Execute - Sistema de Classificação de Emails")
    print("-" * 50)

    try:
        uvicorn.run(
            "backend.app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️  Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")