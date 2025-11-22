from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from ..database.database import get_db
from ..core.security import verify_password, hash_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ============================================================
# REGISTER - Registrar nuevo usuario
# ============================================================
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema.
    
    - **first_name**: Primer nombre (requerido)
    - **middle_name**: Segundo nombre (opcional)
    - **first_surname**: Primer apellido (requerido)
    - **second_surname**: Segundo apellido (opcional)
    - **email**: Correo electrónico único (requerido)
    - **password**: Contraseña (requerido, mínimo 6 caracteres)
    """
    
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    # Validar longitud de contraseña (opcional pero recomendado)
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 6 caracteres"
        )

    # Hashear la contraseña
    hashed_pw = hash_password(user_data.password)

    # Crear nuevo usuario
    new_user = User(
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        first_surname=user_data.first_surname,
        second_surname=user_data.second_surname,
        email=user_data.email,
        password_hash=hashed_pw
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el usuario: {str(e)}"
        )

    return new_user




#=============================================================
# LOGIN - Iniciar sesión
# ============================================================
@router.post("/login", response_model=TokenResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Inicia sesión y devuelve un token de acceso.
    
    - **email**: Correo electrónico del usuario
    - **password**: Contraseña del usuario
    
    Retorna un token JWT que debe incluirse en el header Authorization
    como: Bearer <token>
    """
    
    # Buscar usuario por email
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verificar contraseña
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador"
        )

    # Crear token JWT con el user_id como 'sub' (subject)
    token = create_access_token({"sub": str(user.user_id)})

    return TokenResponse(
        access_token=token, 
        token_type="bearer"
    )