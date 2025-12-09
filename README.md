# BACKEND-FAPI-BDI-SMART_HEALTH
# 🏥 SmartHealth - Clinical Query System with RAG

**Desarrolladores**: Ivan Ospino , Gisell Anaya , Jhoan Smith , Jeison Mendez 

**Creado**: 22-Noviembre-2025

## Descripción   
Este proyecto es un backend desarrollado en FastAPI para la consulta inteligente de información clínica de pacientes utilizando el patrón RAG (Retrieval-Augmented Generation). Utiliza PostgreSQL con pgvector como base de datos y está diseñado con una arquitectura modular que facilita la escalabilidad y el mantenimiento.

Las contribuciones y los comentarios siempre son bienvenidos. ¡Explora y descubre la magia en el directorio /src! ⚡

---

## Estructura del Proyecto

**Contenido**:

- `README.md`: Documentación general del proyecto.
- `Dockerfile`: Configuración de Docker para construir la imagen de producción.
- `docker-compose.yml`: Orquestación de servicios para desarrollo.
- `requirements.txt`: Lista de dependencias de Python.

---

### [src/app/](./src/app/)
**Propósito**: Contiene el código fuente principal del proyecto.

**Subcarpetas**:
- **[database/](./src/app/database/):**  
  - `database.py`: Configuración de la conexión a PostgreSQL con pgvector.

- **[models/](./src/app/models/):**  
  Definición de los modelos SQLAlchemy.

  - `user.py`: Modelo para la entidad "usuario".  
  - `patient.py`: Modelo para la entidad "paciente".
  - `appointment.py`: Modelo para la entidad "citas médicas".
  - `diagnosis.py`:Modelo para la entidad "diagnósticos".
  - `prescription.py`: Modelo para la entidad "prescripciones médicas".
  - `medical_record.py`: Modelo para la entidad "registros médicos".
  - `record_diagnosis.py`: Modelo de relación muchos-a-muchos entre registros médicos y diagnósticos.


- **[routers/](./src/app/routers/):**  
  Contiene los endpoints para las APIs. 
  - `user.py`: API para gestionar el usuario.  
  - `auth.py`: API para gestionar el  registro y login.
  - `query.py`: API para realizar consultas inteligentes usando RAG (Retrieval-Augmented Generation).


- **[schemas/](./src/app/schemas/):**  
  Esquemas de Pydantic para validación y serialización de datos.  
  - `user.py`: Esquema para la entidad "usuario".  
  - `rag.py`: Esquemas para las consultas RAG (QueryRequest, QueryResponse).
  - `clinical.py`: Esquemas para validación de datos clínicos (pacientes, citas, registros médicos).
  - `llm_schemas.py`: Esquemas para las peticiones y respuestas del servicio LLM.

 

- **[services/](./src/app/services/):**  
  Lógica de negocio y acceso a la base de datos.  
  - `user_service.py`: Servicios relacionados con usuario.  
  - `auth_service.py`: Servicios relacionados con el registro y login.
  - `clinical_service.py`: Servicios para gestionar información clínica de pacientes.
  - `llm_client.py`: Cliente para interactuar con la API de OpenAI.
  - `llm_service.py`: Servicios que utilizan el LLM para generar respuestas inteligentes.
  - `rag_context.py`: Construcción del contexto para consultas RAG (prepara información relevante).
  - `rag_service.py`: Orquestación del flujo RAG (búsqueda + generación de respuesta).
  - `vector_search.py`: Servicios de búsqueda vectorial usando pgvector para similitud semántica.

- **[core/](./src/app/core/):**
  Logica de la seguridad 
  - `security.py`: Logica de la seguridad de la API    

**Archivo Principal**:
- `main.py`: Punto de entrada de la aplicación.

---

## Requisitos

- **Python 3.9+**
- **PostgreSQL 16 con extensión pgvector**
- **Docker**
- **Cuenta de OpenAI**
---

## Instalación

Sigue los pasos a continuación para configurar y ejecutar el proyecto:

### 1. Clonar el Repositorio

```bash
git clone git@github.com:Ospino89/-backend-fapi-bdi-smart_health.git
```

### 2. Crear un Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  
```

### 3. Instalar las Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar las Variables de Entorno 

Crea un archivo `.env` en la raíz del proyecto con la siguiente configuración (ajusta los valores según tu entorno):

 ```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthdb
DB_USER=sm_admin
DB_PASSWORD=tu_password
APP_ENV=development
SECRET_KEY=tu_clave_secreta_muy_segura


# OpenAI
OPENAI_API_KEY=sk-tu-api-key-de-openai

# Configuración LLM
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500
LLM_TIMEOUT=30

```

### 5. Inicializar la Base de Datos

Asegúrate de que tu base de datos exista, y esté corriendo en el puerto predispuesto para correr, `postgresql` por defecto corre en el puerto 5432

### 6. Correr el proyecto de FastAPI

Utilizar el siguiente comando, para correr en un puerto especifico en el directorio src

```bash
uvicorn app.main:app --reload --port 8088
```

Si quieren correr en el puerto por default, utilizar este comando

```bash
uvicorn app.main:app --reload
```

### 7. accerde a el proyecto de FastAPI

API: http://127.0.0.1:8000

Documentación Swagger: http://127.0.0.1:8000/docs

URL de Producción: https://smarthealth-api-926g.onrender.com/docs

