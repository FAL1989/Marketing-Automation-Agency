from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Verificar se o usuário já existe
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if test_user:
            print("Usuário de teste já existe")
            return

        # Criar novo usuário de teste
        test_user = User(
            username="test@example.com",
            email="test@example.com",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            is_superuser=False
        )
        db.add(test_user)
        db.commit()
        print("Usuário de teste criado com sucesso")
    except Exception as e:
        print(f"Erro ao criar usuário de teste: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user() 