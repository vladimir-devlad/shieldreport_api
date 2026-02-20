from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import login, logout

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login_endpoint(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    ip = request.client.host
    user_agent = request.headers.get("user-agent")
    return login(body.username, body.password, db, ip, user_agent)


@router.post("/logout")
def logout_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = request.headers.get("authorization").split(" ")[1]
    return logout(token, db)
