import pytest
from datetime import datetime, timedelta
from jose import jwt
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token
)
from backend.app.core.config import settings

def test_password_hashing():
    """Testa o hash e verificação de senha"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Verifica se o hash é diferente da senha original
    assert hashed != password
    
    # Verifica se a senha pode ser validada corretamente
    assert verify_password(password, hashed) is True
    
    # Verifica se uma senha incorreta falha na validação
    assert verify_password("wrongpassword", hashed) is False

def test_access_token_creation():
    """Testa a criação e validação de tokens de acesso"""
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    
    # Decodifica o token para verificar o conteúdo
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    # Verifica se os dados estão corretos
    assert payload["sub"] == "test@example.com"
    assert "exp" in payload
    
    # Verifica se o token expira no tempo correto
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert (exp - now).total_seconds() < 15 * 60  # 15 minutos

def test_refresh_token_creation():
    """Testa a criação e validação de tokens de atualização"""
    data = {"sub": "test@example.com"}
    token = create_refresh_token(data)
    
    # Verifica se o token pode ser validado
    username = verify_refresh_token(token)
    assert username == "test@example.com"
    
    # Verifica se um token inválido retorna None
    assert verify_refresh_token("invalid_token") is None

def test_token_expiration():
    """Testa a expiração dos tokens"""
    data = {"sub": "test@example.com"}
    
    # Cria um token que já expirou
    expired_token = create_access_token(
        data=data,
        expires_delta=timedelta(minutes=-1)
    )
    
    # Verifica se o token expirado é rejeitado
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(expired_token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])

def test_token_tampering():
    """Testa a proteção contra manipulação de tokens"""
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    
    # Tenta decodificar o token com uma chave errada
    with pytest.raises(jwt.JWTError):
        jwt.decode(token, "wrong_key", algorithms=[settings.ALGORITHM])
    
    # Tenta decodificar um token manipulado
    with pytest.raises(jwt.JWTError):
        jwt.decode(token + "tampered", settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]) 