from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.sync_log import SyncLog
from app.models.user import User
from app.schemas.sync_log import SyncLogResponse

router = APIRouter(prefix="/sync", tags=["Sincronización"])


@router.get("/last", response_model=SyncLogResponse)
def get_last_sync(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Devuelve la última vez que se actualizó sot_reportes.
    Disponible para todos los roles.
    """
    log = db.query(SyncLog).filter(SyncLog.table_name == "sot_reportes").first()

    if not log:
        raise HTTPException(
            status_code=404, detail="No hay registros de sincronización"
        )

    return log
