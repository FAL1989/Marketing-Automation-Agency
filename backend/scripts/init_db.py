from app.database.connection import init_db
from app.models import User, Content, AuditLog  # Importando todos os modelos

def main():
    print("Inicializando o banco de dados...")
    init_db()
    print("Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    main() 