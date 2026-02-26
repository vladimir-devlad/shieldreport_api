import os
import re
import sys
import unicodedata
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from passlib.context import CryptContext

from app.database import SessionLocal
from app.models.razon_social import RazonSocial
from app.models.role import Role
from app.models.user import User
from app.models.user_email import UserEmail
from app.models.user_phone import UserPhone
from app.models.user_razon_social import UserRazonSocial
from app.models.user_supervisor import UserSupervisor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", "Welcome123!")


# ─────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────


def to_title_case(text: str) -> str:
    if not text:
        return ""
    return str(text).strip().title()


def clean_username(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.lower().strip())


def generate_username(Name: str, last_name: str, db) -> str:
    base = f"{clean_username(Name)}.{clean_username(last_name)}"
    username = base
    counter = 2
    while db.query(User).filter(User.username == username).first():
        username = f"{base}{counter}"
        counter += 1
    return username


def validate_phone(phone: str) -> bool:
    if not phone:
        return True
    cleaned = str(phone).replace(" ", "").replace("-", "")
    return bool(re.match(r"^\+?[1-9]\d{6,14}$", cleaned))


def safe_str(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def parse_is_active(value: str) -> bool:
    """Convierte SI/NO, TRUE/FALSE, 1/0 a booleano"""
    v = safe_str(value).upper()
    return v in ["SI", "SÍ", "TRUE", "1", "ACTIVO", "ACTIVA", "YES", "S"]


def get_razon_sociales(row, db) -> list:
    razon_sociales = []
    # intenta RazonSocial, RazonSocial1, RazonSocial2...
    cols = ["RazonSocial"] + [f"RazonSocial{i}" for i in range(1, 10)]
    for col in cols:
        if col not in row.index:
            continue
        name = safe_str(row.get(col))
        if not name:
            continue
        rs = (
            db.query(RazonSocial)
            .filter(RazonSocial.name == name, RazonSocial.is_active == True)
            .first()
        )
        if not rs:
            raise ValueError(f"Razón social '{name}' no encontrada o inactiva")
        razon_sociales.append(rs)
    return razon_sociales


# ─────────────────────────────────────────
# PROCESAR SUPERVISORES
# ─────────────────────────────────────────


def get_supervisores(row, db) -> list:
    """
    Extrae todos los supervisores de las columnas:
    Supervisor, Supervisor2, Supervisor3...
    """
    supervisores = []
    cols = ["Supervisor"] + [f"Supervisor{i}" for i in range(2, 10)]

    for col in cols:
        if col not in row.index:
            continue
        username = safe_str(row.get(col))
        if not username:
            continue

        supervisor = db.query(User).filter(User.username == username).first()

        if not supervisor:
            raise ValueError(f"Supervisor '{username}' no encontrado en BD")
        if supervisor.role.name != "supervisor":
            raise ValueError(f"'{username}' no tiene rol de supervisor")

        # evita duplicados
        if supervisor.id not in [s.id for s in supervisores]:
            supervisores.append(supervisor)

    return supervisores


# ─────────────────────────────────────────
# PROCESAR RAZONES SOCIALES
# ─────────────────────────────────────────


def process_razon_social(df, db, errors: list):
    success = 0
    skip = 0

    print(f"  Filas encontradas: {len(df)}\n")

    for index, row in df.iterrows():
        fila = index + 2
        try:
            name = to_title_case(safe_str(row.get("Name")))
            if not name:
                raise ValueError("Name es obligatorio")

            is_active = parse_is_active(safe_str(row.get("IsActive")))

            # verifica si ya existe
            existing = db.query(RazonSocial).filter(RazonSocial.name == name).first()

            if existing:
                # si ya existe solo actualiza is_active
                existing.is_active = is_active
                db.commit()
                print(
                    f"  🔄 Fila {fila}: '{name}' ya existe → actualizado is_active={is_active}"
                )
                success += 1
            else:
                # crea nueva
                rs = RazonSocial(name=name, is_active=is_active)
                db.add(rs)
                db.commit()
                status = "activa" if is_active else "inactiva"
                print(f"  ✅ Fila {fila}: '{name}' creada ({status})")
                success += 1

        except ValueError as e:
            db.rollback()
            skip += 1
            msg = f"Fila {fila} ({safe_str(row.get('Name'))}): {str(e)}"
            errors.append(f"[RAZON_SOCIAL] {msg}")
            print(f"  ⚠️  {msg}")

        except Exception as e:
            db.rollback()
            skip += 1
            msg = f"Fila {fila}: Error inesperado → {str(e)}"
            errors.append(f"[RAZON_SOCIAL] {msg}")
            print(f"  ❌ {msg}")

    return success, skip


# ─────────────────────────────────────────
# PROCESAR USUARIOS POR ROL
# ─────────────────────────────────────────


def process_sheet(df, role_name: str, db, errors: list):
    success = 0
    skip = 0

    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        print(f"❌ Rol '{role_name}' no encontrado en BD")
        return success, skip

    print(f"  Filas encontradas: {len(df)}\n")

    for index, row in df.iterrows():
        fila = index + 2
        try:
            Name = to_title_case(safe_str(row.get("Name")))
            last_name = to_title_case(safe_str(row.get("LastName")))

            if not Name:
                raise ValueError("Name es obligatorio")
            if not last_name:
                raise ValueError("LastName es obligatorio")

            middle_name = to_title_case(safe_str(row.get("MiddleName"))) or None
            second_last_name = (
                to_title_case(safe_str(row.get("SecondLastName"))) or None
            )

            email_1 = safe_str(row.get("Email1")) or None
            email_2 = safe_str(row.get("Email2")) or None
            emails = [e for e in [email_1, email_2] if e]

            for email in emails:
                existing = db.query(UserEmail).filter(UserEmail.email == email).first()
                if existing:
                    raise ValueError(f"Email '{email}' ya está registrado")

            phone = safe_str(row.get("Phone")) or None
            if phone and not validate_phone(phone):
                raise ValueError(f"Teléfono '{phone}' inválido. Ejemplo: +51987654321")

            # supervisor solo para usuarios
            supervisores = []
            if role_name == "usuario":
                supervisores = get_supervisores(row, db)

            # razones sociales
            razon_sociales = get_razon_sociales(row, db)

            # genera username automático
            username = generate_username(Name, last_name, db)

            # crea usuario
            new_user = User(
                Name=Name,
                middle_name=middle_name,
                last_name=last_name,
                second_last_name=second_last_name,
                username=username,
                password=pwd_context.hash(DEFAULT_PASSWORD),
                role_id=role.id,
                is_active=True,
            )
            db.add(new_user)
            db.flush()

            for email in emails:
                db.add(UserEmail(user_id=new_user.id, email=email))

            if phone:
                db.add(
                    UserPhone(
                        user_id=new_user.id,
                        phone_number=phone.replace(" ", "").replace("-", ""),
                    )
                )

            for supervisor in supervisores:
                db.add(UserSupervisor(supervisor_id=supervisor.id, user_id=new_user.id))

            for rs in razon_sociales:
                db.add(UserRazonSocial(user_id=new_user.id, razon_social_id=rs.id))

            db.commit()
            success += 1
            print(f"  ✅ Fila {fila}: {Name} {last_name} → {username}")

        except ValueError as e:
            db.rollback()
            skip += 1
            msg = f"Fila {fila} ({safe_str(row.get('Name'))} {safe_str(row.get('LastName'))}): {str(e)}"
            errors.append(f"[{role_name.upper()}] {msg}")
            print(f"  ⚠️  {msg}")

        except Exception as e:
            db.rollback()
            skip += 1
            msg = f"Fila {fila}: Error inesperado → {str(e)}"
            errors.append(f"[{role_name.upper()}] {msg}")
            print(f"  ❌ {msg}")

    return success, skip


# ─────────────────────────────────────────
# CARGA PRINCIPAL
# ─────────────────────────────────────────


def load_all(excel_path: str):
    db = SessionLocal()
    errors = []
    total_success = 0
    total_skip = 0

    print(f"\n{'=' * 60}")
    print("  CARGA MASIVA")
    print(f"  Archivo : {excel_path}")
    print(f"  Fecha   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    try:
        xl = pd.ExcelFile(excel_path)
        sheets = xl.sheet_names
        print(f"📊 Hojas encontradas: {', '.join(sheets)}\n")
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        db.close()
        return

    # orden de procesamiento
    order = [
        ("razon_social", None),  # primero RS
        ("admins", "admin"),
        ("supervisores", "supervisor"),
        ("usuarios", "usuario"),
    ]

    for sheet_name, role_name in order:
        if sheet_name not in sheets:
            print(f"⚠️  Hoja '{sheet_name}' no encontrada, se omite.\n")
            continue

        print(f"{'─' * 60}")
        print(f"  Procesando: {sheet_name.upper()}")
        print(f"{'─' * 60}")

        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype=str)
            df = df.where(pd.notna(df), None)
        except Exception as e:
            print(f"❌ Error al leer hoja '{sheet_name}': {e}\n")
            continue

        if sheet_name == "razon_social":
            success, skip = process_razon_social(df, db, errors)
        else:
            success, skip = process_sheet(df, role_name, db, errors)

        total_success += success
        total_skip += skip
        print()

    db.close()

    # resumen
    print(f"\n{'=' * 60}")
    print("  RESUMEN FINAL")
    print(f"{'=' * 60}")
    print(f"  ✅ Registros creados  : {total_success}")
    print(f"  ⚠️  Filas con error   : {total_skip}")
    print(f"{'=' * 60}\n")

    if errors:
        os.makedirs("logs", exist_ok=True)
        log_file = f"logs/errores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(
                f"LOG DE ERRORES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write(f"Archivo: {excel_path}\n")
            f.write(f"{'=' * 60}\n\n")
            for error in errors:
                f.write(f"{error}\n")
        print(f"📄 Log guardado en: {log_file}\n")
    else:
        print("🎉 Carga completada sin errores.\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/load_users.py carga_masiva.xlsx")
        sys.exit(1)

    excel_file = sys.argv[1]
    if not os.path.exists(excel_file):
        print(f"❌ Archivo no encontrado: {excel_file}")
        sys.exit(1)

    load_all(excel_file)
