import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

from app.database import SessionLocal
from app.models import Role, User
from app.routers import auth, razon_social, reportes, roles, supervisor, users

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_allowed_origins() -> list[str]:
    """
    Lee ALLOWED_ORIGINS del .env separado por comas.
    Fallback: solo localhost para no romper nada si falta la variable.
    """
    origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
    return [o.strip() for o in origins_env.split(",")]


def create_default_superadmin():
    db = SessionLocal()
    try:
        roles_data = [
            {"name": "superadmin", "description": "Control total del sistema"},
            {"name": "admin", "description": "Gestión de supervisores y usuarios"},
            {"name": "supervisor", "description": "Gestión de su grupo de usuarios"},
            {"name": "usuario", "description": "Acceso estándar"},
        ]
        for r in roles_data:
            existing = db.query(Role).filter(Role.name == r["name"]).first()
            if not existing:
                db.add(Role(name=r["name"], description=r["description"]))
        db.commit()
        print("Roles verificados correctamente")

        superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
        existing_superadmin = (
            db.query(User).filter(User.role_id == superadmin_role.id).first()
        )

        if not existing_superadmin:
            default_superadmin = User(
                name=os.getenv("DEFAULT_SUPERADMIN_NAME"),
                last_name=os.getenv("DEFAULT_SUPERADMIN_LASTNAME"),
                username=os.getenv("DEFAULT_SUPERADMIN_USERNAME"),
                password=pwd_context.hash(os.getenv("DEFAULT_SUPERADMIN_PASSWORD")),
                is_active=True,
                role_id=superadmin_role.id,
            )
            db.add(default_superadmin)
            db.commit()
            print(
                f"Superadmin creado → usuario: {os.getenv('DEFAULT_SUPERADMIN_USERNAME')}"
            )
        else:
            print("Superadmin ya existe, no se crea uno nuevo")

    except Exception as e:
        print(f"Error al crear superadmin por defecto: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    env_name = os.getenv("APP_ENV", "development")
    print(f"Iniciando servidor SOC API... [{env_name}]")
    print(f"  CORS origins: {get_allowed_origins()}")
    create_default_superadmin()
    yield
    print("Servidor apagado")


app = FastAPI(
    title="SOC Management API",
    description="API para gestión de reportes SOC",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(razon_social.router)
app.include_router(supervisor.router)
app.include_router(reportes.router)


@app.get("/")
def root():
    return {
        "message": "SOC Management API funcionando",
        "version": "1.0.0",
        "env": os.getenv("APP_ENV", "development"),
    }
