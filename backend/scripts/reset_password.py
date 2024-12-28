from app.database.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def reset_test_user_password():
    """Redefine a senha do usuário de teste"""
    db = SessionLocal()
    try:
        # Buscar usuário de teste
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("Usuário de teste não encontrado")
            return
            
        # Redefinir senha para "password123"
        user.hashed_password = get_password_hash("password123")
        db.commit()
        print("Senha redefinida com sucesso")
        
    except Exception as e:
        print(f"Erro ao redefinir senha: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_test_user_password() 