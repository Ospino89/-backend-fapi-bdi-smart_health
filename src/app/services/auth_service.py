# app/services/auth_service.py

from sqlalchemy.orm import Session
from app.models.user import User
from ..core.security import create_access_token, verify_password, hash_password


class AuthService:

    @staticmethod
    def create_user(db: Session, user_data):
        """
        Registra un nuevo usuario en la base de datos.
        user_data debe ser un esquema Pydantic con:
            first_name, middle_name, first_surname, second_surname,
            email, password
        """
        # Verificar si ya existe el correo
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("El correo ya está registrado")

        # Crear nuevo usuario
        new_user = User(
            first_name=user_data.first_name,
            middle_name=user_data.middle_name,
            first_surname=user_data.first_surname,
            second_surname=user_data.second_surname,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        """
        Valida credenciales y genera JWT.
        """
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    def login(db: Session, email: str, password: str):
        """
        Servicio principal de login.
        Autentica y retorna token JWT.
        """

        user = AuthService.authenticate_user(db, email, password)

        if not user:
            raise ValueError("Credenciales incorrectas")

        # Generar token
        token_data = {
            "user_id": user.user_id,
            "email": user.email
        }

        access_token = create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()
