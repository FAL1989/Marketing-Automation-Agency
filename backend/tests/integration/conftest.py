import pytest
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.core.security import get_password_hash

@pytest.fixture
def test_user(db_session: Session):
    """Cria um usuário de teste no banco de dados"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user 