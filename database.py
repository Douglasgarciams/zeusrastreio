import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Pega a URL do banco do ambiente ou usa o SQLite como padrão local
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./gps_tracker.db"
)

# Ajuste de compatibilidade para o SQLAlchemy com PostgreSQL na nuvem
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configuração do engine dependendo do banco utilizado
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Para o PostgreSQL do Supabase (com pooler)
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()