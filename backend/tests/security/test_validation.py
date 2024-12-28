import pytest
from backend.app.core.validation import data_validator, ValidationError

def test_validate_email():
    """Testa validação de email"""
    # Email válido
    assert data_validator.validate_email("test@example.com") is True
    
    # Emails inválidos
    with pytest.raises(ValidationError):
        data_validator.validate_email("invalid_email")
    with pytest.raises(ValidationError):
        data_validator.validate_email("@example.com")
    with pytest.raises(ValidationError):
        data_validator.validate_email("test@.com")

def test_validate_password():
    """Testa validação de senha"""
    # Senha válida
    assert data_validator.validate_password("Test123!@#") is True
    
    # Senhas inválidas
    with pytest.raises(ValidationError):
        data_validator.validate_password("short")  # Muito curta
    with pytest.raises(ValidationError):
        data_validator.validate_password("nouppercase123!")  # Sem maiúscula
    with pytest.raises(ValidationError):
        data_validator.validate_password("NOLOWERCASE123!")  # Sem minúscula
    with pytest.raises(ValidationError):
        data_validator.validate_password("NoNumbers!")  # Sem números
    with pytest.raises(ValidationError):
        data_validator.validate_password("NoSpecial123")  # Sem caracteres especiais

def test_validate_username():
    """Testa validação de nome de usuário"""
    # Usernames válidos
    assert data_validator.validate_username("john_doe") is True
    assert data_validator.validate_username("user123") is True
    
    # Usernames inválidos
    with pytest.raises(ValidationError):
        data_validator.validate_username("ab")  # Muito curto
    with pytest.raises(ValidationError):
        data_validator.validate_username("invalid@user")  # Caracteres especiais
    with pytest.raises(ValidationError):
        data_validator.validate_username("user name")  # Espaços

def test_sanitize_input():
    """Testa sanitização de input"""
    # Testa remoção de caracteres perigosos
    input_str = '<script>alert("xss")</script>'
    sanitized = data_validator.sanitize_input(input_str)
    assert "<script>" not in sanitized
    assert "alert" in sanitized
    
    # Testa conversão de caracteres especiais
    input_str = 'Test & < > " \''
    sanitized = data_validator.sanitize_input(input_str)
    assert "&amp;" in sanitized
    assert "&lt;" in sanitized
    assert "&gt;" in sanitized
    assert "&quot;" in sanitized
    assert "&#x27;" in sanitized 