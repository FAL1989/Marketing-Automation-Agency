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
NUM_REQUESTS = 500  # Número total de requisições
CONCURRENT_USERS = 25  # Número de usuários simultâneos

class MFALoadTestResults:
    def __init__(self):
        self.setup_times: List[float] = []
        self.verify_times: List[float] = []
        self.errors: List[str] = []
        self.success_count: int = 0
        self.error_count: int = 0

    def add_result(self, setup_time: float, verify_time: float, success: bool, error_msg: str = None):
        if setup_time > 0:
            self.setup_times.append(setup_time)
        if verify_time > 0:
            self.verify_times.append(verify_time)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            self.errors.append(error_msg)

    def get_statistics(self) -> Dict:
        total_requests = self.success_count + self.error_count
        
        stats = {
            "total_requests": total_requests,
            "success_rate": (self.success_count / total_requests * 100) if total_requests > 0 else 0,
            "error_rate": (self.error_count / total_requests * 100) if total_requests > 0 else 0,
        }
        
        if self.setup_times:
            stats.update({
                "setup_time": {
                    "avg": statistics.mean(self.setup_times),
                    "median": statistics.median(self.setup_times),
                    "p95": sorted(self.setup_times)[int(len(self.setup_times) * 0.95)],
                    "p99": sorted(self.setup_times)[int(len(self.setup_times) * 0.99)],
                }
            })
            
        if self.verify_times:
            stats.update({
                "verify_time": {
                    "avg": statistics.mean(self.verify_times),
                    "median": statistics.median(self.verify_times),
                    "p95": sorted(self.verify_times)[int(len(self.verify_times) * 0.95)],
                    "p99": sorted(self.verify_times)[int(len(self.verify_times) * 0.99)],
                }
            })
            
        return stats

async def simulate_mfa_flow(user_id: int, results: MFALoadTestResults):
    """Simula o fluxo completo de MFA para um usuário"""
    async with httpx.AsyncClient() as client:
        try:
            # Setup MFA
            setup_start = time.time()
            setup_response = await client.post(
                f"{BASE_URL}/api/v1/auth/mfa/setup",
                json={"user_id": user_id}
            )
            setup_time = (time.time() - setup_start) * 1000
            
            if setup_response.status_code != 200:
                results.add_result(
                    setup_time=setup_time,
                    verify_time=0,
                    success=False,
                    error_msg=f"Setup falhou: {setup_response.status_code}"
                )
                return
            
            setup_data = setup_response.json()
            mfa_token = setup_data.get("mfa_token")
            
            # Verify MFA
            verify_start = time.time()
            verify_response = await client.post(
                f"{BASE_URL}/api/v1/auth/mfa/verify",
                json={
                    "user_id": user_id,
                    "mfa_token": mfa_token,
                    "code": "123456"  # Código simulado
                }
            )
            verify_time = (time.time() - verify_start) * 1000
            
            success = verify_response.status_code == 200
            results.add_result(
                setup_time=setup_time,
                verify_time=verify_time,
                success=success,
                error_msg=None if success else f"Verify falhou: {verify_response.status_code}"
            )
            
        except Exception as e:
            results.add_result(
                setup_time=0,
                verify_time=0,
                success=False,
                error_msg=str(e)
            )

async def run_mfa_load_test() -> Dict:
    results = MFALoadTestResults()
    tasks = []
    
    # Criando grupos de requisições concorrentes
    for batch_start in range(0, NUM_REQUESTS, CONCURRENT_USERS):
        batch_size = min(CONCURRENT_USERS, NUM_REQUESTS - batch_start)
        batch_tasks = [
            simulate_mfa_flow(user_id=i + batch_start, results=results)
            for i in range(batch_size)
        ]
        tasks.extend(batch_tasks)
        
        # Executando batch de requisições
        await asyncio.gather(*batch_tasks)
        
        # Pequena pausa entre batches para não sobrecarregar
        await asyncio.sleep(0.1)
    
    return results.get_statistics()

@pytest.mark.asyncio
async def test_mfa_load():
    """Teste de carga para o fluxo de MFA"""
    print("\nIniciando testes de carga do MFA...")
    
    results = await run_mfa_load_test()
    
    # Validando resultados
    assert results["success_rate"] >= 95, "Taxa de sucesso do MFA muito baixa"
    assert results["setup_time"]["avg"] < 300, "Tempo médio de setup muito alto"
    assert results["verify_time"]["avg"] < 200, "Tempo médio de verificação muito alto"
    assert results["setup_time"]["p95"] < 500, "P95 do setup muito alto"
    assert results["verify_time"]["p95"] < 400, "P95 da verificação muito alto"
    
    print("\nResultados do teste de carga MFA:")
    print(f"Taxa de Sucesso: {results['success_rate']:.2f}%")
    print(f"Tempo Médio de Setup: {results['setup_time']['avg']:.2f}ms")
    print(f"Tempo Médio de Verificação: {results['verify_time']['avg']:.2f}ms")
    print(f"P95 Setup: {results['setup_time']['p95']:.2f}ms")
    print(f"P95 Verificação: {results['verify_time']['p95']:.2f}ms")
    
    # Salvando resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"load/results/mfa_load_test_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    asyncio.run(test_mfa_load()) 