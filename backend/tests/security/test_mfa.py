import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pyotp
from ...app.core.config import Settings
from ...app.models.user import User
from ...app.core.security import create_access_token, get_password_hash
from ...app.core.mfa import MFAService

@pytest.fixture
def test_user(db):
    """Fixture para criar um usuário de teste"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        mfa_enabled=False,
        mfa_secret=None
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_auth_headers(test_user):
    """Fixture para criar headers de autenticação"""
    access_token = create_access_token(
        data={"sub": test_user.email}
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def mfa_enabled_user(db, test_user):
    """Fixture para criar um usuário com MFA habilitado"""
    test_user.mfa_secret = pyotp.random_base32()
    test_user.mfa_enabled = True
    test_user.mfa_backup_codes = {
        "12345678": get_password_hash("12345678"),
        "87654321": get_password_hash("87654321")
    }
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    return test_user

@pytest.fixture
def mfa_token(mfa_enabled_user):
    """Fixture para gerar um token MFA válido"""
    totp = pyotp.TOTP(mfa_enabled_user.mfa_secret)
    return totp.now()

def test_enable_mfa(test_client, test_auth_headers):
    """Test enabling MFA for a user"""
    response = test_client.post(
        "/api/v1/auth/mfa/enable",
        headers=test_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "qr_uri" in data
    assert "backup_codes" in data
    assert len(data["backup_codes"]) == 10

def test_verify_mfa_setup(test_client, test_auth_headers):
    """Test verifying MFA setup with correct token"""
    # First enable MFA
    response = test_client.post(
        "/api/v1/auth/mfa/enable",
        headers=test_auth_headers
    )
    data = response.json()
    qr_uri = data["qr_uri"]
    
    # Extract secret from URI
    secret = qr_uri.split("secret=")[1].split("&")[0]
    
    # Generate valid token
    totp = pyotp.TOTP(secret)
    valid_token = totp.now()
    
    response = test_client.post(
        "/api/v1/auth/mfa/verify",
        headers=test_auth_headers,
        json={"code": valid_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "Código MFA válido" in data["message"]

def test_verify_mfa_setup_invalid_token(test_client, test_auth_headers):
    """Test verifying MFA setup with incorrect token"""
    response = test_client.post(
        "/api/v1/auth/mfa/verify",
        headers=test_auth_headers,
        json={"code": "000000"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "Código MFA inválido" in data["detail"]

def test_verify_mfa_with_backup_code(test_client, test_auth_headers, mfa_enabled_user):
    """Test verifying MFA with backup code"""
    response = test_client.post(
        "/api/v1/auth/mfa/verify",
        headers=test_auth_headers,
        json={"code": "12345678"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "Código MFA válido" in data["message"] 