import pytest
from backend.app.core.monitoring import REGISTRY
from backend.app.core import monitoring

def test_failed_login_metrics():
    """Testa métricas de login falho"""
    username = "test_user"
    initial_value = REGISTRY.get_sample_value(
        'failed_login_attempts_total',
        {'username': username}
    ) or 0
    
    monitoring.track_failed_login(username)
    
    final_value = REGISTRY.get_sample_value(
        'failed_login_attempts_total',
        {'username': username}
    ) or 0
    assert final_value == initial_value + 1

def test_active_sessions_metrics():
    """Testa métricas de sessões ativas"""
    username = "test_user"
    initial_value = REGISTRY.get_sample_value(
        'active_sessions',
        {'username': username}
    ) or 0
    
    monitoring.track_successful_login(username)
    
    after_login = REGISTRY.get_sample_value(
        'active_sessions',
        {'username': username}
    ) or 0
    assert after_login == initial_value + 1
    
    monitoring.track_logout(username)
    
    after_logout = REGISTRY.get_sample_value(
        'active_sessions',
        {'username': username}
    ) or 0
    assert after_logout == initial_value

def test_suspicious_patterns():
    """Testa métricas de padrões suspeitos"""
    pattern_type = "sql_injection"
    username = "test_user"
    initial_value = REGISTRY.get_sample_value(
        'suspicious_patterns_total',
        {'pattern_type': pattern_type, 'username': username}
    ) or 0
    
    monitoring.track_suspicious_pattern(pattern_type, username)
    
    final_value = REGISTRY.get_sample_value(
        'suspicious_patterns_total',
        {'pattern_type': pattern_type, 'username': username}
    ) or 0
    assert final_value == initial_value + 1

def test_request_latency():
    """Testa métricas de latência"""
    endpoint = "/test"
    duration = 0.5
    
    # Obtém o valor inicial do contador de observações
    initial_count = REGISTRY.get_sample_value(
        'request_latency_seconds_count',
        {'endpoint': endpoint}
    ) or 0
    
    monitoring.track_request_latency(endpoint, duration)
    
    # Verifica se o contador de observações aumentou
    final_count = REGISTRY.get_sample_value(
        'request_latency_seconds_count',
        {'endpoint': endpoint}
    ) or 0
    assert final_count == initial_count + 1
    
    # Verifica se a soma das observações aumentou
    sum_value = REGISTRY.get_sample_value(
        'request_latency_seconds_sum',
        {'endpoint': endpoint}
    ) or 0
    assert sum_value >= duration 