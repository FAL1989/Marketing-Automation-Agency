import pyotp
import secrets
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from prometheus_client import Counter, Histogram

# Métricas MFA
MFA_ATTEMPTS = Counter(
    'mfa_attempts_total',
    'Total de tentativas de verificação MFA',
    ['status']  # success, failure, locked
)

MFA_VERIFICATION_TIME = Histogram(
    'mfa_verification_seconds',
    'Tempo de verificação do código MFA'
)

class MFAError(Exception):
    """Exceção base para erros de MFA"""
    pass

class MFALockedException(MFAError):
    """Usuário bloqueado por muitas tentativas"""
    pass

class MFAInvalidCodeException(MFAError):
    """Código MFA inválido"""
    pass

class MFAService:
    def __init__(self, db: Session):
        self.db = db
        
    async def generate_mfa_secret(self, user: User) -> str:
        """
        Gera segredo MFA para o usuário e retorna URI para QR code
        """
        secret = pyotp.random_base32()
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            user.email,
            issuer_name="AI Agency"
        )
        
        # Armazena segredo de forma segura
        user.mfa_secret = get_password_hash(secret)
        
        # Gera códigos de backup
        backup_codes = await self.generate_backup_codes()
        user.mfa_backup_codes = {
            code: get_password_hash(code) 
            for code in backup_codes
        }
        
        self.db.commit()
        
        return {
            "uri": uri,
            "backup_codes": backup_codes
        }
        
    async def verify_mfa_code(self, user: User, code: str) -> bool:
        """
        Verifica código MFA fornecido pelo usuário
        """
        # Verifica se usuário está bloqueado
        if user.mfa_locked_until and user.mfa_locked_until > datetime.utcnow():
            MFA_ATTEMPTS.labels(status="locked").inc()
            raise MFALockedException("Muitas tentativas inválidas. Tente novamente mais tarde.")
            
        with MFA_VERIFICATION_TIME.time():
            try:
                # Verifica código principal
                if not user.mfa_secret:
                    return False
                    
                totp = pyotp.TOTP(user.mfa_secret)
                if totp.verify(code):
                    self._handle_successful_verification(user)
                    return True
                    
                # Verifica códigos de backup
                if user.mfa_backup_codes:
                    for backup_code, hashed in user.mfa_backup_codes.items():
                        if verify_password(code, hashed):
                            # Remove código usado
                            del user.mfa_backup_codes[backup_code]
                            self.db.commit()
                            self._handle_successful_verification(user)
                            return True
                            
                # Código inválido
                self._handle_failed_verification(user)
                return False
                
            except Exception as e:
                MFA_ATTEMPTS.labels(status="error").inc()
                raise MFAError(f"Erro ao verificar código MFA: {str(e)}")
        
    async def enable_mfa(self, user: User) -> Dict:
        """
        Habilita MFA para um usuário
        """
        if user.mfa_enabled:
            raise ValueError("MFA já está habilitado para este usuário")
            
        mfa_data = await self.generate_mfa_secret(user)
        user.mfa_enabled = True
        self.db.commit()
        
        return mfa_data
        
    async def disable_mfa(self, user: User) -> None:
        """
        Desabilita MFA para um usuário
        """
        if not user.mfa_enabled:
            raise ValueError("MFA não está habilitado para este usuário")
            
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_backup_codes = None
        user.mfa_attempts = 0
        user.mfa_locked_until = None
        self.db.commit()
        
    async def generate_backup_codes(self, length: int = 8, count: int = 10) -> List[str]:
        """
        Gera códigos de backup aleatórios
        """
        codes = set()
        while len(codes) < count:
            code = secrets.token_hex(length)
            codes.add(code)
        return list(codes)
        
    async def reset_mfa_attempts(self, user: User) -> None:
        """
        Reseta contador de tentativas falhas de MFA
        """
        user.mfa_attempts = 0
        user.mfa_locked_until = None
        self.db.commit()
        
    def _handle_successful_verification(self, user: User) -> None:
        """
        Processa verificação bem sucedida
        """
        MFA_ATTEMPTS.labels(status="success").inc()
        user.mfa_last_used = datetime.utcnow()
        user.mfa_attempts = 0
        user.mfa_locked_until = None
        self.db.commit()
        
    def _handle_failed_verification(self, user: User) -> None:
        """
        Processa verificação falha
        """
        MFA_ATTEMPTS.labels(status="failure").inc()
        user.mfa_attempts += 1
        
        # Bloqueia após 5 tentativas por 30 minutos
        if user.mfa_attempts >= 5:
            user.mfa_locked_until = datetime.utcnow() + timedelta(minutes=30)
            
        self.db.commit()
        
        if user.mfa_locked_until:
            raise MFALockedException("Muitas tentativas inválidas. Tente novamente mais tarde.") 