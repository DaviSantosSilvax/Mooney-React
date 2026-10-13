import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import declarative_base, sessionmaker

# Carrega variáveis de ambiente a partir do .env na pasta backend
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Acesso@1")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "Mooney")

# URL.create cuida automaticamente de caracteres especiais (como o @ na senha)
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

# Criação do Engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Altere para True caso queira ver todas as queries SQL no terminal
    pool_pre_ping=True,  # Verifica conexões ativas antes de executar queries
)

# Fábrica de Sessões para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para os modelos ORM
Base = declarative_base()


def get_db():
    """Gerador de sessão do banco (padrão recomendado para APIs como FastAPI/Flask)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
