from prometheus_client import Counter, Gauge, Histogram
from prometheus_client.registry import CollectorRegistry
from typing import Dict
import time
from ..core.config import settings

# Cria um registro personalizado para métricas de segurança
security_registry = CollectorRegistry()

# Métricas de rate limit
rate_limit_violations = Counter(
    'rate_limit_violations',
    'Número de violações de rate limit',
    ['path', 'ip'],
    registry=security_registry
)

# Métricas de atividade suspeita
suspicious_ip_activity = Counter(
    'suspicious_ip_activity',
    'Número de atividades suspeitas por IP',
    ['ip', 'activity_type'],
    registry=security_registry
)

# Métricas de tentativas de XSS
xss_attempts = Counter(
    'xss_attempts',
    'Número de tentativas de XSS',
    ['path', 'ip'],
    registry=security_registry
)

# Métricas de tentativas de CSRF
csrf_attempts = Counter(
    'csrf_attempts',
    'Número de tentativas de CSRF',
    ['path', 'ip'],
    registry=security_registry
)

# Métricas de acesso não autorizado
unauthorized_access = Counter(
    'unauthorized_access',
    'Número de tentativas de acesso não autorizado',
    ['path', 'ip', 'method'],
    registry=security_registry
)

# Métricas de latência de requisição
request_latency = Histogram(
    'request_latency_seconds',
    'Latência das requisições',
    ['path', 'method'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=security_registry
)

# Métricas de autenticação
auth_failures = Counter(
    'auth_failures',
    'Número de falhas de autenticação',
    ['reason'],
    registry=security_registry
)

mfa_failures = Counter(
    'mfa_failures',
    'Número de falhas de autenticação MFA',
    registry=security_registry
)

active_sessions = Gauge(
    'active_sessions',
    'Número de sessões ativas',
    registry=security_registry
)

# Métricas de performance de autenticação
auth_latency = Histogram(
    'auth_latency_seconds',
    'Latência das operações de autenticação',
    ['operation'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=security_registry
)

# Métricas de bloqueio de conta
account_lockouts = Counter(
    'account_lockouts',
    'Número de contas bloqueadas',
    registry=security_registry
)

# Métricas de tentativas de força bruta
brute_force_attempts = Counter(
    'brute_force_attempts',
    'Número de tentativas suspeitas de força bruta',
    registry=security_registry
)

# Métricas de sessão
session_duration = Histogram(
    'session_duration_seconds',
    'Duração das sessões de usuário',
    buckets=(300, 900, 1800, 3600, 7200, 14400),
    registry=security_registry
)

# Métricas de token
token_validations = Counter(
    'token_validations',
    'Número de validações de token',
    ['result'],
    registry=security_registry
)

# Métricas de circuit breaker
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Estado atual do circuit breaker (0=closed, 1=half-open, 2=open)',
    registry=security_registry
)

circuit_breaker_failures = Counter(
    'circuit_breaker_failures',
    'Número de falhas registradas pelo circuit breaker',
    registry=security_registry
)

class SecurityMetrics:
    """
    Classe que encapsula as métricas de segurança e fornece métodos para registrá-las
    """
    
    @staticmethod
    def record_rate_limit_violation(path: str, ip: str):
        """Registra uma violação de rate limit"""
        rate_limit_violations.labels(path=path, ip=ip).inc()
    
    @staticmethod
    def record_suspicious_ip_activity(ip: str, activity_type: str):
        """Registra uma atividade suspeita de um IP"""
        suspicious_ip_activity.labels(ip=ip, activity_type=activity_type).inc()
    
    @staticmethod
    def record_xss_attempt(path: str, ip: str):
        """Registra uma tentativa de XSS"""
        xss_attempts.labels(path=path, ip=ip).inc()
    
    @staticmethod
    def record_csrf_attempt(path: str, ip: str):
        """Registra uma tentativa de CSRF"""
        csrf_attempts.labels(path=path, ip=ip).inc()
    
    @staticmethod
    def record_unauthorized_access(path: str, ip: str, method: str):
        """Registra uma tentativa de acesso não autorizado"""
        unauthorized_access.labels(path=path, ip=ip, method=method).inc()
    
    @staticmethod
    def start_request_timer() -> Dict[str, float]:
        """Inicia um timer para medir a latência da requisição"""
        return {'start_time': time.time()}
    
    @staticmethod
    def record_request_latency(path: str, method: str, start_time: float):
        """Registra a latência de uma requisição"""
        request_latency.labels(path=path, method=method).observe(time.time() - start_time)
    
    @staticmethod
    def record_auth_failure(reason: str):
        """Registra uma falha de autenticação"""
        auth_failures.labels(reason=reason).inc()
    
    @staticmethod
    def record_mfa_failure():
        """Registra uma falha de autenticação MFA"""
        mfa_failures.inc()
    
    @staticmethod
    def update_active_sessions(count: int):
        """Atualiza o contador de sessões ativas"""
        active_sessions.set(count)
    
    @staticmethod
    def start_auth_timer() -> Dict[str, float]:
        """Inicia um timer para medir a latência de autenticação"""
        return {'start_time': time.time()}
    
    @staticmethod
    def record_auth_latency(operation: str, start_time: float):
        """Registra a latência de uma operação de autenticação"""
        auth_latency.labels(operation=operation).observe(time.time() - start_time)
    
    @staticmethod
    def record_account_lockout():
        """Registra um bloqueio de conta"""
        account_lockouts.inc()
    
    @staticmethod
    def record_brute_force_attempt():
        """Registra uma tentativa suspeita de força bruta"""
        brute_force_attempts.inc()
    
    @staticmethod
    def record_session_duration(duration: float):
        """Registra a duração de uma sessão"""
        session_duration.observe(duration)
    
    @staticmethod
    def record_token_validation(result: str):
        """Registra uma validação de token"""
        token_validations.labels(result=result).inc()
    
    @staticmethod
    def update_circuit_breaker_state(state: str):
        """Atualiza o estado do circuit breaker"""
        state_map = {'closed': 0, 'half-open': 1, 'open': 2}
        circuit_breaker_state.set(state_map[state])
    
    @staticmethod
    def record_circuit_breaker_failure():
        """Registra uma falha no circuit breaker"""
        circuit_breaker_failures.inc() 