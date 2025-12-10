# Backend - SmartHealth API

Este directorio contiene todo el código del backend del proyecto SmartHealth.

## 📁 Estructura

```
backend/
├── src/                    # Código fuente del backend
│   └── app/               # Aplicación FastAPI
│       ├── main.py        # Punto de entrada de la aplicación
│       ├── core/          # Configuración y seguridad
│       ├── database/      # Configuración de base de datos
│       ├── models/        # Modelos SQLAlchemy
│       ├── routers/       # Endpoints de la API
│       ├── schemas/       # Esquemas Pydantic
│       └── services/      # Lógica de negocio
├── start_server.py        # Script para iniciar el servidor
├── requirements.txt       # Dependencias de Python
├── test_db_connection.py  # Test de conexión a BD
├── test_llm_real.py       # Test de LLM
├── test_security.py       # Test de seguridad
├── diagnostico_completo.py # Script de diagnóstico
├── remove_emojis.py       # Utilidad
├── database_setup.md      # Documentación de configuración de BD
└── security.md            # Documentación de seguridad
```

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
# Desde la raíz del proyecto
cd backend
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env` en la **raíz del proyecto** (no en backend/):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthdb
DB_USER=sm_admin
DB_PASSWORD=tu_contraseña
SECRET_KEY=tu_secret_key
APP_ENV=development
OPENAI_API_KEY=tu_api_key
```

### 3. Iniciar el servidor

```bash
# Desde backend/
python start_server.py
```

El servidor estará disponible en:
- API: http://127.0.0.1:8000
- Frontend: http://localhost:8000/chat
- Docs: http://localhost:8000/docs

## 📝 Notas

- El archivo `.env` debe estar en la **raíz del proyecto**, no en `backend/`
- El frontend se encuentra en `../frontend/` (relativo a backend/)
- El servidor sirve automáticamente los archivos estáticos del frontend

## 🔧 Desarrollo

Para desarrollo con auto-reload:

```bash
cd backend
uvicorn src.app.main:app --reload --port 8000
```

## 📚 Documentación

- Ver `database_setup.md` para configuración de la base de datos
- Ver `security.md` para información de seguridad
- Ver el README principal del proyecto para documentación completa

