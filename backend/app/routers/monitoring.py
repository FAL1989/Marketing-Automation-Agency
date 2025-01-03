from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.monitoring_service import MonitoringService
from app.schemas.monitoring import SystemMetrics, ApplicationMetrics, MetricSummary, MetricRecord, MonitoringMetricCreate, MonitoringMetricResponse
from app.repositories.monitoring_repository import MonitoringRepository

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"]
)

async def get_monitoring_service(
    session: AsyncSession = Depends(get_db)
) -> MonitoringService:
    """
    Dependência para obter o serviço de monitoramento
    """
    return MonitoringService(session=session)

@router.get("/system", response_model=SystemMetrics)
async def get_system_metrics(
    service: MonitoringService = Depends(get_monitoring_service)
) -> SystemMetrics:
    """
    Obtém métricas do sistema
    """
    try:
        metrics = await service.get_system_metrics()
        if not metrics:
            raise HTTPException(
                status_code=500,
                detail="Não foi possível coletar métricas do sistema"
            )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter métricas do sistema: {str(e)}"
        )

@router.get("/application", response_model=ApplicationMetrics)
async def get_application_metrics(
    service: MonitoringService = Depends(get_monitoring_service)
) -> ApplicationMetrics:
    """
    Obtém métricas da aplicação
    """
    try:
        metrics = await service.get_application_metrics()
        if not metrics:
            raise HTTPException(
                status_code=500,
                detail="Não foi possível coletar métricas da aplicação"
            )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter métricas da aplicação: {str(e)}"
        )

@router.get("/history/{metric_type}", response_model=List[MetricRecord])
async def get_metrics_history(
    metric_type: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    service: MonitoringService = Depends(get_monitoring_service)
) -> List[Dict]:
    """
    Obtém histórico de métricas
    """
    # Define intervalo padrão (últimas 24h)
    if end_time is None:
        end_time = datetime.utcnow().timestamp()
    if start_time is None:
        start_time = end_time - (24 * 60 * 60)
        
    metrics = await service.get_metrics_history(
        metric_type=metric_type,
        start_time=start_time,
        end_time=end_time
    )
    return metrics

@router.get("/summary", response_model=MetricSummary)
async def get_metrics_summary(
    metric_type: Optional[str] = None,
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict:
    """
    Obtém resumo das métricas
    """
    return await service.get_metrics_summary(
        metric_type=metric_type
    )

@router.post("/cleanup")
async def cleanup_metrics(
    older_than: Optional[float] = None,
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, int]:
    """
    Remove métricas antigas
    """
    count = await service.cleanup_metrics(
        older_than=older_than
    )
    return {"deleted_count": count} 