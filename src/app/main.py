from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, user
from .database.database import Base, engine

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear aplicación
app = FastAPI(
    title="SmartHealth API",
    description="API REST para sistema de gestión de salud",
    version="1.0.0"
)

# Configurar CORS para producción
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://tu-frontend.vercel.app",  # Añade tu dominio de frontend
    "*"  # En producción, especifica dominios exactos
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(user.router)

# Endpoint raíz
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "¡API SmartHealth funcionando en Render!",
        "docs": "/docs",
        "status": "healthy"
    }

# Health check
@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "environment": "production"}