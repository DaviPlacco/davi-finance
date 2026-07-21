import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Pegar o DATABASE_URL do .env (fallback para sqlite local se não houver)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./davi_finance.db")

if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

def add_column():
    with engine.begin() as conn:
        print("A adicionar a coluna profile_image à tabela users...")
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN profile_image TEXT;"))
            print("Coluna adicionada com sucesso!")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("A coluna já existe. Nenhuma alteração foi necessária.")
            else:
                print(f"Erro ao adicionar a coluna: {e}")

if __name__ == "__main__":
    add_column()
