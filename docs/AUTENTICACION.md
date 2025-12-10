# Sistema de Autenticación - SmartHealth

## 📋 Resumen del Flujo

El sistema utiliza **JWT (JSON Web Tokens)** para autenticación. Los usuarios se registran y sus datos se guardan en la base de datos PostgreSQL.

---

## 🔐 1. REGISTRO DE USUARIOS

### ¿Dónde se guardan los datos?
**Sí, los datos se guardan en la base de datos PostgreSQL.**

- **Tabla**: `smart_health.users`
- **Schema**: `smart_health`
- **Ubicación**: Base de datos PostgreSQL configurada en `db_config.py`

### Proceso de Registro:

1. **Frontend** → `POST /auth/register`
   ```json
   {
     "email": "usuario@ejemplo.com",
     "first_name": "Juan",
     "middle_name": "Carlos",
     "first_surname": "Pérez",
     "second_surname": "González",
     "password": "password123"
   }
   ```

2. **Backend** (`auth_service.py`):
   - Valida que la contraseña tenga al menos 6 caracteres
   - Verifica que el email no exista ya
   - **Hashea la contraseña** con bcrypt (NUNCA se guarda en texto plano)
   - Crea el usuario en la base de datos
   - Retorna los datos del usuario (sin contraseña)

3. **Base de Datos**:
   ```sql
   INSERT INTO smart_health.users (
     first_name, middle_name, first_surname, second_surname,
     email, password_hash, is_active, created_at, updated_at
   ) VALUES (...)
   ```

### Campos guardados:
- `user_id` (auto-incremental)
- `first_name`, `middle_name`, `first_surname`, `second_surname`
- `email` (único, indexado)
- `password_hash` (hash bcrypt, NO texto plano)
- `is_active` (boolean, default: true)
- `created_at`, `updated_at` (timestamps automáticos)

---

## 🔑 2. GENERACIÓN DEL JWT

### ¿Cómo se genera el JWT?

**Ubicación**: `src/app/core/security.py` → `create_access_token()`

### Proceso:

1. **Login** → `POST /auth/login`
   ```json
   {
     "email": "usuario@ejemplo.com",
     "password": "password123"
   }
   ```

2. **Autenticación** (`auth_service.py`):
   - Busca el usuario por email en la BD
   - Verifica la contraseña usando `verify_password()` (compara con bcrypt)
   - Verifica que el usuario esté activo (`is_active = true`)

3. **Generación del Token**:
   ```python
   token_data = {"sub": str(user.user_id)}  # "sub" = subject (estándar JWT)
   access_token = create_access_token(token_data)
   ```

4. **Contenido del JWT**:
   ```json
   {
     "sub": "123",           // user_id del usuario
     "exp": 1234567890       // timestamp de expiración (30 minutos)
   }
   ```

5. **Firma del Token**:
   - Algoritmo: `HS256`
   - Secret Key: Desde `settings.secret_key` (variable de entorno)
   - Expiración: 30 minutos por defecto

