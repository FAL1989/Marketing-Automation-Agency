import asyncio
import pytest
import httpx
import time
import json
from typing import List, Dict
import statistics
from datetime import datetime

# Configurações dos testes
BASE_URL = "http://localhost:8000"
NUM_REQUESTS = 2000  # Número total de requisições
CONCURRENT_USERS = 100  # Número de usuários simultâneos
TEST_ENDPOINT = "/api/v1/test-rate-limit"  # Endpoint para teste

class RateLimitTestResults:
    def __init__(self):
        self.response_times: List[float] = []
        self.blocked_times: List[float] = []
        self.success_count: int = 0
        self.blocked_count: int = 0
        self.error_count: int = 0
        self.errors: List[str] = []

    def add_result(self, response_time: float, status_code: int, error_msg: str = None):
        if response_time > 0:
            self.response_times.append(response_time)
            
            if status_code == 429:  # Too Many Requests
                self.blocked_times.append(response_time)
                self.blocked_count += 1
            elif status_code == 200:
                self.success_count += 1
            else:
                self.error_count += 1
                self.errors.append(error_msg or f"Status code: {status_code}")

    def get_statistics(self) -> Dict:
        total_requests = len(self.response_times)
        if total_requests == 0:
            return {}
            
        stats = {
            "total_requests": total_requests,
            "success_rate": (self.success_count / total_requests) * 100,
            "blocked_rate": (self.blocked_count / total_requests) * 100,
            "error_rate": (self.error_count / total_requests) * 100
        }
        
        if self.response_times:
            sorted_times = sorted(self.response_times)
            stats.update({
                "response_times": {
                    "avg": statistics.mean(self.response_times),
                    "median": statistics.median(self.response_times),
                    "p95": sorted_times[int(len(sorted_times) * 0.95)],
                    "p99": sorted_times[int(len(sorted_times) * 0.99)],
                }
            })
            
        if self.blocked_times:
            sorted_blocked = sorted(self.blocked_times)
            stats.update({
                "blocked_times": {
                    "avg": statistics.mean(self.blocked_times),
                    "median": statistics.median(self.blocked_times),
                    "p95": sorted_blocked[int(len(sorted_blocked) * 0.95)],
                    "p99": sorted_blocked[int(len(sorted_blocked) * 0.99)],
                }
            })
            
        return stats

async def make_request(client_id: int, results: RateLimitTestResults):
    """Faz uma requisição simulando um cliente específico"""
    async with httpx.AsyncClient() as client:
        try:
            headers = {
                "X-Client-ID": str(client_id),
                "X-Real-IP": f"192.168.1.{client_id % 255}"
            }
            
            start_time = time.time()
            response = await client.get(
                f"{BASE_URL}{TEST_ENDPOINT}",
                headers=headers
            )
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            results.add_result(
                response_time=response_time,
                status_code=response.status_code,
                error_msg=None
            )
            
        except Exception as e:
            results.add_result(
                response_time=0,
                status_code=500,
                error_msg=str(e)
            )

async def run_rate_limit_test() -> Dict:
    results = RateLimitTestResults()
    tasks = []
    
    # Criando grupos de requisições concorrentes
    for batch_start in range(0, NUM_REQUESTS, CONCURRENT_USERS):
        batch_size = min(CONCURRENT_USERS, NUM_REQUESTS - batch_start)
        batch_tasks = [
            make_request(client_id=i + batch_start, results=results)
            for i in range(batch_size)
        ]
        tasks.extend(batch_tasks)
        
        # Executando batch de requisições
        await asyncio.gather(*batch_tasks)
        
        # Pequena pausa entre batches
        await asyncio.sleep(0.05)
    
    return results.get_statistics()

@pytest.mark.asyncio
async def test_rate_limit_load():
    """Teste de carga para validar o rate limiting"""
    print("\nIniciando testes de carga do rate limiting...")
    
    results = await run_rate_limit_test()
    
    # Validando resultados
    assert results["blocked_rate"] > 0, "Nenhuma requisição foi bloqueada pelo rate limit"
    assert results["blocked_rate"] < 50, "Taxa de bloqueio muito alta"
    assert results["error_rate"] < 5, "Taxa de erro muito alta"
    assert results["response_times"]["avg"] < 200, "Tempo médio de resposta muito alto"
    
    print("\nResultados do teste de rate limiting:")
    print(f"Total de Requisições: {results['total_requests']}")
    print(f"Taxa de Sucesso: {results['success_rate']:.2f}%")
    print(f"Taxa de Bloqueio: {results['blocked_rate']:.2f}%")
    print(f"Taxa de Erro: {results['error_rate']:.2f}%")
    print(f"Tempo Médio de Resposta: {results['response_times']['avg']:.2f}ms")
    print(f"P95 Tempo de Resposta: {results['response_times']['p95']:.2f}ms")
    
    if results.get("blocked_times"):
        print(f"Tempo Médio de Bloqueio: {results['blocked_times']['avg']:.2f}ms")
        print(f"P95 Tempo de Bloqueio: {results['blocked_times']['p95']:.2f}ms")
    
    # Salvando resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"load/results/rate_limit_test_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    asyncio.run(test_rate_limit_load()) 