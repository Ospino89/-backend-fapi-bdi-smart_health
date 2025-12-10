# ==========================================
# Imagen base para producción en Render
# ==========================================
FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ==========================================
# Stage 1: Instalar dependencias
# ==========================================
FROM base as dependencies

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# Stage 2: Imagen final
# ==========================================
FROM base as final

# Copiar dependencias instaladas
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Instalar curl y libpq5 para healthcheck y PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN groupadd -r appuser && \
    useradd -r -g appuser appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Copiar código backend
COPY --chown=appuser:appuser ./backend/src /app/src

#  COPIAR FRONTEND (CLAVE PARA ESTA OPCIÓN)
COPY --chown=appuser:appuser ./frontend /app/frontend

# Variables de entorno
ENV PYTHONPATH=/app

# Cambiar a usuario no-root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# Exponer puerto
EXPOSE ${PORT:-10000}

# Comando con Gunicorn + Uvicorn workers
CMD gunicorn src.app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-10000} \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    --log-level info