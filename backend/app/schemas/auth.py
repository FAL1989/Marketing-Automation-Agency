from pydantic import BaseModel
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    scopes: List[str] = []

class MFAResponse(BaseModel):
    """Schema para resposta de configuração MFA"""
    qr_uri: str
    backup_codes: List[str]

class MFAVerifyRequest(BaseModel):
    """Schema para verificação de código MFA"""
    code: str 