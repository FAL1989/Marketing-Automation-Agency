import pytest
from fastapi import FastAPI
from unittest.mock import Mock, patch
from ...app.monitoring.metrics_exporter import MetricsExporter, metrics_exporter
import logging

@pytest.fixture
def app():
    """
    Fixture que cria uma aplicação FastAPI
    """
    return FastAPI()

@pytest.fixture
def exporter():
    """
    Fixture que cria uma instância do MetricsExporter
    """
    return MetricsExporter()

@patch("prometheus_client.start_http_server")
async def test_metrics_server_start(mock_start_server, app, exporter):
    """
    Testa a inicialização do servidor de métricas
    """
    port = 9090
    await exporter.start(app, port)
    
    # Verifica se o servidor foi iniciado
    mock_start_server.assert_called_once_with(port)
    
    # Verifica se o evento de shutdown foi registrado
    assert any(
        handler.__name__ == "shutdown"
        for handler in app.router.on_shutdown
    )

@patch("prometheus_client.start_http_server")
async def test_metrics_server_start_error(mock_start_server, app, exporter):
    """
    Testa o tratamento de erro na inicialização do servidor
    """
    mock_start_server.side_effect = Exception("Server start failed")
    
    with pytest.raises(Exception) as exc_info:
        await exporter.start(app, 9090)
    assert str(exc_info.value) == "Server start failed"

async def test_metrics_server_shutdown(exporter):
    """
    Testa o desligamento do servidor de métricas
    """
    # Configura um mock para o servidor
    exporter._server = Mock()
    
    await exporter.shutdown()
    
    # Verifica se o método stop foi chamado
    exporter._server.stop.assert_called_once()

def test_get_registry(exporter):
    """
    Testa a obtenção do registro de métricas
    """
    registry = exporter.get_registry()
    assert registry is not None
    
    # Verifica se é o mesmo registro usado pelo Prometheus
    from prometheus_client import REGISTRY
    assert registry == REGISTRY

@patch("prometheus_client.start_http_server")
async def test_metrics_server_port_configuration(mock_start_server, app, exporter):
    """
    Testa a configuração da porta do servidor
    """
    # Testa com porta padrão
    await exporter.start(app)
    mock_start_server.assert_called_with(9090)
    mock_start_server.reset_mock()
    
    # Testa com porta personalizada
    custom_port = 8000
    await exporter.start(app, custom_port)
    mock_start_server.assert_called_with(custom_port)

@patch("logging.Logger.info")
@patch("prometheus_client.start_http_server")
async def test_metrics_server_logging(mock_start_server, mock_log_info, app, exporter):
    """
    Testa o logging do servidor de métricas
    """
    port = 9090
    await exporter.start(app, port)
    
    # Verifica se a mensagem de log foi registrada
    mock_log_info.assert_called_with(f"Metrics server started on port {port}")
    
    # Testa logging no shutdown
    exporter._server = Mock()
    await exporter.shutdown()
    mock_log_info.assert_called_with("Metrics server stopped")

@patch("prometheus_client.start_http_server")
async def test_metrics_server_singleton(mock_start_server, app):
    """
    Testa se o exportador de métricas é um singleton
    """
    # Verifica se a instância global é a mesma
    exporter1 = metrics_exporter
    exporter2 = metrics_exporter
    assert exporter1 is exporter2
    
    # Verifica se o registro é o mesmo
    assert exporter1.get_registry() is exporter2.get_registry()

@patch("prometheus_client.start_http_server")
async def test_metrics_server_multiple_starts(mock_start_server, app, exporter):
    """
    Testa múltiplas inicializações do servidor
    """
    # Primeira inicialização
    await exporter.start(app, 9090)
    assert mock_start_server.call_count == 1
    
    # Segunda inicialização
    await exporter.start(app, 9090)
    assert mock_start_server.call_count == 2  # Deve iniciar novamente
    
    # Verifica se o evento de shutdown foi registrado apenas uma vez
    shutdown_handlers = [
        handler.__name__
        for handler in app.router.on_shutdown
        if handler.__name__ == "shutdown"
    ]
    assert len(shutdown_handlers) == 1 