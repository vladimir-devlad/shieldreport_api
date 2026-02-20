import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.session import UserSession as SessionModel
from app.models.user import User

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Genera un JWT con expiración"""
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def login(
    username: str, password: str, db: Session, ip: str = None, user_agent: str = None
):
    # busca el usuario
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado, contacte al administrador",
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    # genera el token
    token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.name,
            "name": user.name,  # ← agregar
            "last_name": user.last_name,  # ← agregar
        }
    )

    # guarda la sesión en la BD
    expires_at = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    session = SessionModel(
        user_id=user.id,
        token=token,
        ip_address=ip,
        user_agent=user_agent,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role.name,
        "name": user.name,  # ← agregar
        "last_name": user.last_name,  # ← agregar
    }


def logout(token: str, db: Session):
    """Elimina la sesión de la BD invalidando el token"""
    session = db.query(SessionModel).filter(SessionModel.token == token).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada"
        )

    db.delete(session)
    db.commit()
    return {"message": "Sesión cerrada correctamente"}
