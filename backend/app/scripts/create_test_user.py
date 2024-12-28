from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash
from app.models import User, Base
from app.core.config import settings

def create_test_user():
    # Criar conexão com o banco de dados
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)  # Criar tabelas se não existirem
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Verificar se o usuário já existe
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if test_user:
            print("Usuário de teste já existe")
            return

        # Criar usuário de teste
        test_user = User(
            username="test",
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