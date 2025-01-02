import asyncio
import pytest
import httpx
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import statistics

# Configurações dos testes
BASE_URL = "http://localhost:8000"
NUM_REQUESTS = 100  # Número total de requisições
CONCURRENT_USERS = 10  # Número de usuários simultâneos
ENDPOINTS = [
    "/"  # Endpoint raiz
]

class LoadTestResults:
    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.success_count: int = 0
        self.error_count: int = 0

    def add_result(self, response_time: float, success: bool, error_msg: str = None):
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            self.errors.append(error_msg)

    def get_statistics(self) -> Dict:
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        return {
            "total_requests": len(self.response_times),
            "success_rate": (self.success_count / len(self.response_times)) * 100,
            "error_rate": (self.error_count / len(self.response_times)) * 100,
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "p95_response_time": p95,
            "p99_response_time": p99,
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times)
        }

async def make_request(endpoint: str, results: LoadTestResults):
    async with httpx.AsyncClient() as client:
        try:
            start_time = time.time()
            response = await client.get(f"{BASE_URL}{endpoint}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convertendo para ms
            success = response.status_code == 200
            
            results.add_result(
                response_time=response_time,
                success=success,
                error_msg=None if success else f"Status code: {response.status_code}"
            )
            
        except Exception as e:
            results.add_result(
                response_time=0,
                success=False,
                error_msg=str(e)
            )

async def run_load_test(endpoint: str) -> Dict:
    results = LoadTestResults()
    tasks = []
    
    # Criando grupos de requisições concorrentes
    for _ in range(0, NUM_REQUESTS, CONCURRENT_USERS):
        batch = min(CONCURRENT_USERS, NUM_REQUESTS - len(tasks))
        batch_tasks = [make_request(endpoint, results) for _ in range(batch)]
        tasks.extend(batch_tasks)
        
        # Executando batch de requisições
        await asyncio.gather(*batch_tasks)
        
        # Pequena pausa entre batches para não sobrecarregar
        await asyncio.sleep(0.1)
    
    return results.get_statistics()

@pytest.mark.asyncio
async def test_endpoint_load():
    """Teste de carga para endpoints críticos"""
    print("\nIniciando testes de carga...")
    
    all_results = {}
    for endpoint in ENDPOINTS:
        print(f"\nTestando endpoint: {endpoint}")
        results = await run_load_test(endpoint)
        all_results[endpoint] = results
        
        # Validando resultados
        assert results["success_rate"] >= 95, f"Taxa de sucesso muito baixa para {endpoint}"
        assert results["avg_response_time"] < 500, f"Tempo médio de resposta muito alto para {endpoint}"
        assert results["p95_response_time"] < 1000, f"P95 muito alto para {endpoint}"
        
        print(f"\nResultados para {endpoint}:")
        print(f"Taxa de Sucesso: {results['success_rate']:.2f}%")
        print(f"Tempo Médio de Resposta: {results['avg_response_time']:.2f}ms")
        print(f"P95: {results['p95_response_time']:.2f}ms")
        print(f"P99: {results['p99_response_time']:.2f}ms")
        
    return all_results

if __name__ == "__main__":
    asyncio.run(test_endpoint_load()) 