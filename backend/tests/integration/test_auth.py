"""
Testes de integração para autenticação
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.models.user import User
import logging
import json

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_login(client: TestClient, test_user: User):
    """Testa o endpoint de login com credenciais válidas"""
    try:
        logger.info(f"Testando login para usuário: {test_user.email}")
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123"  # Senha definida no fixture test_user
            }
        )
        
        logger.info(f"Status code: {response.status_code}")
        try:
            response_json = response.json()
            logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
        except Exception as e:
            logger.error(f"Erro ao decodificar response: {e}")
            logger.error(f"Response text: {response.text}")
            raise
        
        assert response.status_code == 200, "Login falhou"
        assert "access_token" in response_json, "Token não encontrado na resposta"
        assert response_json["token_type"] == "bearer", "Tipo de token incorreto"
        
        logger.info("Teste de login concluído com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no teste de login: {e}")
        raise

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: TestClient, test_user: User):
    """Testa o login com credenciais inválidas"""
    try:
        logger.info("Testando login com credenciais inválidas")
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "invalid@example.com",
                "password": "wrongpassword"
            }
        )
        
        logger.info(f"Status code: {response.status_code}")
        try:
            response_json = response.json()
            logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
        except Exception as e:
            logger.error(f"Erro ao decodificar response: {e}")
            logger.error(f"Response text: {response.text}")
            raise
        
        assert response.status_code == 401, "Status code incorreto para credenciais inválidas"
        assert response_json["detail"] == "Credenciais inválidas", "Mensagem de erro incorreta"
        
        logger.info("Teste de login com credenciais inválidas concluído com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no teste de login com credenciais inválidas: {e}")
        raise

@pytest.mark.asyncio
async def test_login_rate_limit(client: TestClient, test_user: User):
    """Testa o rate limiting no endpoint de login"""
    try:
        logger.info("Testando rate limit no login")
        
        # Tenta fazer login múltiplas vezes para acionar o rate limit
        for i in range(31):  # Limite é 30 tentativas por minuto
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "wrongpassword"
                }
            )
            logger.info(f"Tentativa {i+1}: status={response.status_code}")
            
            if response.status_code == 429:
                break
        
        assert response.status_code == 429, "Rate limit não foi acionado"
        response_json = response.json()
        assert "detail" in response_json, "Mensagem de rate limit não encontrada"
        assert "rate limit exceeded" in response_json["detail"].lower(), "Mensagem de rate limit incorreta"
        
        logger.info("Teste de rate limit no login concluído com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no teste de rate limit: {e}")
        raise

@pytest.mark.asyncio
async def test_login_mfa_required(client: TestClient, test_user: User):
    """Testa o login quando MFA está habilitado"""
    try:
        logger.info("Testando login com MFA habilitado")
        
        # Primeiro faz login com credenciais corretas
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123"
            }
        )
        
        logger.info(f"Status code inicial: {response.status_code}")
        response_json = response.json()
        logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
        
        # Se MFA está habilitado, deve retornar 202 (Accepted) com token temporário
        if test_user.mfa_enabled:
            assert response.status_code == 202, "Status code incorreto para MFA pendente"
            assert "temp_token" in response_json, "Token temporário não encontrado"
        else:
            assert response.status_code == 200, "Status code incorreto para login sem MFA"
            assert "access_token" in response_json, "Token de acesso não encontrado"
        
        logger.info("Teste de login com MFA concluído com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no teste de login com MFA: {e}")
        raise 