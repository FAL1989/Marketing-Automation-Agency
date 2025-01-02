import pytest
from unittest.mock import Mock, patch
from prometheus_client import REGISTRY
from ...app.monitoring.security_metrics import (
    SecurityMetrics,
    rate_limit_violations,
    suspicious_ip_activity,
    xss_attempts,
    csrf_attempts,
    unauthorized_access,
    request_latency
)

@pytest.fixture
def security_metrics():
    """
    Fixture que cria uma instância do SecurityMetrics
    """
    return SecurityMetrics()

def test_rate_limit_violation_recording(security_metrics):
    """
    Testa o registro de violações de rate limit
    """
    # Obtém o valor inicial do contador
    initial_value = rate_limit_violations.labels(path="/test", ip="1.1.1.1")._value.get()
    
    # Registra uma violação
    security_metrics.record_rate_limit_violation(path="/test", ip="1.1.1.1")
    
    # Verifica se o contador foi incrementado
    final_value = rate_limit_violations.labels(path="/test", ip="1.1.1.1")._value.get()
    assert final_value == initial_value + 1

def test_suspicious_ip_activity_recording(security_metrics):
    """
    Testa o registro de atividades suspeitas de IP
    """
    # Obtém o valor inicial do contador
    initial_value = suspicious_ip_activity.labels(
        ip="1.1.1.1",
        activity_type="brute_force"
    )._value.get()
    
    # Registra uma atividade suspeita
    security_metrics.record_suspicious_ip_activity(
        ip="1.1.1.1",
        activity_type="brute_force"
    )
    
    # Verifica se o contador foi incrementado
    final_value = suspicious_ip_activity.labels(
        ip="1.1.1.1",
        activity_type="brute_force"
    )._value.get()
    assert final_value == initial_value + 1

def test_xss_attempt_recording(security_metrics):
    """
    Testa o registro de tentativas de XSS
    """
    # Obtém o valor inicial do contador
    initial_value = xss_attempts.labels(path="/test", ip="1.1.1.1")._value.get()
    
    # Registra uma tentativa de XSS
    security_metrics.record_xss_attempt(path="/test", ip="1.1.1.1")
    
    # Verifica se o contador foi incrementado
    final_value = xss_attempts.labels(path="/test", ip="1.1.1.1")._value.get()
    assert final_value == initial_value + 1

def test_csrf_attempt_recording(security_metrics):
    """
    Testa o registro de tentativas de CSRF
    """
    # Obtém o valor inicial do contador
    initial_value = csrf_attempts.labels(path="/test", ip="1.1.1.1")._value.get()
    
    # Registra uma tentativa de CSRF
    security_metrics.record_csrf_attempt(path="/test", ip="1.1.1.1")
    
    # Verifica se o contador foi incrementado
    final_value = csrf_attempts.labels(path="/test", ip="1.1.1.1")._value.get()
    assert final_value == initial_value + 1

def test_unauthorized_access_recording(security_metrics):
    """
    Testa o registro de tentativas de acesso não autorizado
    """
    # Obtém o valor inicial do contador
    initial_value = unauthorized_access.labels(
        path="/test",
        ip="1.1.1.1",
        method="GET"
    )._value.get()
    
    # Registra uma tentativa de acesso não autorizado
    security_metrics.record_unauthorized_access(
        path="/test",
        ip="1.1.1.1",
        method="GET"
    )
    
    # Verifica se o contador foi incrementado
    final_value = unauthorized_access.labels(
        path="/test",
        ip="1.1.1.1",
        method="GET"
    )._value.get()
    assert final_value == initial_value + 1

def test_request_latency_recording(security_metrics):
    """
    Testa o registro de latência das requisições
    """
    # Inicia o timer
    timer = security_metrics.start_request_timer()
    assert "start_time" in timer
    
    # Registra a latência
    security_metrics.record_request_latency(
        path="/test",
        method="GET",
        start_time=timer["start_time"]
    )
    
    # Verifica se o histograma foi atualizado
    histogram = request_latency.labels(path="/test", method="GET")
    assert histogram._sum.get() > 0
    assert histogram._count.get() > 0

def test_metrics_registration():
    """
    Testa se todas as métricas estão registradas no REGISTRY
    """
    metrics = [
        "rate_limit_violations_total",
        "suspicious_ip_activity_total",
        "xss_attempts_total",
        "csrf_attempts_total",
        "unauthorized_access_total",
        "request_latency_seconds"
    ]
    
    for metric in metrics:
        assert any(
            metric in str(collector)
            for collector in REGISTRY.collect()
        )

def test_metrics_labels():
    """
    Testa se as métricas têm os labels corretos
    """
    # Rate limit violations
    assert set(rate_limit_violations._labelnames) == {"path", "ip"}
    
    # Suspicious IP activity
    assert set(suspicious_ip_activity._labelnames) == {"ip", "activity_type"}
    
    # XSS attempts
    assert set(xss_attempts._labelnames) == {"path", "ip"}
    
    # CSRF attempts
    assert set(csrf_attempts._labelnames) == {"path", "ip"}
    
    # Unauthorized access
    assert set(unauthorized_access._labelnames) == {"path", "ip", "method"}
    
    # Request latency
    assert set(request_latency._labelnames) == {"path", "method"} 