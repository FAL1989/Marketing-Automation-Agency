from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta
from app.core.clickhouse import clickhouse_client
from shared.cache import cache_manager
from app.api.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/metrics/realtime")
async def get_realtime_metrics(
    provider: Optional[str] = None,
    event_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtém métricas em tempo real do Redis
    """
    # Determinar chave base
    if provider:
        base_key = f"metrics:realtime:provider:{provider}"
    elif event_type:
        base_key = f"metrics:realtime:type:{event_type}"
    else:
        base_key = "metrics:realtime:total"
    
    # Obter métricas
    count = await cache_manager.get_rate_limit(f"{base_key}:count")
    tokens = await cache_manager.get_rate_limit(f"{base_key}:tokens")
    
    return {
        "last_hour": {
            "event_count": count,
            "token_count": tokens
        }
    }

@router.get("/metrics/historical")
async def get_historical_metrics(
    start_date: str = Query(..., description="Data inicial (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Data final (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Intervalo de agregação (1h, 1d)"),
    provider: Optional[str] = None,
    event_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtém métricas históricas do ClickHouse
    """
    try:
        # Validar datas
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use YYYY-MM-DD"
        )
    
    # Validar intervalo
    if interval not in ["1h", "1d"]:
        raise HTTPException(
            status_code=400,
            detail="Intervalo inválido. Use 1h ou 1d"
        )
    
    # Construir query base
    query = f"""
        SELECT
            toStartOf{interval}(timestamp) as period,
            COUNT(*) as event_count,
            SUM(tokens) as token_count,
            COUNT(DISTINCT user_id) as unique_users,
            provider
        FROM events
        WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
    """
    
    # Adicionar filtros opcionais
    if provider:
        query += f" AND provider = '{provider}'"
    if event_type:
        query += f" AND event_type = '{event_type}'"
    
    # Agrupar resultados
    query += " GROUP BY period, provider ORDER BY period"
    
    try:
        return await clickhouse_client.fetchall(query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar métricas: {str(e)}"
        )

@router.get("/metrics/summary")
async def get_metrics_summary(
    days: int = Query(7, description="Número de dias para análise")
) -> Dict[str, Any]:
    """
    Obtém um resumo das métricas dos últimos X dias
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    try:
        # Obter métricas do ClickHouse
        query = f"""
            SELECT
                toStartOfDay(timestamp) as period,
                COUNT(*) as event_count,
                SUM(tokens) as token_count,
                COUNT(DISTINCT user_id) as unique_users,
                provider
            FROM events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY period, provider
            ORDER BY period
        """
        
        metrics = await clickhouse_client.fetchall(query)
        
        # Calcular totais
        total_events = sum(m["event_count"] for m in metrics)
        total_tokens = sum(m["token_count"] for m in metrics)
        total_users = sum(m["unique_users"] for m in metrics)
        
        # Agrupar por provedor
        provider_stats = {}
        for m in metrics:
            provider = m["provider"]
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "events": 0,
                    "tokens": 0
                }
            provider_stats[provider]["events"] += m["event_count"]
            provider_stats[provider]["tokens"] += m["token_count"]
        
        return {
            "period": {
                "start": start_date,
                "end": end_date,
                "days": days
            },
            "totals": {
                "events": total_events,
                "tokens": total_tokens,
                "unique_users": total_users
            },
            "by_provider": provider_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter métricas: {str(e)}"
        )

@router.get(
    "/metrics/user",
    summary="Métricas do usuário",
    description="Retorna métricas de uso do usuário atual"
)
async def get_user_metrics(
    start_date: str = Query(
        default=(datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d"),
        description="Data inicial (YYYY-MM-DD)"
    ),
    end_date: str = Query(
        default=datetime.utcnow().strftime("%Y-%m-%d"),
        description="Data final (YYYY-MM-DD)"
    ),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Obtém métricas do usuário
    """
    try:
        metrics = await clickhouse_client.get_user_metrics(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter métricas: {str(e)}"
        )

@router.get(
    "/metrics/system",
    summary="Métricas do sistema",
    description="Retorna métricas gerais do sistema"
)
async def get_system_metrics(
    start_date: str = Query(
        default=(datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d"),
        description="Data inicial (YYYY-MM-DD)"
    ),
    end_date: str = Query(
        default=datetime.utcnow().strftime("%Y-%m-%d"),
        description="Data final (YYYY-MM-DD)"
    ),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Obtém métricas do sistema
    """
    try:
        # Verificar se usuário é admin
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=403,
                detail="Acesso não autorizado"
            )
        
        metrics = await clickhouse_client.get_system_metrics(
            start_date=start_date,
            end_date=end_date
        )
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter métricas: {str(e)}"
        ) 