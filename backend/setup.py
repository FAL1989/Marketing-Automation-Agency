"""
Setup do pacote aiagency
"""

from setuptools import setup, find_packages

setup(
    name="aiagency",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Web Framework
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        
        # Database
        "sqlalchemy>=2.0.23",
        "alembic>=1.12.1",
        "asyncpg>=0.29.0",
        "motor>=3.3.1",
        
        # Validation
        "pydantic>=2.5.2",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        
        # Security
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        
        # Monitoring
        "redis>=5.0.1",
        "prometheus-client>=0.19.0",
        "structlog>=23.2.0",
        
        # HTTP Client
        "httpx>=0.25.2",
        "aiohttp>=3.9.1",
        
        # Email
        "aiosmtplib>=2.0.1",
        
        # Data Processing
        "pandas>=2.0.0",
        "xlsxwriter>=3.1.0",
        "python-magic>=0.4.27",
        
        # Testing
        "pytest>=7.4.3",
        "pytest-asyncio>=0.23.2",
        "pytest-cov>=4.1.0",
        "pytest-env>=1.1.1",
        "pytest-mock>=3.12.0",
        "docker>=7.0.0",
        
        # Utils
        "pytz>=2023.3",
        "email-validator>=2.1.0.post1",
        "python-slugify>=8.0.1",
        "aiofiles>=23.2.1",
    ],
    extras_require={
        "dev": [
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "pre-commit>=3.5.0",
        ],
        "test": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.23.2",
            "pytest-cov>=4.1.0",
            "pytest-env>=1.1.1",
            "pytest-mock>=3.12.0",
            "docker>=7.0.0",
        ],
    },
    python_requires=">=3.12",
) 