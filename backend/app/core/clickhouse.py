"""
ClickHouse client and metrics functions
"""

from typing import Dict, Any
import aiohttp
from aiochclient import ChClient
from app.core.config import settings

__all__ = ['get_metrics', 'clickhouse_client']

class ClickHouseClient:
    def __init__(self):
        self.url = settings.CLICKHOUSE_URL
        self.user = settings.CLICKHOUSE_USER
        self.password = settings.CLICKHOUSE_PASSWORD
        self.database = settings.CLICKHOUSE_DB
        self.session = None
        self.client = None
    
    async def connect(self):
        """Estabelece conexão com ClickHouse"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            self.client = ChClient(
                self.session, 
                url=self.url,
                user=self.user,
                password=self.password,
                database=self.database
            )
    
    async def close(self):
        """Fecha conexão com ClickHouse"""
        if self.session:
            await self.session.close()
            self.session = None
            self.client = None

    async def execute(self, query: str):
        """Executa query no ClickHouse"""
        if not self.client:
            await self.connect()
        return await self.client.execute(query)

    async def fetchall(self, query: str) -> list:
        """Executa query e retorna todos os resultados"""
        if not self.client:
            await self.connect()
        return [dict(row) async for row in self.client.iterate(query)]

    async def fetchone(self, query: str) -> Dict[str, Any]:
        """Executa query e retorna primeiro resultado"""
        if not self.client:
            await self.connect()
        async for row in self.client.iterate(query):
            return dict(row)
        return None

clickhouse_client = ClickHouseClient()

async def get_metrics() -> Dict[str, Any]:
    """
    Obtém métricas do ClickHouse
    """
    try:
        # Exemplo de consulta para obter métricas
        query = """
            SELECT 
                count() as total_requests,
                avg(response_time) as avg_response_time,
                max(response_time) as max_response_time
            FROM request_logs
            WHERE timestamp >= now() - INTERVAL 1 DAY
        """
        result = await clickhouse_client.fetchone(query)
        
        if not result:
            return {
                "total_requests": 0,
                "avg_response_time": 0,
                "max_response_time": 0
            }
            
        return {
            "total_requests": result["total_requests"],
            "avg_response_time": float(result["avg_response_time"]),
            "max_response_time": float(result["max_response_time"])
        }
        
    except Exception as e:
        # Em caso de erro, retorna métricas zeradas
        return {
            "total_requests": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "error": str(e)
        } 