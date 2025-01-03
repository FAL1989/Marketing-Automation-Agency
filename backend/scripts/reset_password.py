from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import asyncio

async def reset_password(email: str, new_password: str):
    """
    Reseta a senha de um usuário
    """
    async with AsyncSessionLocal() as session:
        try:
            # Busca o usuário
            user = await session.query(User).filter(User.email == email).first()
            if not user:
                print(f"Usuário com email {email} não encontrado")
                return False
            
            # Atualiza a senha
            user.hashed_password = get_password_hash(new_password)
            await session.commit()
            print(f"Senha alterada com sucesso para o usuário {email}")
            return True
            
        except Exception as e:
            print(f"Erro ao resetar senha: {e}")
            await session.rollback()
            return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Uso: python reset_password.py <email> <nova_senha>")
        sys.exit(1)
        
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    asyncio.run(reset_password(email, new_password)) 