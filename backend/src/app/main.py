# src/app/main.py

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
import os
from pathlib import Path

from .routers import auth, user, query, websocket_chat, history , catalog 
from .database.database import Base, engine
from .database.db_config import settings

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear tablas en la base de datos
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas de base de datos creadas exitosamente")
except Exception as e:
    logger.error(f"Error creando tablas: {str(e)}")
    raise

# ============================================================
# CREAR APLICACIÓN
# ============================================================
app = FastAPI(
    title="SmartHealth API",
    description="API REST y WebSocket para sistema de gestión de salud con RAG",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True
    }
)

# ============================================================
# MIDDLEWARES
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if settings.app_env == "production":
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} Time: {process_time:.3f}s Path: {request.url.path}")
    return response

# ============================================================
# EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Error de validación en los datos enviados",
                "details": exc.errors()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    if settings.app_env == "development":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": str(exc),
                    "type": type(exc).__name__
                }
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Error interno del servidor"
            }
        }
    )

# ============================================================
# ROUTERS DE LA API
# ============================================================

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(query.router)
app.include_router(websocket_chat.router)
app.include_router(history.router)
app.include_router(catalog.router)

# ============================================================
# DETECTAR Y CONFIGURAR FRONTEND
# ============================================================

# Variable global para saber si el frontend está montado
FRONTEND_MOUNTED = False

# Detectar la ruta del frontend
FRONTEND_DIR_ENV = os.getenv("FRONTEND_DIR")
if FRONTEND_DIR_ENV:
    FRONTEND_DIR = Path(FRONTEND_DIR_ENV)
    logger.info(f"🔧 Usando FRONTEND_DIR desde variable de entorno: {FRONTEND_DIR}")
else:
    # Ruta por defecto en el contenedor Docker
    FRONTEND_DIR = Path("/app/frontend")
    logger.info(f"🔧 Usando ruta por defecto: {FRONTEND_DIR}")

# Logs de diagnóstico
logger.info("=" * 60)
logger.info(" DIAGNÓSTICO DE RUTAS DEL FRONTEND")
logger.info(f" FRONTEND_DIR: {FRONTEND_DIR}")
logger.info(f" Frontend existe: {FRONTEND_DIR.exists()}")

if FRONTEND_DIR.exists():
    try:
        contenido = [item.name for item in FRONTEND_DIR.iterdir()]
        logger.info(f" Contenido: {contenido}")
    except Exception as e:
        logger.error(f" Error listando contenido: {e}")
else:
    logger.error(f" Frontend NO encontrado en: {FRONTEND_DIR}")

logger.info("=" * 60)

# ============================================================
# MONTAR ARCHIVOS ESTÁTICOS Y FRONTEND
# ============================================================

if FRONTEND_DIR.exists():
    static_dir = FRONTEND_DIR / "static"
    public_dir = FRONTEND_DIR / "public"
    
    # Montar archivos estáticos
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f" Archivos estáticos montados: {static_dir}")
    else:
        logger.warning(f"  Carpeta static no encontrada: {static_dir}")
    
    # Verificar carpeta public
    if public_dir.exists():
        logger.info(f" Carpeta public encontrada: {public_dir}")
        FRONTEND_MOUNTED = True
        
        # Listar archivos HTML
        try:
            html_files = list(public_dir.glob("*.html"))
            logger.info(f" Archivos HTML encontrados: {[f.name for f in html_files]}")
        except Exception as e:
            logger.error(f" Error listando archivos HTML: {e}")
    else:
        logger.warning(f"  Carpeta public no encontrada: {public_dir}")
else:
    logger.warning(f"  Frontend no encontrado en: {FRONTEND_DIR}")

# ============================================================
# ENDPOINTS DEL FRONTEND (solo si existe)
# ============================================================

