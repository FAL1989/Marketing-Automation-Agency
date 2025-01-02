from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import re
import time
from ..monitoring.security_metrics import SecurityMetrics
from ..core.config import settings

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.security_metrics = SecurityMetrics()
        self.xss_pattern = re.compile(r'<[^>]*script.*?>|javascript:|data:', re.IGNORECASE)
        self.security_headers = {
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        }
        self.public_paths = settings.RATE_LIMIT_EXCLUDE_PATHS

    async def dispatch(self, request: Request, call_next) -> Response:
        # Inicia o timer para medir a latência
        timer = self.security_metrics.start_request_timer()

        # Verifica tentativas de XSS nos parâmetros da requisição
        await self._check_xss(request)

        # Verifica tentativas de CSRF
        await self._check_csrf(request)

        # Verifica acesso não autorizado
        await self._check_unauthorized_access(request)

        # Registra atividade suspeita se necessário
        await self._check_suspicious_activity(request)

        response = await call_next(request)

        # Adiciona headers de segurança
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Registra a latência da requisição
        self.security_metrics.record_request_latency(
            path=request.url.path,
            method=request.method,
            start_time=timer['start_time']
        )

        return response

    async def _check_xss(self, request: Request) -> None:
        """
        Verifica tentativas de XSS nos parâmetros da requisição
        """
        # Verifica query params
        for param in request.query_params.values():
            if self.xss_pattern.search(param):
                self.security_metrics.record_xss_attempt(
                    path=request.url.path,
                    ip=self._get_client_ip(request)
                )

        # Verifica headers
        for header in request.headers.values():
            if self.xss_pattern.search(header):
                self.security_metrics.record_xss_attempt(
                    path=request.url.path,
                    ip=self._get_client_ip(request)
                )

    async def _check_csrf(self, request: Request) -> None:
        """
        Verifica tentativas de CSRF
        """
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            origin = request.headers.get('Origin')
            referer = request.headers.get('Referer')

            if not origin and not referer:
                self.security_metrics.record_csrf_attempt(
                    path=request.url.path,
                    ip=self._get_client_ip(request)
                )

    async def _check_unauthorized_access(self, request: Request) -> None:
        """
        Verifica tentativas de acesso não autorizado
        """
        auth_header = request.headers.get('Authorization')
        if not auth_header and request.url.path not in self.public_paths:
            self.security_metrics.record_unauthorized_access(
                path=request.url.path,
                ip=self._get_client_ip(request),
                method=request.method
            )

    def _get_client_ip(self, request: Request) -> str:
        """
        Obtém o IP do cliente da requisição, processando corretamente o X-Forwarded-For
        """
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Processa múltiplos IPs no header X-Forwarded-For
            ips = [ip.strip() for ip in forwarded_for.split(',')]
            # Registra todos os IPs como atividade suspeita se houver mais de um
            if len(ips) > 1:
                for ip in ips:
                    self.security_metrics.record_suspicious_ip_activity(
                        ip=ip,
                        activity_type='multiple_ips'
                    )
            # Retorna o primeiro IP (mais próximo do cliente)
            return ips[0]
        return request.client.host if request.client else '0.0.0.0'

    async def _check_suspicious_activity(self, request: Request) -> None:
        """
        Verifica e registra atividades suspeitas
        """
        # Verifica múltiplos IPs em um curto período
        client_ip = self._get_client_ip(request)
        if client_ip != '0.0.0.0':
            # Registra a atividade do IP atual
            self.security_metrics.record_suspicious_ip_activity(
                ip=client_ip,
                activity_type='multiple_requests'
            )

            # Verifica se há múltiplos IPs no X-Forwarded-For
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for and ',' in forwarded_for:
                ips = [ip.strip() for ip in forwarded_for.split(',')]
                for ip in ips:
                    if ip != client_ip:
                        self.security_metrics.record_suspicious_ip_activity(
                            ip=ip,
                            activity_type='multiple_ips'
                        )

        # Verifica tentativas de força bruta em endpoints sensíveis
        if request.url.path in ['/api/v1/auth/login', '/api/v1/auth/mfa/verify']:
            self.security_metrics.record_suspicious_ip_activity(
                ip=client_ip,
                activity_type='auth_attempt'
            )
            
            # Registra tentativas de autenticação com múltiplos IPs
            if forwarded_for and ',' in forwarded_for:
                for ip in [ip.strip() for ip in forwarded_for.split(',')]:
                    if ip != client_ip:
                        self.security_metrics.record_suspicious_ip_activity(
                            ip=ip,
                            activity_type='auth_attempt_multiple_ips'
                        ) 