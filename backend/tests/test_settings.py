from app.core.config import Settings

class TestSettings(Settings):
    PROJECT_NAME: str = "AI Agency Test"
    VERSION: str = "0.1.0-test"
    DESCRIPTION: str = "AI Agency API - Ambiente de Testes"
    
    # Database
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_USER: str = "aiagency_test"
    POSTGRES_PASSWORD: str = "aiagency_test123"
    POSTGRES_DB: str = "aiagency_test"
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Debug
    DEBUG: bool = True
    
    # Testing
    TESTING: bool = True

test_settings = TestSettings() 