from typing import Dict, Any
import psutil
import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models.user import User
from prometheus_client import CollectorRegistry

# Criar registro global do Prometheus
REGISTRY = CollectorRegistry()

async def get_system_metrics() -> Dict[str, Any]:
    """
    Coleta métricas do sistema
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "count": psutil.cpu_count()
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    }

async def get_application_metrics(db: Session) -> Dict[str, Any]:
    """
    Coleta métricas da aplicação
    """
    # TODO: Implementar métricas específicas da aplicação
    return {
        "users": {
            "total": db.query(User).count(),
            "active": db.query(User).filter(User.is_active == True).count()
        },
        "requests": {
            "total": 0,  # TODO: Implementar contagem de requisições
            "success_rate": 100.0
        },
        "response_time": {
            "avg": 0.0,  # TODO: Implementar média de tempo de resposta
            "p95": 0.0,
            "p99": 0.0
        }
    } 