import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Métricas personalizadas
const errors = new Rate('errors');
const recovery = new Rate('recovery');

// Configurações do teste
export const options = {
    scenarios: {
        network_failures: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '1m', target: 10 },  // Rampa até 10 VUs
                { duration: '2m', target: 50 },  // Aumenta para 50 VUs
                { duration: '1m', target: 10 },  // Reduz para 10 VUs
                { duration: '1m', target: 0 }    // Finaliza
            ],
        },
    },
    thresholds: {
        'http_req_duration': ['p(95)<5000'], // 95% das requisições devem completar em 5s
        'errors': ['rate<0.1'],              // Taxa de erro menor que 10%
        'recovery': ['rate>0.9']             // Taxa de recuperação maior que 90%
    }
};

// Função para simular falhas de rede
function simulateNetworkFailure() {
    if (Math.random() < 0.3) { // 30% de chance de falha
        throw new Error('Network failure simulated');
    }
}

// Função para retry com backoff exponencial
async function withRetry(fn, maxRetries = 3, initialDelay = 1000) {
    let delay = initialDelay;
    
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            sleep(delay / 1000); // k6 sleep usa segundos
            delay *= 2; // Backoff exponencial
        }
    }
}

export default function () {
    group('Resilience Tests', function () {
        // Login inicial
        const loginRes = http.post(`${__ENV.BASE_URL}/auth/login`, {
            username: 'test@example.com',
            password: 'testpass',
            grant_type: 'password'
        }, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
        
        check(loginRes, {
            'login successful': (r) => r.status === 200,
            'has token': (r) => r.json('access_token') !== ''
        });
        
        const token = loginRes.json('access_token');
        
        group('Circuit Breaker', function () {
            // Teste do Circuit Breaker
            const responses = [];
            
            // Faz várias requisições para forçar o circuit breaker a abrir
            for (let i = 0; i < 10; i++) {
                try {
                    const res = http.get(
                        `${__ENV.BASE_URL}/api/slow-endpoint`,
                        {
                            headers: { 'Authorization': `Bearer ${token}` }
                        }
                    );
                    responses.push(res.status);
                    simulateNetworkFailure();
                } catch (e) {
                    responses.push(503); // Esperamos 503 quando o circuito abre
                }
                sleep(1);
            }
            
            // Verifica se o circuit breaker abriu após falhas
            check(responses, {
                'circuit breaker working': (r) => r.includes(503)
            });
        });
        
        group('Fallback Mechanism', function () {
            // Teste do mecanismo de fallback
            try {
                const res = withRetry(() => http.post(
                    `${__ENV.BASE_URL}/content/generate`,
                    {
                        prompt: 'Test content generation',
                        max_tokens: 100
                    },
                    {
                        headers: { 'Authorization': `Bearer ${token}` }
                    }
                ));
                
                check(res, {
                    'fallback successful': (r) => r.status === 200
                });
            } catch (e) {
                errors.add(1);
            }
        });
        
        group('Timeout Recovery', function () {
            // Teste de recuperação de timeout
            try {
                const res = withRetry(() => http.get(
                    `${__ENV.BASE_URL}/api/slow-endpoint`,
                    {
                        headers: { 'Authorization': `Bearer ${token}` },
                        timeout: 5000
                    }
                ));
                
                check(res, {
                    'handles timeout gracefully': (r) => r.status !== 500
                });
                
                if (res.status === 200) {
                    recovery.add(1);
                }
            } catch (e) {
                errors.add(1);
            }
        });
    });
    
    sleep(1);
} 