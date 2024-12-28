"""
Metrics routes module
"""

from fastapi import APIRouter, HTTPException
from app.core.clickhouse import get_metrics, clickhouse_client

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/")
async def read_metrics():
    """
    Get system metrics from ClickHouse
    """
    try:
        metrics = await get_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching metrics: {str(e)}"
        ) 