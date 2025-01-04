import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import settings

def setup_logging():
    """
    Configura o sistema de logging da aplicação
    """
    # Cria o diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configura o formato do log
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Configura o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # Handler para arquivo
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    # Configura loggers específicos
    loggers = [
        "uvicorn",
        "uvicorn.error",
        "fastapi",
        "sqlalchemy.engine",
        "aiohttp.client",
        "aiohttp.server",
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers = []  # Remove handlers existentes
        logger.propagate = True  # Propaga para o logger raiz 