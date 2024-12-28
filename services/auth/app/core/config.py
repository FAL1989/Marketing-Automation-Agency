from typing import List
from pydantic_settings import BaseSettings
from pydantic import model_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Auth Service"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # MFA
    MFA_ISSUER: str = "AI Agency"
    MFA_DIGITS: int = 6
    MFA_INTERVAL: int = 30
    
    model_config = {
        "env_file": ".env",
        "extra": "allow",
        "case_sensitive": False
    }

settings = Settings() 