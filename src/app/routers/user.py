# app/routers/user.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..core.security import get_current_user
from ..schemas.user import UserResponse
from ..models.user import User

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
  
    return current_user

