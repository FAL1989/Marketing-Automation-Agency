from fastapi import Request, Response, UploadFile
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.config import settings
from ..core import monitoring
import json
import re
import magic
import bleach
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware para validação avançada de entrada"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Tipos de arquivo permitidos
        self.allowed_mime_types: Set[str] = {
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/pdf',
            'text/plain',
            'application/json',
            'text/csv'
        }
        
        # Tamanhos máximos (em bytes)
        self.max_payload_size: int = 10 * 1024 * 1024  # 10MB
        self.max_file_size: int = 5 * 1024 * 1024      # 5MB
        
        # Configuração do sanitizador HTML
        self.html_sanitizer = bleach.sanitizer.Cleaner(
            tags=bleach.sanitizer.ALLOWED_TAGS + ['p', 'br', 'div', 'span'],
            attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES,
            styles=['color', 'font-weight', 'text-align'],
            protocols=bleach.sanitizer.ALLOWED_PROTOCOLS,
            strip=True,
            strip_comments=True
        )
        
        # Padrões suspeitos em JSON
        self.suspicious_json_patterns = [
            r"__proto__",
            r"constructor",
            r"prototype",
            r"\$where",
            r"\$ne",
            r"\$gt",
            r"\$lt"
        ]
        
    async def _validate_content_type(self, request: Request) -> Optional[Response]:
        """Valida o Content-Type da requisição"""
        content_type = request.headers.get("content-type", "")
        
        # Verifica se é um upload de arquivo
        if content_type.startswith("multipart/form-data"):
            form = await request.form()
            for field in form:
                if isinstance(form[field], UploadFile):
                    file = form[field]
                    # Verifica tamanho do arquivo
                    if await file.size() > self.max_file_size:
                        return Response(
                            content="File too large",
                            status_code=413
                        )
                    
                    # Verifica tipo do arquivo
                    mime = magic.from_buffer(await file.read(1024), mime=True)
                    if mime not in self.allowed_mime_types:
                        return Response(
                            content="File type not allowed",
                            status_code=415
                        )
                    
                    # Retorna o arquivo para o início
                    await file.seek(0)
        
        return None
        
    def _sanitize_html(self, content: str) -> str:
        """Sanitiza conteúdo HTML"""
        return self.html_sanitizer.clean(content)
        
    def _validate_json_payload(self, data: dict) -> Optional[str]:
        """Valida payload JSON contra padrões suspeitos"""
        json_str = json.dumps(data)
        
        # Verifica padrões suspeitos
        for pattern in self.suspicious_json_patterns:
            if re.search(pattern, json_str, re.IGNORECASE):
                return f"Suspicious pattern detected: {pattern}"
        
        # Verifica profundidade do JSON
        def check_depth(obj, current_depth=0):
            if current_depth > 20:  # Máximo de 20 níveis
                return False
            if isinstance(obj, dict):
                return all(check_depth(v, current_depth + 1) for v in obj.values())
            if isinstance(obj, list):
                return all(check_depth(item, current_depth + 1) for item in obj)
            return True
            
        if not check_depth(data):
            return "JSON structure too deep"
            
        return None
        
    async def _validate_request_size(self, request: Request) -> Optional[Response]:
        """Valida o tamanho total da requisição"""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_payload_size:
            return Response(
                content="Payload too large",
                status_code=413
            )
        return None
        
    async def __call__(self, scope, receive, send):
        """Processa a requisição aplicando validações"""
        request = Request(scope, receive=receive)
        
        try:
            # Valida tamanho da requisição
            size_validation = await self._validate_request_size(request)
            if size_validation:
                await size_validation(scope, receive, send)
                return
                
            # Valida content type e arquivos
            content_validation = await self._validate_content_type(request)
            if content_validation:
                await content_validation(scope, receive, send)
                return
                
            # Intercepta o body para validação
            body = await request.body()
            if body:
                try:
                    # Tenta parse JSON
                    if request.headers.get("content-type") == "application/json":
                        json_data = json.loads(body)
                        json_error = self._validate_json_payload(json_data)
                        if json_error:
                            return Response(
                                content=json_error,
                                status_code=400
                            )
                    
                    # Sanitiza campos HTML se necessário
                    if b"<" in body and b">" in body:
                        decoded = body.decode()
                        sanitized = self._sanitize_html(decoded)
                        if sanitized != decoded:
                            monitoring.track_xss_attempt(request.client.host)
                            
                except json.JSONDecodeError:
                    return Response(
                        content="Invalid JSON format",
                        status_code=400
                    )
                except UnicodeDecodeError:
                    return Response(
                        content="Invalid character encoding",
                        status_code=400
                    )
                
            # Processa a requisição
            async def receive_wrapper():
                payload = await receive()
                if payload["type"] == "http.request":
                    payload["body"] = body
                return payload
                
            await self.app(scope, receive_wrapper, send)
            
        except Exception as e:
            logger.error(f"Error in input validation: {str(e)}")
            return Response(
                content="Internal server error during input validation",
                status_code=500
            ) 