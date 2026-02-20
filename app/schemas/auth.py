from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Lo que el usuario envía para hacer login"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Lo que el API devuelve tras un login exitoso"""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str
    name: str  # ← agregar
    last_name: str  # ← agregar
