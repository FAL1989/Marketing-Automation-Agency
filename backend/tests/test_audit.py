import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.events import EventType
from app.models.audit import AuditLog
from app.core.audit import audit_logger

@pytest.fixture
def sample_logs(db: Session):
    """Cria logs de exemplo para testes"""
    logs = [
        AuditLog(
            event_type=EventType.LOGIN_SUCCESS.value,
            user_id=1,
            ip_address="192.168.1.1",
            severity="info",
            details={"browser": "Chrome"}
        ),
        AuditLog(
            event_type=EventType.ACCESS_DENIED.value,
            user_id=2,
            ip_address="192.168.1.2",
            severity="warning",
            details={"reason": "unauthorized"}
        ),
        AuditLog(
            event_type=EventType.SUSPICIOUS_ACTIVITY.value,
            ip_address="192.168.1.3",
            severity="critical",
            details={"type": "xss_attempt"}
        )
    ]
    
    for log in logs:
        db.add(log)
    db.commit()
    
    return logs

def test_create_audit_log(db: Session):
    """Testa criação de log de auditoria"""
    log = AuditLog(
        event_type=EventType.LOGIN_SUCCESS.value,
        user_id=1,
        ip_address="192.168.1.1",
        severity="info"
    )
    db.add(log)
    db.commit()
    
    assert log.id is not None
    assert log.timestamp is not None
    assert log.event_type == EventType.LOGIN_SUCCESS.value

def test_get_audit_logs(client: TestClient, sample_logs, superuser_token_headers):
    """Testa listagem de logs de auditoria"""
    response = client.get("/api/v1/audit/logs", headers=superuser_token_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    assert data[0]["event_type"] == EventType.LOGIN_SUCCESS.value

def test_get_audit_logs_with_filters(client: TestClient, sample_logs, superuser_token_headers):
    """Testa filtros na listagem de logs"""
    # Filtro por tipo de evento
    response = client.get(
        "/api/v1/audit/logs?event_types=LOGIN_SUCCESS",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["event_type"] == EventType.LOGIN_SUCCESS.value
    
    # Filtro por severidade
    response = client.get(
        "/api/v1/audit/logs?severity=critical",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["severity"] == "critical"

def test_get_audit_statistics(client: TestClient, sample_logs, superuser_token_headers):
    """Testa estatísticas dos logs"""
    response = client.get("/api/v1/audit/statistics", headers=superuser_token_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "events_by_type" in data
    assert "events_by_severity" in data
    assert "top_ips" in data
    
    assert data["events_by_type"][EventType.LOGIN_SUCCESS.value] == 1
    assert data["events_by_severity"]["critical"] == 1

def test_export_audit_logs(client: TestClient, sample_logs, superuser_token_headers):
    """Testa exportação de logs"""
    # Exportação CSV
    response = client.get(
        "/api/v1/audit/export?format=csv",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    
    # Exportação JSON
    response = client.get(
        "/api/v1/audit/export?format=json",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

def test_get_user_recent_activity(client: TestClient, sample_logs, superuser_token_headers):
    """Testa busca de atividade recente do usuário"""
    response = client.get(
        "/api/v1/audit/recent-activity/1",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == 1

def test_get_security_events(client: TestClient, sample_logs, superuser_token_headers):
    """Testa busca de eventos de segurança"""
    response = client.get(
        "/api/v1/audit/security-events",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2  # ACCESS_DENIED e SUSPICIOUS_ACTIVITY
    assert any(log["severity"] == "critical" for log in data)

def test_audit_logger_integration(db: Session):
    """Testa integração do logger de auditoria"""
    # Log de evento de segurança
    audit_logger.log_security_event(
        db=db,
        event_type=EventType.SUSPICIOUS_ACTIVITY,
        request_info={
            "ip": "192.168.1.4",
            "path": "/api/test",
            "method": "POST",
            "user_agent": "test-agent"
        },
        severity="warning"
    )
    
    # Verifica se o log foi criado
    log = db.query(AuditLog).filter_by(
        event_type=EventType.SUSPICIOUS_ACTIVITY.value,
        ip_address="192.168.1.4"
    ).first()
    
    assert log is not None
    assert log.severity == "warning"
    assert "test-agent" in log.details["user_agent"]

def test_audit_log_retention(db: Session, sample_logs):
    """Testa retenção de logs"""
    # Cria um log antigo
    old_log = AuditLog(
        event_type=EventType.LOGIN_SUCCESS.value,
        timestamp=datetime.utcnow() - timedelta(days=100),
        user_id=1
    )
    db.add(old_log)
    db.commit()
    
    # Verifica se o log antigo é excluído da consulta padrão
    logs = AuditLog.get_by_filters(
        db=db,
        start_date=datetime.utcnow() - timedelta(days=30)
    )
    
    assert old_log not in logs
    assert len(logs) == len(sample_logs)

def test_audit_log_search(db: Session, sample_logs):
    """Testa busca em logs"""
    # Busca por IP
    logs = AuditLog.get_by_filters(db=db, ip_address="192.168.1.1")
    assert len(logs) == 1
    assert logs[0].ip_address == "192.168.1.1"
    
    # Busca por severidade
    logs = AuditLog.get_by_filters(db=db, severity="critical")
    assert len(logs) == 1
    assert logs[0].severity == "critical"
    
    # Busca por tipo de evento
    logs = AuditLog.get_by_filters(
        db=db,
        event_types=[EventType.LOGIN_SUCCESS.value]
    )
    assert len(logs) == 1
    assert logs[0].event_type == EventType.LOGIN_SUCCESS.value 