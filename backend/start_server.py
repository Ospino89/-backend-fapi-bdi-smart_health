#!/usr/bin/env python3
"""
Script para iniciar el servidor FastAPI con Uvicorn
"""
import sys
import os
import subprocess

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("=" * 60)
    print("Iniciando servidor FastAPI/Uvicorn...")
    print("=" * 60)
    print(f"Python: {sys.executable}")
    print(f"Directorio: {os.getcwd()}")
    print("=" * 60)
    print()
    
    try:
        # Intentar importar uvicorn
        import uvicorn
        print("✓ Uvicorn encontrado")
    except ImportError:
        print("✗ Uvicorn no encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn[standard]"])
        import uvicorn
    
    try:
        # Intentar importar la app
        from app.main import app
        print("✓ Aplicación FastAPI cargada correctamente")
        print()
        print("Iniciando servidor en http://127.0.0.1:8000")
        print("Frontend disponible en: http://localhost:8000/chat")
        print("API Docs disponible en: http://localhost:8000/docs")
        print()
        print("Presiona Ctrl+C para detener el servidor")
        print("=" * 60)
        print()
        
        # Iniciar servidor
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"✗ Error al cargar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

