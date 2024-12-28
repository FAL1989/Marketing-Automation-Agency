import pyotp
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash

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
        self.db.commit()
        
        return uri
        
    async def verify_mfa_code(self, user: User, code: str) -> bool:
        """
        Verifica código MFA fornecido pelo usuário
        """
        if not user.mfa_secret:
            return False
            
        totp = pyotp.TOTP(user.mfa_secret)
        return totp.verify(code)
        
    async def enable_mfa(self, user: User) -> str:
        """
        Habilita MFA para um usuário
        """
        if user.mfa_enabled:
            raise ValueError("MFA já está habilitado para este usuário")
            
        uri = await self.generate_mfa_secret(user)
        user.mfa_enabled = True
        self.db.commit()
        
        return uri
        
    async def disable_mfa(self, user: User) -> None:
        """
        Desabilita MFA para um usuário
        """
        if not user.mfa_enabled:
            raise ValueError("MFA não está habilitado para este usuário")
            
        user.mfa_enabled = False
        user.mfa_secret = None
        self.db.commit() 