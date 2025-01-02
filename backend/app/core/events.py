from enum import Enum

class EventType(str, Enum):
    """Tipos de eventos do sistema"""
    
    # Eventos de autenticação
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    
    # Eventos de usuário
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PASSWORD_CHANGED = "password_changed"
    
    # Eventos de segurança
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    INVALID_TOKEN = "invalid_token"
    ACCESS_DENIED = "access_denied"
    
    # Eventos de MFA
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILED = "mfa_failed"
    MFA_RATE_LIMIT = "mfa_rate_limit"
    
    # Eventos de sistema
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"
    CIRCUIT_BREAKER_STATE_CHANGE = "circuit_breaker_state_change"
    
    # Eventos de auditoria
    AUDIT_LOG_CREATED = "audit_log_created"
    AUDIT_LOG_DELETED = "audit_log_deleted"
    AUDIT_LOG_EXPORTED = "audit_log_exported" 