6. **Respuesta al Frontend**:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer"
   }
   ```

---

## 🛡️ 3. AUTENTICACIÓN EN PETICIONES

### ¿Cómo se autentica cada petición?

**Ubicación**: `src/app/core/security.py` → `get_current_user()`

### Proceso:

1. **Frontend envía petición** con header:
   ```
   Authorization: Bearer <token>
   ```

2. **Backend valida el token**:
   - Extrae el token del header `Authorization`
   - Decodifica el JWT usando `decode_access_token()`
   - Verifica la firma con `SECRET_KEY`
   - Verifica que no haya expirado (`exp`)
   - Extrae el `user_id` del campo `sub`

3. **Busca el usuario en la BD**:
   ```python
   user = db.query(User).filter(User.user_id == int(user_id)).first()
   ```

4. **Verifica que el usuario esté activo**:
   ```python
   if not user.is_active:
       raise HTTPException(403, "Usuario inactivo")
   ```

5. **Retorna el usuario** para usar en el endpoint

### Endpoints que requieren autenticación:

- `GET /user/me` - Obtener perfil actual
- `GET /user/{user_id}` - Obtener usuario específico
- `PUT /user/{user_id}` - Actualizar usuario
- `POST /query/` - Consultas RAG (requiere `user_id` en el body)
- `WebSocket /ws/chat` - Chat en tiempo real (token en query param)

---

## 📊 4. ESTRUCTURA DE LA BASE DE DATOS

### Tabla `users`:

```sql
CREATE TABLE smart_health.users (
    user_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    first_surname VARCHAR(50) NOT NULL,
    second_surname VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Hash bcrypt
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Seguridad:

- ✅ Contraseñas hasheadas con **bcrypt** (no se guardan en texto plano)
- ✅ JWT firmado con `SECRET_KEY` (debe tener al menos 32 caracteres)
- ✅ Tokens expiran en 30 minutos
- ✅ Verificación de usuario activo en cada petición
- ✅ Email único (índice único en la BD)

---

## 🔄 5. FLUJO COMPLETO

### Registro:
```
Usuario → Frontend (/register) 
       → POST /auth/register
       → AuthService.register_user()
       → Hash password (bcrypt)
       → INSERT INTO users
       → Retorna UserResponse (sin password)
```

### Login:
```
Usuario → Frontend (/login)
       → POST /auth/login
       → AuthService.authenticate_user() (verifica email + password)
       → AuthService.login() (genera JWT)
       → create_access_token({"sub": user_id})
       → Retorna {access_token, token_type}
       → Frontend guarda token en localStorage
```

### Petición Autenticada:
```
Frontend → API Request
         → Header: Authorization: Bearer <token>
         → get_current_user() (dependency)
         → decode_access_token()
         → Busca usuario en BD por user_id
         → Retorna User object
         → Endpoint usa el usuario
```

---

## 🔍 6. VERIFICACIÓN EN EL FRONTEND

### Almacenamiento:
- **Token**: `localStorage.getItem('jwt_token')`
- **Usuario**: `localStorage.getItem('user_data')`

### Uso:
```javascript
// En cada petición API
const token = Auth.getToken();
headers['Authorization'] = `Bearer ${token}`;
```

### Verificación:
```javascript
// Verificar si está autenticado
if (!Auth.isAuthenticated()) {
    window.location.href = '/login';
}
```

---

## ⚠️ 7. IMPORTANTE

1. **Las contraseñas NUNCA se guardan en texto plano** - Solo el hash bcrypt
2. **El JWT contiene solo el `user_id`** - No contiene datos sensibles
3. **Cada petición valida el token y busca el usuario en la BD** - No se confía solo en el token
4. **Los tokens expiran en 30 minutos** - El usuario debe hacer login nuevamente
5. **Los usuarios inactivos no pueden autenticarse** - `is_active = false` bloquea el acceso

---

## 📝 8. CONFIGURACIÓN

### Variables de Entorno Necesarias:

```env
SECRET_KEY=tu_clave_secreta_de_al_menos_32_caracteres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smart_health
DB_USER=postgres
DB_PASSWORD=tu_password
```

### Secret Key:
- Debe tener al menos 32 caracteres
- Se usa para firmar y verificar JWT
- **NUNCA** debe estar en el código fuente
- Debe ser diferente en desarrollo y producción

---

## ✅ Resumen

- ✅ **Sí, los usuarios se guardan en PostgreSQL** (tabla `smart_health.users`)
- ✅ **Sí, se usa JWT para autenticación** (generado con `create_access_token()`)
- ✅ **Sí, cada petición valida el token** (usando `get_current_user()`)
- ✅ **Sí, las contraseñas están hasheadas** (bcrypt, nunca texto plano)
- ✅ **Sí, el token contiene el `user_id`** (en el campo `sub`)

