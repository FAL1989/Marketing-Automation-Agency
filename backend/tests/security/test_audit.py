import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.audit import audit_logger
from app.models.user import User
from app.core.security import get_password_hash
from app.db.session import engine

@pytest.mark.asyncio
async def test_audit_log_request(test_client: AsyncClient):
    """
    Testa o registro de log de auditoria para uma requisição
    """
    response = await test_client.get("/api/v1/users/me")
    assert response.status_code in [401, 403]  # Deve falhar sem autenticação
    
    # Verificar se o log foi registrado
    with open(audit_logger.file_handler.baseFilename, "r") as f:
        logs = f.readlines()
        assert len(logs) > 0
        last_log = logs[-1]
        assert "GET" in last_log
        assert "/api/v1/users/me" in last_log

@pytest.mark.asyncio
async def test_audit_log_security_event(test_user: User):
    """
    Testa o registro de eventos de segurança
    """
    event_type = "login_attempt"
    user_id = str(test_user.id)
    details = {"ip": "127.0.0.1", "success": True}
    
    audit_logger.log_security_event(event_type, user_id, details)
    
    # Verificar se o log foi registrado
    with open(audit_logger.file_handler.baseFilename, "r") as f:
        logs = f.readlines()
        assert len(logs) > 0
        last_log = logs[-1]
        assert event_type in last_log
        assert user_id in last_log 