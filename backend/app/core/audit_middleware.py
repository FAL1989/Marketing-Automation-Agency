from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from .audit import audit_logger, AuditEventType, AuditSeverity

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log da tentativa de acesso
        await audit_logger.log_event(
            event_type=AuditEventType.ACCESS_ATTEMPT,
            message=f"Access attempt to {request.url.path}",
            request=request
        )

        try:
            response = await call_next(request)

            # Log do acesso bem-sucedido
            if response.status_code < 400:
                await audit_logger.log_event(
                    event_type=AuditEventType.ACCESS_GRANTED,
                    message=f"Access granted to {request.url.path}",
                    request=request,
                    details={"status_code": response.status_code}
                )
            else:
                # Log do acesso negado
                await audit_logger.log_event(
                    event_type=AuditEventType.ACCESS_DENIED,
                    message=f"Access denied to {request.url.path}",
                    severity=AuditSeverity.WARNING,
                    request=request,
                    details={"status_code": response.status_code}
                )

            return response

        except Exception as e:
            # Log do erro
            await audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                message=str(e),
                severity=AuditSeverity.ERROR,
                request=request,
                details={"error_type": type(e).__name__}
            )
            raise 