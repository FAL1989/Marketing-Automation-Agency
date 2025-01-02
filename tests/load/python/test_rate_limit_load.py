import pytest
import asyncio
import aiohttp
import time
from fastapi import FastAPI
from ...app.middleware.rate_limit import RateLimitMiddleware
from ...app.core.config import settings
import uvicorn
import multiprocessing
import statistics
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def create_test_app():
    """
    Cria uma aplicação FastAPI para testes
    """
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app

def run_server(host: str, port: int):
    """
    Executa o servidor de teste
    """
    app = create_test_app()
    uvicorn.run(app, host=host, port=port)

@pytest.fixture(scope="module")
def server():
    """
    Fixture que inicia o servidor de teste
    """
    host = "localhost"
    port = 8000
    
    # Inicia o servidor em um processo separado
    process = multiprocessing.Process(
        target=run_server,
        args=(host, port)
    )
    process.start()
    
    # Aguarda o servidor iniciar
    time.sleep(2)
    
    yield f"http://{host}:{port}"
    
    # Encerra o servidor
    process.terminate()
    process.join()

async def make_requests(
    url: str,
    total_requests: int,
    concurrent_requests: int,
    headers: Dict[str, str] = None
) -> List[Dict]:
    """
    Faz requisições concorrentes para o servidor
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        results = []
        
        async def make_request():
            start_time = time.time()
            try:
                async with session.get(url, headers=headers) as response:
                    elapsed = time.time() - start_time
                    return {
                        "status": response.status,
                        "elapsed": elapsed,
                        "headers": dict(response.headers)
                    }
            except Exception as e:
                logger.error(f"Error making request: {e}")
                return {
                    "status": 500,
                    "elapsed": time.time() - start_time,
                    "error": str(e)
                }
        
        # Cria as tasks para as requisições
        for _ in range(total_requests):
            if len(tasks) >= concurrent_requests:
                # Aguarda algumas tasks completarem
                done, tasks = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                results.extend([task.result() for task in done])
            
            tasks.append(asyncio.create_task(make_request()))
        
        # Aguarda as tasks restantes
        if tasks:
            done, _ = await asyncio.wait(tasks)
            results.extend([task.result() for task in done])
        
        return results

@pytest.mark.asyncio
async def test_rate_limit_single_client(server):
    """
    Testa o rate limit para um único cliente
    """
    # Configuração do teste
    total_requests = settings.RATE_LIMIT_PER_MINUTE * 2
    concurrent_requests = 10
    
    # Faz as requisições
    results = await make_requests(
        f"{server}/test",
        total_requests,
        concurrent_requests
    )
    
    # Análise dos resultados
    status_counts = {}
    latencies = []
    
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == 200:
            latencies.append(result["elapsed"])
    
    # Verifica se o rate limit foi aplicado
    assert status_counts.get(429, 0) > 0
    assert status_counts.get(200, 0) <= settings.RATE_LIMIT_PER_MINUTE
    
    # Análise de latência
    if latencies:
        logger.info(f"Latency stats:")
        logger.info(f"  Min: {min(latencies):.3f}s")
        logger.info(f"  Max: {max(latencies):.3f}s")
        logger.info(f"  Avg: {statistics.mean(latencies):.3f}s")
        logger.info(f"  Med: {statistics.median(latencies):.3f}s")

@pytest.mark.asyncio
async def test_rate_limit_multiple_clients(server):
    """
    Testa o rate limit para múltiplos clientes
    """
    # Configuração do teste
    clients = 5
    requests_per_client = settings.RATE_LIMIT_PER_MINUTE
    concurrent_requests = 10
    
    # Faz requisições para cada cliente
    tasks = []
    for i in range(clients):
        headers = {"X-Forwarded-For": f"192.168.1.{i}"}
        tasks.append(
            make_requests(
                f"{server}/test",
                requests_per_client,
                concurrent_requests,
                headers
            )
        )
    
    # Aguarda todas as requisições completarem
    results = await asyncio.gather(*tasks)
    
    # Análise dos resultados por cliente
    for i, client_results in enumerate(results):
        status_counts = {}
        latencies = []
        
        for result in client_results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            if status == 200:
                latencies.append(result["elapsed"])
        
        # Verifica se cada cliente tem seu próprio rate limit
        assert status_counts.get(200, 0) <= settings.RATE_LIMIT_PER_MINUTE
        
        # Análise de latência por cliente
        if latencies:
            logger.info(f"Client {i} latency stats:")
            logger.info(f"  Min: {min(latencies):.3f}s")
            logger.info(f"  Max: {max(latencies):.3f}s")
            logger.info(f"  Avg: {statistics.mean(latencies):.3f}s")
            logger.info(f"  Med: {statistics.median(latencies):.3f}s")

@pytest.mark.asyncio
async def test_rate_limit_burst(server):
    """
    Testa o comportamento do rate limit em situações de burst
    """
    # Configuração do teste
    burst_size = settings.RATE_LIMIT_PER_MINUTE
    concurrent_requests = burst_size
    
    # Faz um burst de requisições
    results = await make_requests(
        f"{server}/test",
        burst_size,
        concurrent_requests
    )
    
    # Análise dos resultados
    status_counts = {}
    latencies = []
    
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == 200:
            latencies.append(result["elapsed"])
    
    # Verifica se o rate limit foi aplicado mesmo em burst
    assert status_counts.get(200, 0) <= settings.RATE_LIMIT_PER_MINUTE
    
    # Análise de latência
    if latencies:
        logger.info(f"Burst latency stats:")
        logger.info(f"  Min: {min(latencies):.3f}s")
        logger.info(f"  Max: {max(latencies):.3f}s")
        logger.info(f"  Avg: {statistics.mean(latencies):.3f}s")
        logger.info(f"  Med: {statistics.median(latencies):.3f}s") 