from sqlalchemy.orm import Session
from ..models.user import User
from typing import Optional, List


class UserService:
    """
    Servicio que maneja operaciones relacionadas con usuarios.
    """

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
      
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
       
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
     
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def update_user(db: Session, user_id: int, update_data: dict) -> Optional[User]:
      
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return None
        
        # Actualizar solo los campos proporcionados
        for field, value in update_data.items():
            if value is not None and hasattr(user, field):
                setattr(user, field, value)
        
        try:
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al actualizar usuario: {str(e)}")

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> bool:
     
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        user.is_active = False
        
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al desactivar usuario: {str(e)}")

    @staticmethod
    def activate_user(db: Session, user_id: int) -> bool:
      
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        user.is_active = True
        
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al activar usuario: {str(e)}")

    @staticmethod
    def delete_user_permanently(db: Session, user_id: int) -> bool:
       
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        try:
            db.delete(user)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al eliminar usuario: {str(e)}")