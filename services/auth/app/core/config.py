from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, EmailStr, validator
import secrets
from datetime import timedelta

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    APP_NAME: str = "AI Agency"
    APP_URL: str = "http://localhost:3000"
    SUPPORT_EMAIL: EmailStr = "support@aiagency.com"
    
    # Configurações JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Configurações de banco de dados
    DATABASE_URL: str
    
    # Configurações de email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    
    # Configurações CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    
    # Configurações MFA
    MFA_ISSUER: str = "AI Agency"
    MFA_DIGITS: int = 6
    MFA_INTERVAL: int = 30
    MFA_BACKUP_CODES_COUNT: int = 10
    MFA_BACKUP_CODE_LENGTH: int = 8
    MFA_MAX_ATTEMPTS: int = 5
    MFA_LOCKOUT_MINUTES: int = 30
    MFA_RECOVERY_LINK_EXPIRE_MINUTES: int = 30
    
    # Configurações de Rate Limiting
    RATE_LIMIT_DEFAULT: Dict[str, Any] = {
        "times": 5,
        "seconds": 5
    }
    
    RATE_LIMIT_MFA: Dict[str, Any] = {
        "times": 5,
        "seconds": 300  # 5 minutos
    }
    
    # Configurações de segurança
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 50
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Configurações de auditoria
    AUDIT_LOG_RETENTION_DAYS: int = 90
    AUDIT_ENABLED: bool = True
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 