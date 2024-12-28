from typing import Dict, Any, List
import aiohttp
from aiochclient import ChClient
from app.core.config import settings

__all__ = ['get_metrics', 'clickhouse_client']

class ClickHouseClient:
    """
    Cliente assíncrono para ClickHouse
    """
    
    def __init__(self):
        self.url = settings.CLICKHOUSE_URL
        self.session = None
        self.client = None
    
    async def connect(self):
        """
        Estabelece conexão com ClickHouse
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
            self.client = ChClient(self.session, url=self.url)
    
    async def close(self):
        """
        Fecha conexão com ClickHouse
        """
        if self.session:
            await self.session.close()
            self.session = None
            self.client = None
    
    async def execute(self, query: str, params: List[Dict[str, Any]] = None):
        """
        Executa query no ClickHouse
        """
        if not self.client:
            await self.connect()
        
        if params:
            for param in params:
                await self.client.execute(query, param)
        else:
            await self.client.execute(query)
    
    async def fetchall(self, query: str) -> List[Dict[str, Any]]:
        """
        Executa query e retorna todos os resultados
        """
        if not self.client:
            await self.connect()
        
        return [dict(row) async for row in self.client.iterate(query)]
    
    async def fetchone(self, query: str) -> Dict[str, Any]:
        """
        Executa query e retorna primeiro resultado
        """
        if not self.client:
            await self.connect()
        
        async for row in self.client.iterate(query):
            return dict(row)
        return None
    
    async def get_user_metrics(
        self,
        user_id: int,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Obtém métricas de uso por usuário
        """
        # Métricas de geração de conteúdo
        generation_metrics = await self.fetchone(f"""
            SELECT
                COUNT(*) as total_generations,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(cached) as cached_generations,
                groupArray(provider) as providers_used
            FROM content_generation_events
            WHERE user_id = {user_id}
            AND timestamp BETWEEN '{start_date}' AND '{end_date}'
        """)
        
        # Métricas de conteúdo
        content_metrics = await self.fetchone(f"""
            SELECT
                COUNT(*) as total_contents,
                groupArray(content_type) as content_types,
                COUNT(DISTINCT content_type) as unique_content_types
            FROM content_events
            WHERE user_id = {user_id}
            AND timestamp BETWEEN '{start_date}' AND '{end_date}'
            AND event_type = 'content_created'
        """)
        
        # Métricas de template
        template_metrics = await self.fetchone(f"""
            SELECT
                COUNT(*) as total_templates,
                COUNT(DISTINCT template_type) as unique_template_types,
                SUM(event_type = 'template_used') as template_uses
            FROM template_events
            WHERE user_id = {user_id}
            AND timestamp BETWEEN '{start_date}' AND '{end_date}'
        """)
        
        return {
            "generation": generation_metrics,
            "content": content_metrics,
            "template": template_metrics
        }
    
    async def get_system_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Obtém métricas gerais do sistema
        """
        # Métricas de geração
        generation_metrics = await self.fetchone(f"""
            SELECT
                COUNT(*) as total_generations,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(cached) as cached_generations,
                groupArray(provider) as providers,
                COUNT(DISTINCT user_id) as unique_users
            FROM content_generation_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
        """)
        
        # Métricas por provedor
        provider_metrics = await self.fetchall(f"""
            SELECT
                provider,
                COUNT(*) as total_generations,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(cached) as cached_generations
            FROM content_generation_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY provider
        """)
        
        # Métricas de conteúdo
        content_metrics = await self.fetchone(f"""
            SELECT
                COUNT(*) as total_contents,
                COUNT(DISTINCT user_id) as content_users,
                groupArray(content_type) as content_types
            FROM content_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
            AND event_type = 'content_created'
        """)
        
        # Métricas de template
        template_metrics = await self.fetchone(f"""
            SELECT
                COUNT(*) as total_templates,
                COUNT(DISTINCT user_id) as template_users,
                SUM(event_type = 'template_used') as template_uses
            FROM template_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
        """)
        
        return {
            "generation": generation_metrics,
            "providers": provider_metrics,
            "content": content_metrics,
            "template": template_metrics
        }

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