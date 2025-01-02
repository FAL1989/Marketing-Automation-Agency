import pytest
from unittest.mock import patch, MagicMock
from ..conftest import test_client, test_user
from ...app.core.config import settings
from ...app.core.notifications import NotificationService
from ...app.core.events import EventType

def test_notification_service_init():
    """Testa a inicialização do serviço de notificações"""
    service = NotificationService()
    assert service is not None
    assert hasattr(service, 'send_email')
    assert hasattr(service, 'send_slack')

@patch('app.core.notifications.NotificationService.send_email')
def test_security_event_email(mock_send_email, test_client):
    """Testa o envio de email para eventos de segurança"""
    # Simula uma tentativa de login inválida
    test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrong_password"
        }
    )
    
    # Verifica se o email foi enviado
    mock_send_email.assert_called_once()
    call_args = mock_send_email.call_args[0]
    assert "security alert" in call_args[0].lower()
    assert "login attempt" in call_args[1].lower()

@patch('app.core.notifications.NotificationService.send_slack')
def test_security_event_slack(mock_send_slack, test_client):
    """Testa o envio de notificação Slack para eventos de segurança"""
    # Simula múltiplas tentativas de login
    for _ in range(5):
        test_client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": "wrong@example.com",
                "password": "wrong_password"
            }
        )
    
    # Verifica se a notificação Slack foi enviada
    mock_send_slack.assert_called()
    call_args = mock_send_slack.call_args[0]
    assert "multiple failed login attempts" in call_args[0].lower()

def test_rate_limit_notification(test_client):
    """Testa notificações de rate limit"""
    with patch('app.core.notifications.NotificationService.send_email') as mock_email:
        # Força rate limit
        for _ in range(settings.RATE_LIMIT_PER_SECOND + 1):
            test_client.get("/")
        
        # Verifica notificação
        mock_email.assert_called_once()
        call_args = mock_email.call_args[0]
        assert "rate limit exceeded" in call_args[1].lower()

def test_suspicious_activity_notification(test_client):
    """Testa notificações de atividade suspeita"""
    with patch('app.core.notifications.NotificationService.send_slack') as mock_slack:
        # Simula atividade suspeita (tentativa de SQL injection)
        test_client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": "admin' OR '1'='1",
                "password": "anything"
            }
        )
        
        # Verifica notificação
        mock_slack.assert_called_once()
        call_args = mock_slack.call_args[0]
        assert "suspicious activity" in call_args[0].lower()

def test_notification_throttling():
    """Testa o throttling de notificações"""
    service = NotificationService()
    
    # Tenta enviar múltiplas notificações rapidamente
    with patch('app.core.notifications.NotificationService.send_email') as mock_email:
        for _ in range(10):
            service.notify_security_event(
                EventType.FAILED_LOGIN,
                {"user": "test@example.com"}
            )
        
        # Deve ter menos chamadas que tentativas devido ao throttling
        assert mock_email.call_count < 10

def test_notification_formatting():
    """Testa a formatação das notificações"""
    service = NotificationService()
    
    with patch('app.core.notifications.NotificationService.send_email') as mock_email:
        # Envia notificação com dados complexos
        service.notify_security_event(
            EventType.SUSPICIOUS_ACTIVITY,
            {
                "ip": "1.2.3.4",
                "user_agent": "test-agent",
                "path": "/api/test",
                "method": "POST"
            }
        )
        
        # Verifica formatação
        call_args = mock_email.call_args[0]
        message = call_args[1]
        assert "IP: 1.2.3.4" in message
        assert "User-Agent: test-agent" in message
        assert "Path: /api/test" in message
        assert "Method: POST" in message 