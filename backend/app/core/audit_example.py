from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
from .audit import audit_logger, AuditEventType, AuditSeverity
import traceback
from starlette.middleware.base import BaseHTTPMiddleware

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        
        try:
            # Executa a requisição
            response = await call_next(request)
            
            # Registra eventos bem-sucedidos
            if response.status_code < 400:
                await audit_logger.log_event(
                    event_type=AuditEventType.ACCESS_GRANTED,
                    message=f"Acesso permitido: {request.url.path}",
                    severity=AuditSeverity.INFO,
                    request=request
                )
            else:
                await audit_logger.log_event(
                    event_type=AuditEventType.ACCESS_DENIED,
                    message=f"Acesso negado: {request.url.path}",
                    severity=AuditSeverity.WARNING,
                    request=request
                )
                
            return response
            
        except HTTPException as e:
            # Registra erros HTTP
            await audit_logger.log_event(
                event_type=AuditEventType.ACCESS_DENIED,
                message=f"Erro HTTP {e.status_code}: {e.detail}",
                severity=AuditSeverity.WARNING,
                request=request
            )
            raise
            
        except Exception as e:
            # Registra erros críticos
            await audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                message=f"Erro crítico: {str(e)}",
                severity=AuditSeverity.CRITICAL,
                request=request,
                details={"error": str(e), "traceback": traceback.format_exc()}
            )
            raise

async def setup_audit_logging(app: FastAPI):
    """Configura o sistema de audit logging"""
    await audit_logger.setup()
    app.add_middleware(AuditMiddleware)

async def example_usage():
    """Exemplo de uso do sistema de audit logging"""
    # Registra um evento de login bem-sucedido
    await audit_logger.log_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        message="Login bem-sucedido",
        user_id="user123",
        details={
            "ip": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "login_type": "password"
        }
    )
    
    # Registra uma tentativa de acesso não autorizado
    await audit_logger.log_event(
        event_type=AuditEventType.SECURITY_VIOLATION,
        message="Tentativa de acesso a recurso protegido",
        severity=AuditSeverity.CRITICAL,
        user_id="unknown",
        resource_id="protected_resource",
        details={
            "ip": "10.0.0.1",
            "path": "/api/admin",
            "method": "POST"
        }
    )
    
    # Consulta eventos dos últimos 7 dias
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    events = await audit_logger.get_events(
        start_date=start_date,
        end_date=end_date,
        severities=[AuditSeverity.CRITICAL]
    )
    
    # Exporta eventos para diferentes formatos
    if events:
        # CSV
        csv_file = await audit_logger.export_events(events, format="csv")
        print(f"Eventos exportados para CSV: {csv_file}")
        
        # JSON
        json_file = await audit_logger.export_events(events, format="json")
        print(f"Eventos exportados para JSON: {json_file}")
        
        # Excel
        excel_file = await audit_logger.export_events(events, format="excel")
        print(f"Eventos exportados para Excel: {excel_file}")
        
        # Relatório resumido
        summary_file = await audit_logger.export_events(events, format="summary")
        print(f"Relatório resumido gerado: {summary_file}")
        
    # Limpa eventos antigos
    await audit_logger.cleanup_old_events(days=90)

# Exemplo de uso em um endpoint FastAPI
async def register_user(request: Request, user_data: dict):
    """Exemplo de endpoint com audit logging"""
    try:
        # Simula registro de usuário
        user_id = "new_user_123"
        
        # Registra o evento
        await audit_logger.log_event(
            event_type=AuditEventType.DATA_CREATE,
            message=f"Novo usuário registrado: {user_id}",
            severity=AuditSeverity.INFO,
            user_id=user_id,
            request=request,
            details={
                "email": user_data.get("email"),
                "username": user_data.get("username"),
                "registration_source": "api"
            }
        )
        
        return {"user_id": user_id, "status": "success"}
        
    except Exception as e:
        # Registra o erro
        await audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            message=f"Erro ao registrar usuário: {str(e)}",
            severity=AuditSeverity.ERROR,
            request=request,
            details={"error": str(e)}
        )
        raise 