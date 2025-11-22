# app/routers/user.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.models.user import User

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Obtiene el perfil del usuario autenticado actualmente.
    
    Requiere token de autenticación en el header:
    Authorization: Bearer <token>
    
    Retorna toda la información del usuario excepto la contraseña.
    
    **Ejemplo de uso:**
    ```bash
    curl -X GET "http://localhost:8000/users/me" \
      -H "Authorization: Bearer <tu_token_aqui>"
    ```
    """
    return current_user

