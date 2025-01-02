import pyotp
import qrcode
import io
import base64
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User
from .security import get_password_hash
from .config import settings
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class MFAService:
    """Serviço para gerenciamento de MFA"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def generate_secret(self) -> str:
        """Gera um novo segredo para MFA"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, email: str, secret: str) -> str:
        """Gera o QR code para configuração do MFA"""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            email,
            issuer_name=settings.PROJECT_NAME
        )
        
        # Gerar QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Converter para imagem base64
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def generate_backup_codes(self, count: int = 10) -> Dict[str, str]:
        """Gera códigos de backup"""
        codes = {}
        for _ in range(count):
            code = pyotp.random_base32()[:8]  # 8 caracteres
            codes[code] = get_password_hash(code)
        return codes
    
    async def verify_mfa(self, user: User, code: str) -> bool:
        """Verifica um código MFA"""
        logger.info(f"Verificando código MFA para usuário: {user.email}")
        
        if not user.mfa_enabled or not user.mfa_secret:
            logger.error("MFA não está habilitado ou sem segredo configurado")
            return False
            
        # Verificar se o usuário está bloqueado
        if user.mfa_locked_until:
            now = datetime.utcnow()
            if user.mfa_locked_until > now:
                remaining_time = (user.mfa_locked_until - now).total_seconds()
                logger.warning(f"Usuário bloqueado por mais {remaining_time:.0f} segundos")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {remaining_time:.0f} seconds."
                )
            else:
                # Se o tempo de bloqueio já passou, reseta o contador
                logger.info("Tempo de bloqueio expirado, resetando contador")
                await self._reset_attempts(user)
        
        # Verificar código TOTP
        try:
            totp = pyotp.TOTP(user.mfa_secret)
            if totp.verify(code, valid_window=1):  # Permite uma janela de 30s antes/depois
                logger.info("Código TOTP válido")
                await self._reset_attempts(user)
                return True
        except Exception as e:
            logger.error(f"Erro ao verificar código TOTP: {e}")
            
        # Verificar código de backup
        if user.mfa_backup_codes and code in user.mfa_backup_codes:
            if await self._verify_backup_code(user, code):
                logger.info("Código de backup válido")
                await self._reset_attempts(user)
                return True
                
        # Incrementar tentativas falhas
        logger.warning(f"Código inválido. Tentativas: {user.mfa_attempts + 1}")
        await self._increment_attempts(user)
        return False
    
    async def _verify_backup_code(self, user: User, code: str) -> bool:
        """Verifica e invalida um código de backup"""
        if not user.mfa_backup_codes:
            return False
            
        hashed_code = user.mfa_backup_codes.get(code)
        if not hashed_code:
            return False
            
        # Remover código usado
        del user.mfa_backup_codes[code]
        await self.db.commit()
        
        return True
    
    async def _increment_attempts(self, user: User):
        """Incrementa o contador de tentativas falhas"""
        user.mfa_attempts += 1
        logger.info(f"Incrementando tentativas para {user.mfa_attempts}")
        
        # Bloquear após exceder limite
        if user.mfa_attempts > settings.MFA_MAX_ATTEMPTS:
            block_duration = timedelta(seconds=settings.MFA_BLOCK_DURATION)
            user.mfa_locked_until = datetime.utcnow() + block_duration
            logger.warning(f"Usuário bloqueado por {settings.MFA_BLOCK_DURATION} segundos")
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {settings.MFA_BLOCK_DURATION} seconds."
            )
            
        await self.db.commit()
    
    async def _reset_attempts(self, user: User):
        """Reseta o contador de tentativas"""
        logger.info("Resetando contador de tentativas")
        user.mfa_attempts = 0
        user.mfa_locked_until = None
        user.mfa_last_used = datetime.utcnow()
        await self.db.commit()
        logger.info("Contador resetado com sucesso")
    
    async def enable_mfa(self, user: User) -> Dict[str, str]:
        """Habilita MFA para um usuário"""
        secret = self.generate_secret()
        qr_uri = self.generate_qr_code(user.email, secret)
        backup_codes = self.generate_backup_codes()
        
        user.mfa_secret = secret
        user.mfa_backup_codes = backup_codes
        user.mfa_enabled = True
        user.mfa_attempts = 0
        user.mfa_locked_until = None
        
        await self.db.commit()
        
        return {
            "qr_uri": qr_uri,
            "backup_codes": list(backup_codes.keys())
        }
    
    async def disable_mfa(self, user: User):
        """Desabilita MFA para um usuário"""
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_backup_codes = None
        user.mfa_attempts = 0
        user.mfa_locked_until = None
        user.mfa_last_used = None
        
        await self.db.commit() 