if FRONTEND_MOUNTED:
    public_dir = FRONTEND_DIR / "public"
    
    @app.get("/", tags=["Frontend"], include_in_schema=False)
    @app.head("/", include_in_schema=False)
    async def root():
        """Redirige a la página de login"""
        return RedirectResponse(url="/login", status_code=302)
    
    @app.get("/login", tags=["Frontend"])
    async def serve_login():
        """Sirve la página de login"""
        login_path = public_dir / "login.html"
        if login_path.exists():
            logger.info(f" Sirviendo login desde: {login_path}")
            return FileResponse(str(login_path))
        logger.error(f" Login no encontrado en: {login_path}")
        raise StarletteHTTPException(status_code=404, detail="Página de login no encontrada")
    
    @app.get("/chat", tags=["Frontend"])
    async def serve_chat():
        """Sirve la aplicación de chat"""
        index_path = public_dir / "index.html"
        if index_path.exists():
            logger.info(f" Sirviendo chat desde: {index_path}")
            return FileResponse(str(index_path))
        logger.error(f" Chat no encontrado en: {index_path}")
        raise StarletteHTTPException(status_code=404, detail="Frontend no encontrado")
    
    @app.get("/register", tags=["Frontend"])
    async def serve_register():
        """Sirve la página de registro"""
        register_path = public_dir / "register.html"
        if register_path.exists():
            return FileResponse(str(register_path))
        raise StarletteHTTPException(status_code=404, detail="Página de registro no encontrada")
    
    @app.get("/unauthorized", tags=["Frontend"])
    async def serve_unauthorized():
        """Sirve la página de no autorizado"""
        unauthorized_path = public_dir / "unauthorized.html"
        if unauthorized_path.exists():
            return FileResponse(str(unauthorized_path))
        raise StarletteHTTPException(status_code=404, detail="Página no encontrada")
    
    logger.info(" Endpoints del frontend registrados correctamente")

else:
    # Si no hay frontend, endpoint raíz muestra info de la API
    @app.get("/", tags=["API Info"])
    @app.head("/")
    def root():
        """Información de la API"""
        return {
            "message": "API SmartHealth funcionando correctamente",
            "version": "2.0.0",
            "environment": settings.app_env,
            "frontend": "No disponible - Solo API REST",
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "api_info": "/api"
            }
        }
    
    logger.warning("  Frontend no disponible - Solo se expone la API REST")

# ============================================================
# ENDPOINTS DE LA API (siempre disponibles)
# ============================================================

@app.get("/api", tags=["API Info"])
@app.head("/api")
def api_info():
    """Información detallada de la API"""
    return {
        "message": "API SmartHealth funcionando correctamente",
        "version": "2.0.0",
        "environment": settings.app_env,
        "features": {
            "rest_api": True,
            "websocket": True,
            "rag_enabled": True,
            "streaming": True,
            "authentication": True,
            "frontend": FRONTEND_MOUNTED
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "api_info": "/api",
            "health": "/health",
            "websocket": f"wss://backend-fapi-bdi-smart-health-1.onrender.com/ws/chat" if settings.app_env == "production" else "ws://localhost:8000/ws/chat"
        }
    }

@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint"""
    db_status = "disconnected"
    error_details = None
    
    try:
        from .database.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1"))
            result.scalar()
            db_status = "connected"
        except Exception as db_error:
            db_status = "disconnected"
            error_details = str(db_error)
            logger.error(f"Database health check failed: {db_error}")
        finally:
            db.close()
    except Exception as e:
        db_status = "error"
        error_details = str(e)
        logger.error(f"Database health check error: {e}")
    
    is_healthy = db_status == "connected"
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": time.time(),
        "environment": settings.app_env,
        "frontend_mounted": FRONTEND_MOUNTED,
        "frontend_path": str(FRONTEND_DIR),
        "services": {
            "database": db_status,
            "llm": "ready",
            "vector_search": "ready",
            "websocket": "enabled"
        }
    }
    
    if not is_healthy and settings.app_env == "development" and error_details:
        response["error"] = error_details
    
    return response

# ============================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info(" SmartHealth API iniciando")
    logger.info(f" Entorno: {settings.app_env}")
    logger.info(f" Modelo LLM: {settings.llm_model}")
    logger.info(f" Base de datos: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info(f" Frontend: {' Disponible' if FRONTEND_MOUNTED else ' No disponible'}")
    logger.info(f" Frontend path: {FRONTEND_DIR}")
    logger.info(f" Documentación disponible en: /docs y /redoc")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(" SmartHealth API cerrando")