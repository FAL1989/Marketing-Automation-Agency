from pydantic import BaseModel

class TokenResponse(BaseModel):
    """Esquema de resposta com tokens"""
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    """Esquema para requisição de renovação de token"""
    refresh_token: str 