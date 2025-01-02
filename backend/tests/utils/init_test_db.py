import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect
import logging
import asyncio

# Importar todos os modelos necessários
from ...app.db.base import Base
from ...app.models.user import User
from ...app.models.audit import AuditLog
from ...app.models.content import Content
from ...app.models.template import Template
from ...app.models.generation import Generation

logger = logging.getLogger(__name__)

async def init_test_db():
    """
    Inicializa o banco de dados de teste
    """
    # Configurações
    db_params = {
        'host': 'localhost',
        'user': 'aiagency',
        'password': 'aiagency123',
        'port': '5432'
    }
    
    db_name = 'aiagency_test'
    
    try:
        logger.info("Iniciando inicialização do banco de dados de teste")
        
        # Conecta ao PostgreSQL
        conn = psycopg2.connect(
            **db_params,
            database='postgres'  # Conecta ao banco postgres para poder criar/dropar outros bancos
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Fecha todas as conexões existentes com o banco
        cursor.execute("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = %s
            AND pid <> pg_backend_pid()
        """, (db_name,))
        logger.info("Conexões existentes encerradas")
        
        # Verifica se o banco existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        # Tenta dropar o banco se existir
        if exists:
            try:
                cursor.execute(f'DROP DATABASE {db_name}')
                logger.info(f"Banco de dados {db_name} removido")
            except Exception as e:
                logger.warning(f"Erro ao remover banco de dados: {e}")
        
        # Cria o banco de dados
        cursor.execute(f'CREATE DATABASE {db_name}')
        logger.info(f"Banco de dados {db_name} criado")
        
        cursor.close()
        conn.close()
        
        # Conecta ao banco criado com SQLAlchemy
        engine = create_async_engine(
            f"postgresql+asyncpg://aiagency:aiagency123@localhost:5432/{db_name}",
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,
            max_overflow=10,
            echo=True
        )
        
        # Cria todas as tabelas em uma única transação
        async with engine.begin() as connection:
            logger.info("Criando todas as tabelas")
            await connection.run_sync(Base.metadata.drop_all)  # Garante que não há tabelas antigas
            await connection.run_sync(Base.metadata.create_all)
            
            # Verifica se as tabelas foram criadas
            def get_tables(conn):
                inspector = inspect(conn)
                tables = inspector.get_table_names()
                logger.info(f"Tabelas criadas: {tables}")
                
                # Verifica cada tabela necessária
                required_tables = ['users', 'audit_logs', 'contents', 'templates', 'generations']
                for table in required_tables:
                    if table not in tables:
                        raise Exception(f"Tabela {table} não foi criada!")
                    columns = inspector.get_columns(table)
                    logger.info(f"Colunas da tabela {table}: {[col['name'] for col in columns]}")
                return tables
            
            await connection.run_sync(get_tables)
        
        # Testa a criação de um usuário
        Session = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with Session() as session:
            try:
                # Cria um usuário de teste
                test_user = User(
                    email='test@test.com',
                    full_name='Test User',
                    hashed_password='test_hash',
                    is_active=True
                )
                session.add(test_user)
                await session.commit()
                logger.info("Usuário de teste criado com sucesso")
                
                # Verifica se o usuário foi criado
                result = await session.execute(
                    text("SELECT * FROM users WHERE email = :email"),
                    {"email": "test@test.com"}
                )
                user = result.first()
                if not user:
                    raise Exception("Usuário de teste não foi encontrado após criação")
                
                # Limpa o usuário de teste
                await session.execute(
                    text("DELETE FROM users WHERE email = :email"),
                    {"email": "test@test.com"}
                )
                await session.commit()
                logger.info("Usuário de teste removido com sucesso")
                
            except Exception as e:
                logger.error(f"Erro ao testar tabela users: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
        
        await engine.dispose()
        logger.info("Inicialização do banco de dados de teste concluída com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados de teste: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_test_db()) 