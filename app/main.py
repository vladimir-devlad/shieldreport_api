import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

from app.database import SessionLocal
from app.models import Role, User
from app.routers import auth, roles, users

load_dotenv()  # ← primero siempre

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_default_admin():
    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.name == "admin").first()

        if not admin_role:
            roles = [
                Role(name="admin", description="Acceso total al sistema"),
                Role(name="supervisor", description="Puede gestionar reportes"),
                Role(name="usuario", description="Acceso estándar"),
            ]
            db.add_all(roles)
            db.commit()
            db.refresh(roles[0])
            admin_role = roles[0]
            print("✅ Roles creados correctamente")

        existing_admin = db.query(User).filter(User.role_id == admin_role.id).first()

        if not existing_admin:
            default_admin = User(
                name=os.getenv("DEFAULT_ADMIN_NAME"),
                last_name=os.getenv("DEFAULT_ADMIN_LASTNAME"),
                username=os.getenv("DEFAULT_ADMIN_USERNAME"),
                password=pwd_context.hash(os.getenv("DEFAULT_ADMIN_PASSWORD")),
                is_active=True,
                role_id=admin_role.id,
            )
            db.add(default_admin)
            db.commit()
            print(f"✅ Admin creado → usuario: {os.getenv('DEFAULT_ADMIN_USERNAME')}")
        else:
            print("ℹ️  Admin ya existe, no se crea uno nuevo")

    except Exception as e:
        print(f"❌ Error al crear admin por defecto: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando servidor SOC API...")
    create_default_admin()
    yield
    print("Servidor apagado")


app = FastAPI(
    title="SOC Management API",
    description="API para gestión de reportes SOC",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)  # ← después de crear app
app.include_router(users.router)
app.include_router(roles.router)


@app.get("/")
def root():
    return {"message": "SOC Management API funcionando", "version": "1.0.0"}
