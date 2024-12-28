from sqlalchemy.orm import Session
from app.db.base_class import Base
from app.db.session import engine
from app.services.rabbitmq import setup_rabbitmq

def init_db() -> None:
    """
    Inicializa o banco de dados e configura o RabbitMQ
    """
    # Criar tabelas
    Base.metadata.create_all(bind=engine)
    
    # Configurar RabbitMQ
    setup_rabbitmq()

def init_db_and_tables() -> None:
    """
    Inicializa o banco de dados e cria dados iniciais se necessário
    """
    init_db()
    # Aqui podemos adicionar a criação de dados iniciais se necessário 