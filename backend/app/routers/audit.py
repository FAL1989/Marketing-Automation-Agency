from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..core.auth import get_current_superuser
from ..db.deps import get_db
from ..models.audit import AuditLog
from ..schemas.audit import AuditLogResponse, AuditLogFilters, AuditLogStatistics
from ..core.security import verify_api_key

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get(
    "/logs",
    response_model=List[AuditLogResponse],
    dependencies=[Depends(get_current_superuser)]
)
async def get_audit_logs(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_types: Optional[List[str]] = Query(None),
    user_id: Optional[int] = Query(None),
    ip_address: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Retorna logs de auditoria com filtros
    
    Requer autenticação de superusuário
    """
    logs = AuditLog.get_by_filters(
        db=db,
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        user_id=user_id,
        ip_address=ip_address,
        severity=severity,
        limit=limit,
        offset=offset
    )
    return [log.to_dict() for log in logs]

@router.get(
    "/statistics",
    response_model=AuditLogStatistics,
    dependencies=[Depends(get_current_superuser)]
)
async def get_audit_statistics(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """
    Retorna estatísticas dos logs de auditoria
    
    Requer autenticação de superusuário
    """
    return AuditLog.get_statistics(db=db, days=days)

@router.get(
    "/export",
    dependencies=[Depends(get_current_superuser)]
)
async def export_audit_logs(
    db: Session = Depends(get_db),
    format: str = Query(..., regex="^(csv|json)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_types: Optional[List[str]] = Query(None)
):
    """
    Exporta logs de auditoria em CSV ou JSON
    
    Requer autenticação de superusuário
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io
    import json
    
    # Busca os logs
    logs = AuditLog.get_by_filters(
        db=db,
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        limit=10000  # Limite maior para exportação
    )
    
    if format == "csv":
        # Cria o CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "timestamp", "event_type", "user_id", "ip_address", "severity", "details"]
        )
        writer.writeheader()
        for log in logs:
            writer.writerow(log.to_dict())
        
        # Retorna o arquivo
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    else:
        # Retorna JSON
        return StreamingResponse(
            iter([json.dumps([log.to_dict() for log in logs], indent=2)]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.json"
            }
        )

@router.get(
    "/recent-activity/{user_id}",
    response_model=List[AuditLogResponse],
    dependencies=[Depends(get_current_superuser)]
)
async def get_user_recent_activity(
    user_id: int,
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=30)
):
    """
    Retorna atividade recente de um usuário
    
    Requer autenticação de superusuário
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    logs = AuditLog.get_by_filters(
        db=db,
        start_date=start_date,
        user_id=user_id,
        limit=1000
    )
    return [log.to_dict() for log in logs]

@router.get(
    "/security-events",
    response_model=List[AuditLogResponse],
    dependencies=[Depends(get_current_superuser)]
)
async def get_security_events(
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=30),
    min_severity: str = Query("warning")
):
    """
    Retorna eventos de segurança recentes
    
    Requer autenticação de superusuário
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    logs = AuditLog.get_by_filters(
        db=db,
        start_date=start_date,
        severity=min_severity,
        event_types=["ACCESS_DENIED", "SUSPICIOUS_ACTIVITY", "AUTHENTICATION_FAILED"],
        limit=1000
    )
    return [log.to_dict() for log in logs] 