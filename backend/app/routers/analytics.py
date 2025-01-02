from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Union, Literal
import random

from ..auth.dependencies import get_current_user
from ..models.user import User
from ..db.deps import get_db
from ..models.content import Content
from ..models.template import Template

router = APIRouter()

def get_date_range(time_range: str) -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    if time_range == "day":
        start_date = now - timedelta(days=1)
    elif time_range == "week":
        start_date = now - timedelta(weeks=1)
    else:  # month
        start_date = now - timedelta(days=30)
    return start_date, now

@router.get("/chart/line")
async def get_line_chart_data(
    time_range: Literal["day", "week", "month"] = Query(..., description="Período de tempo para os dados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna dados para o gráfico de linha de gerações por período"""
    start_date, end_date = get_date_range(time_range)
    
    # TODO: Implementar query real
    # Por enquanto, retornando dados mockados
    if time_range == "day":
        labels = [f"{i}h" for i in range(24)]
        data = [random.randint(0, 50) for _ in range(24)]
    elif time_range == "week":
        labels = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        data = [random.randint(20, 100) for _ in range(7)]
    else:
        labels = [f"Dia {i+1}" for i in range(30)]
        data = [random.randint(50, 200) for _ in range(30)]
    
    return {
        "labels": labels,
        "datasets": [{
            "label": "Gerações",
            "data": data
        }]
    }

@router.get("/chart/pie")
async def get_pie_chart_data(
    time_range: Literal["day", "week", "month"] = Query(..., description="Período de tempo para os dados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna dados para o gráfico de pizza de distribuição por template"""
    start_date, end_date = get_date_range(time_range)
    
    # TODO: Implementar query real
    # Por enquanto, retornando dados mockados
    templates = ["Blog Post", "Email Marketing", "Social Media", "Press Release"]
    data = [random.randint(10, 100) for _ in range(len(templates))]
    
    return {
        "labels": templates,
        "datasets": [{
            "data": data
        }]
    }

@router.get("/chart/bar")
async def get_bar_chart_data(
    time_range: Literal["day", "week", "month"] = Query(..., description="Período de tempo para os dados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna dados para o gráfico de barras de taxa de sucesso por template"""
    start_date, end_date = get_date_range(time_range)
    
    # TODO: Implementar query real
    # Por enquanto, retornando dados mockados
    templates = ["Blog Post", "Email Marketing", "Social Media", "Press Release"]
    success_rates = [random.uniform(0.8, 1.0) for _ in range(len(templates))]
    
    return {
        "labels": templates,
        "datasets": [{
            "label": "Taxa de Sucesso",
            "data": [rate * 100 for rate in success_rates]
        }]
    } 