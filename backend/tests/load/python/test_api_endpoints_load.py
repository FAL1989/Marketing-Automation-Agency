import pytest
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import json
import logging
from datetime import datetime
from app.core.config import settings
from app.core.redis import get_redis, init_redis_pool
from app.core.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class LoadTestResults:
    def __init__(self):
        self.response_times: List[float] = []
        self.error_count: int = 0
        self.success_count: int = 0
        self.start_time: float = time.time()
        self.end_time: float = 0
        self.requests_per_second: float = 0
        self.avg_response_time: float = 0
        self.p95_response_time: float = 0
        self.p99_response_time: float = 0
        self.min_response_time: float = float('inf')
        self.max_response_time: float = 0
        self.total_requests: int = 0
        self.success_rate: float = 0
        self.error_rate: float = 0

    def add_response_time(self, response_time: float):
        self.response_times.append(response_time)
        self.min_response_time = min(self.min_response_time, response_time)
        self.max_response_time = max(self.max_response_time, response_time)

    def calculate_metrics(self):
        self.end_time = time.time()
        total_time = self.end_time - self.start_time
        self.total_requests = self.success_count + self.error_count
        
        if self.total_requests > 0:
            self.success_rate = (self.success_count / self.total_requests) * 100
            self.error_rate = (self.error_count / self.total_requests) * 100
            
        if self.response_times:
            self.avg_response_time = statistics.mean(self.response_times)
            sorted_times = sorted(self.response_times)
            self.p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            self.p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
            
        if total_time > 0:
            self.requests_per_second = self.total_requests / total_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate, 2),
            "error_rate": round(self.error_rate, 2),
            "requests_per_second": round(self.requests_per_second, 2),
            "avg_response_time": round(self.avg_response_time * 1000, 2),
            "p95_response_time": round(self.p95_response_time * 1000, 2),
            "p99_response_time": round(self.p99_response_time * 1000, 2),
            "min_response_time": round(self.min_response_time * 1000, 2),
            "max_response_time": round(self.max_response_time * 1000, 2),
            "total_time": round(self.end_time - self.start_time, 2)
        }

    def save_to_file(self, filename: str):
        results = self.to_dict()
        results["timestamp"] = datetime.now().isoformat()
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Resultados salvos em {filename}")

async def run_load_test(
    endpoint: str,
    num_requests: int,
    concurrent_users: int,
    monitoring_service: MonitoringService,
    headers: Dict[str, str] = None
) -> LoadTestResults:
    """
    Executa teste de carga em um endpoint específico
    """
    results = LoadTestResults()
    semaphore = asyncio.Semaphore(concurrent_users)
    
    async def make_request():
        try:
            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    
                    try:
                        async with session.get(
                            f"{settings.API_V1_STR}{endpoint}",
                            headers=headers
                        ) as response:
                            await response.text()
                            end_time = time.time()
                            response_time = end_time - start_time
                            
                            if response.status == 200:
                                results.success_count += 1
                                results.add_response_time(response_time)
                                await monitoring_service.record_api_success(endpoint, response_time)
                            else:
                                results.error_count += 1
                                await monitoring_service.record_api_error(endpoint, response.status)
                                
                    except Exception as e:
                        logger.error(f"Erro na requisição: {str(e)}")
                        results.error_count += 1
                        await monitoring_service.record_api_error(endpoint, 500)
                        
        except Exception as e:
            logger.error(f"Erro ao criar sessão: {str(e)}")
            results.error_count += 1
            await monitoring_service.record_api_error(endpoint, 500)

    # Cria e executa as tasks
    tasks = [make_request() for _ in range(num_requests)]
    await asyncio.gather(*tasks)
    
    # Calcula métricas finais
    results.calculate_metrics()
    return results

@pytest.mark.asyncio
async def test_api_endpoints_load():
    """
    Teste de carga principal para endpoints da API
    """
    # Inicializa serviços
    redis = await init_redis_pool()
    monitoring_service = MonitoringService()
    
    # Configurações do teste
    test_configs = [
        {
            "endpoint": "/health",
            "num_requests": 1000,
            "concurrent_users": 50,
            "description": "Health Check Endpoint"
        },
        {
            "endpoint": "/metrics",
            "num_requests": 500,
            "concurrent_users": 25,
            "description": "Metrics Endpoint"
        }
    ]
    
    # Executa testes para cada endpoint
    for config in test_configs:
        logger.info(f"Iniciando teste de carga para {config['description']}")
        
        results = await run_load_test(
            endpoint=config["endpoint"],
            num_requests=config["num_requests"],
            concurrent_users=config["concurrent_users"],
            monitoring_service=monitoring_service
        )
        
        # Salva resultados
        filename = f"load_test_results_{config['endpoint'].replace('/', '_')}_{int(time.time())}.json"
        results.save_to_file(f"tests/load/results/{filename}")
        
        # Verifica métricas
        assert results.error_rate < 1.0, f"Taxa de erro muito alta: {results.error_rate}%"
        assert results.avg_response_time < 0.5, f"Tempo médio de resposta muito alto: {results.avg_response_time}s"
        assert results.p95_response_time < 1.0, f"P95 muito alto: {results.p95_response_time}s"
        
        logger.info(f"Teste de carga concluído para {config['description']}")
        logger.info(f"Resultados: {json.dumps(results.to_dict(), indent=2)}")
    
    # Limpa recursos
    await redis.close()

if __name__ == "__main__":
    asyncio.run(test_api_endpoints_load()) 