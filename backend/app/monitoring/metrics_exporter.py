from prometheus_client import start_http_server, REGISTRY
from prometheus_client.core import CollectorRegistry
from fastapi import FastAPI
from typing import Optional
import logging
import socket
import threading
import time
import atexit
import asyncio
import psutil
import os
from .security_metrics import security_registry
from ..services.rate_limiter import RATE_LIMIT_REGISTRY

logger = logging.getLogger(__name__)

class PortManager:
    """Gerencia portas para o servidor de métricas"""
    def __init__(self):
        self._used_ports = set()
        self._lock = threading.Lock()
        self._port_to_pid = {}
        self._port_to_thread = {}

    def find_free_port(self) -> int:
        """Encontra uma porta livre e a marca como em uso"""
        with self._lock:
            for _ in range(10):  # Tenta 10 vezes
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))
                    port = s.getsockname()[1]
                    if port not in self._used_ports:
                        self._used_ports.add(port)
                        self._port_to_pid[port] = os.getpid()
                        return port
            raise RuntimeError("Não foi possível encontrar uma porta livre")

    def register_thread(self, port: int, thread: threading.Thread) -> None:
        """Registra a thread associada a uma porta"""
        with self._lock:
            self._port_to_thread[port] = thread

    def release_port(self, port: int, force: bool = True) -> None:
        """Libera uma porta marcada como em uso"""
        with self._lock:
            if port in self._port_to_thread:
                thread = self._port_to_thread[port]
                if thread and thread.is_alive():
                    logger.warning(f"Thread ainda ativa na porta {port}, forçando encerramento")
                    # Tenta encerrar a thread graciosamente
                    for _ in range(5):
                        if not thread.is_alive():
                            break
                        time.sleep(0.1)
                    
            if force and port in self._port_to_pid:
                pid = self._port_to_pid[port]
                try:
                    for proc in psutil.process_iter(['pid', 'name', 'connections']):
                        try:
                            if proc.pid == pid:
                                for conn in proc.connections():
                                    if conn.laddr.port == port:
                                        proc.terminate()
                                        proc.wait(timeout=1)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception as e:
                    logger.warning(f"Erro ao tentar liberar processos na porta {port}: {e}")
            
            self._used_ports.discard(port)
            self._port_to_pid.pop(port, None)
            self._port_to_thread.pop(port, None)

    def is_port_in_use(self, port: int) -> bool:
        """Verifica se uma porta está em uso"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(0.2)
                s.bind(('', port))
                return False
            except (socket.error, OSError):
                return True

port_manager = PortManager()

class MetricsExporter:
    def __init__(self):
        # Cria um registro combinado com todas as métricas
        self.registry = CollectorRegistry()
        # Adiciona os registros específicos
        REGISTRY.register = lambda: None  # Desabilita o registro global
        self.registry.register = lambda collector: None  # Desabilita o registro automático
        
        # Registra as métricas de segurança
        for metric in security_registry.collect():
            self.registry.register(metric)
        
        # Registra as métricas de rate limit
        for metric in RATE_LIMIT_REGISTRY.collect():
            self.registry.register(metric)
        
        self._server = None
        self._port = None
        self._server_thread = None
        self._shutdown_event = threading.Event()
        self._lock = asyncio.Lock()
        self._initialized = False
        atexit.register(self._cleanup)

    async def start(self, app: FastAPI, port: Optional[int] = None) -> None:
        """Inicia o servidor de métricas do Prometheus com retry"""
        try:
            async with self._lock:
                if self._initialized:
                    logger.warning("Metrics server already initialized, shutting down first")
                    await self.shutdown()
                
                await self.shutdown()  # Garante que qualquer instância anterior está desligada
                await asyncio.sleep(0.2)  # Delay maior para garantir liberação de recursos
                
                for attempt in range(3):
                    try:
                        self._port = port or port_manager.find_free_port()
                        
                        # Verifica se a porta já está em uso
                        if port_manager.is_port_in_use(self._port):
                            logger.warning(f"Port {self._port} is already in use, forcing release")
                            port_manager.release_port(self._port, force=True)
                            await asyncio.sleep(0.2)
                            if port_manager.is_port_in_use(self._port):
                                raise RuntimeError(f"Port {self._port} could not be released")
                        
                        self._shutdown_event.clear()
                        self._server_thread = threading.Thread(
                            target=self._run_server,
                            args=(self._port,),
                            daemon=True
                        )
                        port_manager.register_thread(self._port, self._server_thread)
                        self._server_thread.start()
                        
                        # Aguarda o servidor iniciar com timeout
                        start_time = time.time()
                        while time.time() - start_time < 5:  # 5 segundos de timeout
                            if self._check_server_running():
                                self._initialized = True
                                logger.info(f"Metrics server started on port {self._port}")
                                app.add_event_handler("shutdown", self.shutdown)
                                return
                            await asyncio.sleep(0.1)
                        
                        raise RuntimeError("Timeout waiting for metrics server to start")
                    except Exception as e:
                        if attempt == 2:  # Última tentativa
                            raise RuntimeError(f"Failed to start metrics server after 3 attempts: {e}")
                        logger.warning(f"Failed to start metrics server (attempt {attempt + 1}): {e}")
                        await asyncio.sleep(0.5 * (2 ** attempt))  # Backoff exponencial
                        await self.shutdown()
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise

    def _run_server(self, port: int) -> None:
        """Executa o servidor de métricas em uma thread separada"""
        try:
            start_http_server(port, registry=self.registry)
            while not self._shutdown_event.is_set():
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Metrics server error: {e}")
        finally:
            self._cleanup()

    def _check_server_running(self) -> bool:
        """Verifica se o servidor está rodando"""
        if not self._port:
            return False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                s.connect(('localhost', self._port))
                return True
        except:
            return False

    async def shutdown(self) -> None:
        """Desliga o servidor de métricas com retry"""
        if not self._server_thread:
            return

        try:
            async with self._lock:
                self._shutdown_event.set()
                self._initialized = False
                
                if self._port:
                    # Tenta encerrar graciosamente
                    for _ in range(5):  # Tenta por 0.5 segundos
                        if not self._server_thread.is_alive():
                            break
                        await asyncio.sleep(0.1)
                    
                    # Se ainda estiver rodando, força o encerramento
                    if self._server_thread.is_alive():
                        logger.warning("Forcing metrics server shutdown")
                        port_manager.release_port(self._port, force=True)
                    
                    # Aguarda a liberação da porta
                    for _ in range(10):  # Espera até 1 segundo
                        if not port_manager.is_port_in_use(self._port):
                            break
                        await asyncio.sleep(0.1)
                    
                    if port_manager.is_port_in_use(self._port):
                        logger.error(f"Failed to release port {self._port}")
                
        except Exception as e:
            logger.error(f"Error shutting down metrics server: {e}")
        finally:
            if self._port:
                port_manager.release_port(self._port, force=True)
            self._server_thread = None
            self._port = None
            logger.info("Metrics server stopped")

    def _cleanup(self) -> None:
        """Cleanup no shutdown do processo"""
        if self._port:
            port_manager.release_port(self._port, force=True)
            self._port = None
        self._server_thread = None
        self._initialized = False

    def get_registry(self) -> CollectorRegistry:
        """Retorna o registro de métricas"""
        return self.registry

metrics_exporter = MetricsExporter() 