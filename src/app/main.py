from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.routers import auth, user, query
from app.database.database import Base, engine

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear aplicación
app = FastAPI(
    title="SmartHealth API - Sprint 1",
    description="API REST para sistema de gestión de salud",
    version="1.0.0",
)

# -------------------------------
# Manejo centralizado de errores
# -------------------------------

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": str(request.url),
            },
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "DB_ERROR",
                "message": "Error de base de datos",
                "details": str(exc),
            },
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": "Ha ocurrido un error inesperado",
                "details": str(exc),
            },
        },
    )

# Configurar CORS (permitir peticiones desde frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(query.router)

# Endpoint raíz
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "¡API SmartHealth funcionando correctamente!",
        "docs": "/docs",
    }

# Health check
@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
