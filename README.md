🏥 SmartHealth - Clinical Query System with RAG


Este proyecto es un backend desarrollado en FastAPI para la consulta inteligente de información clínica de pacientes utilizando el patrón RAG (Retrieval-Augmented Generation). Utiliza PostgreSQL con pgvector como base de datos y está diseñado con una arquitectura modular que facilita la escalabilidad y el mantenimiento.
Las contribuciones y los comentarios siempre son bienvenidos. ¡Explora y descubre la magia en el directorio /src! ⚡



Objetivo Funcional
El usuario autenticado puede enviar:

document_type_id (tipo de documento)
document_number (número de documento)
question (pregunta sobre el paciente)

El sistema responde con información clínica relevante generada por IA basada exclusivamente en datos de la base de datos.

📁 Estructura del Proyecto

Propósito: Centraliza toda la documentación relevante del proyecto.
Contenido:

README.md: Documentación general del proyecto.
API_Documentation.md: Detalles de los endpoints desarrollados con FastAPI.
Database_Diagram.png: Diagrama de la base de datos utilizada.

📂 src/app/
Propósito: Contiene el código fuente principal del proyecto.
Subcarpetas:

database/: Configuración de la conexión a PostgreSQL con pgvector.



models/: Definición de los modelos SQLAlchemy.


routers/: Contiene los endpoints para las APIs.


schemas/: Esquemas de Pydantic para validación y serialización.


services/: Lógica de negocio y acceso a la base de datos.




Archivo Principal:

main.py: Punto de entrada de la aplicación FastAPI.


database/: Scripts SQL para inicializar o gestionar la base de datos.

init_db.sql: Inicialización de esquemas y tablas.
seed_data.sql: Carga de datos de prueba.
generate_embeddings.py: Generación de embeddings para pgvector.




🔧 Requisitos Previos
Asegúrate de tener instalados los siguientes componentes antes de comenzar:

Python 3.9+ 🐍
PostgreSQL 14+ con extensión pgvector 🗄️
Git 📦


📥 Instalación
Sigue los pasos a continuación para configurar y ejecutar el proyecto:
1. Clonar el Repositorio
bashgit clone https://github.com/tu-usuario/smarthealth.git
cd smarthealth
2. Crear Entorno Virtual
bashpython -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
3. Instalar Dependencias
bashpip install -r requirements.txt


⚙️ Configuración
1. Variables de Entorno
Crea un archivo .env en la raíz del proyecto con la siguiente configuración (ajusta los valores según tu entorno):
env# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthealth
DB_USER=postgres
DB_PASSWORD=tu_password
APP_ENV=development
SECRET_KEY=tu_clave_secreta_muy_segura
ALGORITHM=HS256


🚀 Ejecución
Ejecutar en modo desarrollo:
En un puerto específico (ejemplo: 8088):
bashuvicorn app.main:app --reload --port 8088
En el puerto por defecto (8000):
bashuvicorn app.main:app --reload
La aplicación estará disponible en:

API: http://localhost:8088
Documentación Swagger: http://localhost:8088/docs
Documentación ReDoc: http://localhost:8088/redoc