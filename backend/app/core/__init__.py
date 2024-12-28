"""
Core module initialization
"""

from .clickhouse import get_metrics, clickhouse_client

__all__ = ['get_metrics', 'clickhouse_client'] 