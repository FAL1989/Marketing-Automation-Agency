import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.core.notifications import NotificationManager
import json
import aiohttp
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@pytest.fixture
def notification_manager():
    """Fixture para criar uma instância do NotificationManager"""
    return NotificationManager()

@pytest.fixture
def sample_events():
    """Fixture para criar eventos de exemplo"""
    return [
        {
            "event_id": "test1",
            "timestamp": datetime.utcnow(),
            "event_type": "security.violation",
            "severity": "critical",
            "message": "Tentativa de acesso não autorizado",
            "details": {
                "ip": "192.168.1.1",
                "user_agent": "test-agent",
                "path": "/api/secure"
            }
        },
        {
            "event_id": "test2",
            "timestamp": datetime.utcnow(),
            "event_type": "system.error",
            "severity": "critical",
            "message": "Erro crítico no sistema",
            "details": {
                "component": "database",
                "error": "Connection timeout"
            }
        }
    ]

@pytest.mark.asyncio
async def test_notify_critical_events(notification_manager, sample_events):
    """Testa o envio de notificações para eventos críticos"""
    # Mock das funções de notificação
    notification_manager._send_slack_notification = AsyncMock()
    notification_manager._send_email_notification = AsyncMock()
    
    # Executa a notificação
    await notification_manager.notify_critical_events(sample_events)
    
    # Verifica se as funções foram chamadas
    notification_manager._send_slack_notification.assert_called_once_with(sample_events)
    notification_manager._send_email_notification.assert_called_once_with(sample_events)

@pytest.mark.asyncio
async def test_slack_notification(notification_manager, sample_events):
    """Testa o envio de notificações para o Slack"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        await notification_manager._send_slack_notification(sample_events)
        
        # Verifica se a chamada foi feita corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        
        # Verifica o formato da mensagem
        message = call_args["json"]
        assert "blocks" in message
        blocks = message["blocks"]
        
        # Verifica o cabeçalho
        assert blocks[0]["type"] == "header"
        assert "🚨" in blocks[0]["text"]["text"]
        assert str(len(sample_events)) in blocks[0]["text"]["text"]
        
        # Verifica os detalhes dos eventos
        event_blocks = [b for b in blocks if b.get("type") == "section"]
        assert len(event_blocks) > 0
        
        # Verifica se os campos importantes estão presentes
        for event in sample_events:
            event_text = str(message)
            assert event["event_id"] in event_text
            assert event["event_type"] in event_text
            assert event["message"] in event_text

@pytest.mark.asyncio
async def test_email_notification(notification_manager, sample_events):
    """Testa o envio de notificações por email"""
    with patch("aiosmtplib.send") as mock_send:
        await notification_manager._send_email_notification(sample_events)
        
        # Verifica se o email foi enviado
        mock_send.assert_called_once()
        
        # Verifica o formato do email
        call_args = mock_send.call_args[1]
        assert "hostname" in call_args
        assert "port" in call_args
        assert "username" in call_args
        assert "password" in call_args
        assert "use_tls" in call_args

def test_format_slack_message(notification_manager, sample_events):
    """Testa a formatação de mensagens para o Slack"""
    blocks = notification_manager._format_slack_message(sample_events)
    
    # Verifica a estrutura básica
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    
    # Verifica o cabeçalho
    header = blocks[0]
    assert header["type"] == "header"
    assert "text" in header
    assert str(len(sample_events)) in header["text"]["text"]
    
    # Verifica o resumo
    summary = blocks[1]
    assert summary["type"] == "section"
    assert "Período" in summary["text"]["text"]
    assert "Total de Eventos" in summary["text"]["text"]
    
    # Verifica os eventos
    event_blocks = []
    for block in blocks:
        if block["type"] == "section" and "fields" in block:
            event_blocks.append(block)
            
    assert len(event_blocks) >= len(sample_events)

def test_format_email_message(notification_manager, sample_events):
    """Testa a formatação de mensagens de email"""
    msg = notification_manager._format_email_message(sample_events)
    
    # Verifica o tipo da mensagem
    assert isinstance(msg, MIMEMultipart)
    
    # Verifica os cabeçalhos
    assert "[AUDITORIA]" in msg["Subject"]
    assert str(len(sample_events)) in msg["Subject"]
    assert msg["To"] == notification_manager.alert_email
    
    # Verifica o corpo
    body = msg.get_payload()[0].get_payload()
    assert isinstance(body, str)
    
    # Verifica o conteúdo
    assert "EVENTOS CRÍTICOS DE AUDITORIA" in body
    assert "RESUMO" in body
    assert "DETALHES DOS EVENTOS" in body
    
    # Verifica se os eventos estão incluídos
    for event in sample_events:
        assert event["event_id"] in body
        assert event["event_type"] in body
        assert event["message"] in body

def test_format_time_range(notification_manager, sample_events):
    """Testa a formatação do intervalo de tempo"""
    time_range = notification_manager._format_time_range(sample_events)
    
    # Verifica o formato
    assert isinstance(time_range, str)
    assert "até" in time_range
    
    # Verifica se as datas são válidas
    start, end = time_range.split(" até ")
    assert datetime.strptime(start.strip(), "%Y-%m-%d %H:%M:%S")
    assert datetime.strptime(end.strip(), "%Y-%m-%d %H:%M:%S")

def test_format_details(notification_manager):
    """Testa a formatação de detalhes dos eventos"""
    # Testa com detalhes vazios
    empty_details = notification_manager._format_details({})
    assert empty_details == "Nenhum detalhe adicional"
    
    # Testa com detalhes simples
    details = {
        "ip": "192.168.1.1",
        "user": "test_user",
        "action": "login"
    }
    formatted = notification_manager._format_details(details)
    
    # Verifica se todas as chaves e valores estão presentes
    for key, value in details.items():
        assert f"{key}: {value}" in formatted
        
    # Verifica se está formatado corretamente
    lines = formatted.split("\n")
    assert len(lines) == len(details)

@pytest.mark.asyncio
async def test_error_handling(notification_manager, sample_events):
    """Testa o tratamento de erros nas notificações"""
    # Simula erro no Slack
    with patch("aiohttp.ClientSession.post", side_effect=Exception("Slack Error")):
        # Não deve lançar exceção
        await notification_manager.notify_critical_events(sample_events)
        
    # Simula erro no email
    with patch("aiosmtplib.send", side_effect=Exception("Email Error")):
        # Não deve lançar exceção
        await notification_manager.notify_critical_events(sample_events)

@pytest.mark.asyncio
async def test_empty_events(notification_manager):
    """Testa o comportamento com lista vazia de eventos"""
    # Mock das funções de notificação
    notification_manager._send_slack_notification = AsyncMock()
    notification_manager._send_email_notification = AsyncMock()
    
    # Tenta notificar sem eventos
    await notification_manager.notify_critical_events([])
    
    # Verifica se nenhuma notificação foi enviada
    notification_manager._send_slack_notification.assert_not_called()
    notification_manager._send_email_notification.assert_not_called()

@pytest.mark.asyncio
async def test_notification_rate_limiting(notification_manager, sample_events):
    """Testa o rate limiting das notificações"""
    # Simula múltiplas chamadas rápidas
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 429  # Too Many Requests
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Tenta enviar várias notificações
        for _ in range(5):
            await notification_manager._send_slack_notification(sample_events)
            
        # Verifica se todas as tentativas foram feitas
        assert mock_post.call_count == 5 