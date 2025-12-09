# ==========================================
# Imagen base para producción en Render
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements PRIMERO (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY ./src /app/src

# IMPORTANTE: NO copiar .env al contenedor
# Render manejará las variables de entorno

# Exponer puerto (Render usa la variable PORT)
EXPOSE 8088

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8088/health || exit 1

# Comando para ejecutar
# Render usa la variable $PORT, así que haremos que sea flexible
CMD uvicorn src.app.main:app --host 0.0.0.0 --port ${PORT:-8088}