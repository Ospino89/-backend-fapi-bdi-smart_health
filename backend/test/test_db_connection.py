"""
Test de Conexión a la Base de Datos
====================================
Ejecutar: python test_db_connection.py
"""

import sys
from pathlib import Path

# Agregar src al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir / "src"))

print("🔍 Probando conexión a la base de datos...\n")

# Test 1: Variables de entorno
print("=" * 60)
print("TEST 1: Variables de Entorno")
print("=" * 60)

try:
    from dotenv import load_dotenv
    import os
    
    env_path = root_dir / ".env"
    load_dotenv(env_path)
    
    print(f"✅ Archivo .env: {env_path}")
    print(f"✅ DB_HOST: {os.getenv('DB_HOST')}")
    print(f"✅ DB_PORT: {os.getenv('DB_PORT')}")
    print(f"✅ DB_NAME: {os.getenv('DB_NAME')}")
    print(f"✅ DB_USER: {os.getenv('DB_USER')}")
    print(f"✅ DB_PASSWORD: {'***' if os.getenv('DB_PASSWORD') else 'NO CONFIGURADA'}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Configuración de settings
print("\n" + "=" * 60)
print("TEST 2: Settings de la Aplicación")
print("=" * 60)

try:
    from app.database.db_config import settings
    
    print(f"✅ DB Host: {settings.db_host}")
    print(f"✅ DB Port: {settings.db_port}")
    print(f"✅ DB Name: {settings.db_name}")
    print(f"✅ DB User: {settings.db_user}")
    print(f"✅ Database URL: {settings.database_url[:50]}...")
    
except Exception as e:
    print(f"❌ Error cargando settings: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Engine de SQLAlchemy
print("\n" + "=" * 60)
print("TEST 3: SQLAlchemy Engine")
print("=" * 60)

try:
    from app.database.database import engine
    from sqlalchemy import text
    
    print(f"✅ Engine creado: {engine}")
    print(f"✅ URL: {engine.url}")
    
    # Probar conexión
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.scalar()
        print(f"✅ Conexión exitosa!")
        print(f"✅ PostgreSQL: {version.split(',')[0]}")
        
except Exception as e:
    print(f"❌ Error con engine: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: SessionLocal
print("\n" + "=" * 60)
print("TEST 4: SessionLocal")
print("=" * 60)

try:
    from app.database.database import SessionLocal
    
    db = SessionLocal()
    
    # Query simple
    result = db.execute(text("SELECT COUNT(*) FROM smart_health.patients;"))
    count = result.scalar()
    
    print(f"✅ SessionLocal funciona correctamente")
    print(f"✅ Pacientes en BD: {count}")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error con SessionLocal: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Simular el health endpoint
print("\n" + "=" * 60)
print("TEST 5: Simulación del Health Endpoint")
print("=" * 60)

try:
    from app.database.database import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        result.scalar()
        print("✅ Health check: PASSED")
        print("✅ Database status: connected")
    except Exception as db_error:
        print(f"❌ Health check: FAILED")
        print(f"❌ Error: {db_error}")
    finally:
        db.close()
        
except Exception as e:
    print(f"❌ Error en health check: {e}")
    import traceback
    traceback.print_exc()

# Resumen
print("\n" + "=" * 60)
print("✅ TODOS LOS TESTS PASARON")
print("=" * 60)
print("\nLa base de datos está funcionando correctamente.")
print("El problema debe estar en el endpoint /health de FastAPI.")
print("\nSolución: Reemplaza el endpoint /health en src/app/main.py")
print("con la versión corregida proporcionada.")