from pydantic import BaseModel


class AgregarUsuarioRequest(BaseModel):
    supervisor_id: int
    user_id: int


class RemoverUsuarioRequest(BaseModel):
    supervisor_id: int
    user_id: int
