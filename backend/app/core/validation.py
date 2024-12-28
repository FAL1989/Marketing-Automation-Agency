import re
from typing import Dict, Any
from fastapi import HTTPException, status

class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class DataValidator:
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    USERNAME_PATTERN = r'^[a-zA-Z0-9_]+$'
    PASSWORD_RULES = [
        (r'.{8,}', 'Senha deve ter pelo menos 8 caracteres'),
        (r'[A-Z]', 'Senha deve conter pelo menos uma letra maiúscula'),
        (r'[a-z]', 'Senha deve conter pelo menos uma letra minúscula'),
        (r'\d', 'Senha deve conter pelo menos um número'),
        (r'[!@#$%^&*(),.?":{}|<>]', 'Senha deve conter pelo menos um caractere especial')
    ]

    @classmethod
    def validate_email(cls, email: str) -> bool:
        if not re.match(cls.EMAIL_PATTERN, email):
            raise ValidationError("Email inválido")
        return True

    @classmethod
    def validate_password(cls, password: str) -> bool:
        for pattern, message in cls.PASSWORD_RULES:
            if not re.search(pattern, password):
                raise ValidationError(message)
        return True

    @classmethod
    def validate_username(cls, username: str) -> bool:
        if len(username) < 3:
            raise ValidationError("Nome de usuário deve ter pelo menos 3 caracteres")
        if not re.match(cls.USERNAME_PATTERN, username):
            raise ValidationError("Nome de usuário deve conter apenas letras, números e underscore")
        return True

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "(": "&#40;",
            ")": "&#41;"
        }
        for char, entity in replacements.items():
            input_str = input_str.replace(char, entity)
        return input_str

data_validator = DataValidator() 