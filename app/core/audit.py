import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import Request, Response
from app.core.config import settings

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Configurar formato do log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Criar diretório de logs se não existir
        os.makedirs(settings.AUDIT_LOG_PATH, exist_ok=True)
        
        # Handler para arquivo
        self.file_handler = logging.FileHandler(
            os.path.join(settings.AUDIT_LOG_PATH, "audit.log")
        )
        self.file_handler.setFormatter(formatter)
        
        # Handler para console
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(formatter)
        
        # Adicionar handlers
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)

    def log_request(
        self,
        request: Request,
        response: Optional[Response] = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        Registra uma requisição HTTP com detalhes de auditoria
        """
        try:
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "status_code": getattr(response, "status_code", None) if response else None,
                "error": str(error) if error else None
            }
            
            # Adicionar headers relevantes (exceto sensíveis)
            headers = dict(request.headers)
            sensitive_headers = {"authorization", "cookie", "x-api-key"}
            filtered_headers = {
                k: v for k, v in headers.items() 
                if k.lower() not in sensitive_headers
            }
            audit_data["headers"] = filtered_headers
            
            # Log como JSON
            self.logger.info(json.dumps(audit_data))
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar log de auditoria: {str(e)}")

    def log_security_event(
        self, 
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra um evento de segurança
        """
        try:
            security_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "details": details or {}
            }
            
            self.logger.info(json.dumps(security_data))
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar evento de segurança: {str(e)}")

# Instância global do logger de auditoria
audit_logger = AuditLogger() 