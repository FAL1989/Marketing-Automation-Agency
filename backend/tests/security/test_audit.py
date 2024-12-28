import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from fastapi import Request
from backend.app.core.audit import AuditLogger, audit_logger
from sqlalchemy.orm import Session

@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.client.host = "127.0.0.1"
    request.method = "GET"
    request.url.path = "/api/resource"
    request.headers = {
        "user-agent": "test-agent",
        "referer": "http://test.com"
    }
    return request

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.query = MagicMock()
    return db

@pytest.mark.asyncio
async def test_log_event_basic(mock_db):
    """Testa o registro básico de eventos"""
    await audit_logger.log_event(
        event_type="auth.login.success",
        user_id=1,
        details={"ip": "127.0.0.1"},
        db=mock_db
    )
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_log_event_with_request(mock_db, mock_request):
    """Testa o registro de eventos com detalhes da requisição"""
    await audit_logger.log_event(
        event_type="auth.access",
        user_id=1,
        request=mock_request,
        db=mock_db
    )
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_events_with_filters(mock_db):
    """Testa a consulta de eventos com diferentes filtros"""
    await audit_logger.get_events(
        db=mock_db,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
        event_type="auth.login",
        user_id=1
    )
    mock_db.query.assert_called_once()

@pytest.mark.asyncio
async def test_cleanup_old_events(mock_db):
    """Testa a limpeza de eventos antigos"""
    await audit_logger.cleanup_old_events(db=mock_db, days=90)
    mock_db.query.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_export_events(mock_db):
    """Testa a exportação de eventos"""
    mock_db.query.return_value.all.return_value = []
    
    # Testa exportação JSON
    json_data = await audit_logger.export_events(
        db=mock_db,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
        format="json"
    )
    assert isinstance(json_data, str)
    
    # Testa exportação CSV
    csv_data = await audit_logger.export_events(
        db=mock_db,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
        format="csv"
    )
    assert isinstance(csv_data, str)
    
    # Testa formato inválido
    with pytest.raises(ValueError):
        await audit_logger.export_events(
            db=mock_db,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            format="invalid"
        ) 