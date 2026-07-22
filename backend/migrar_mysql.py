import sys
sys.path.append('.')
from sqlalchemy import create_engine
import models
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# URL original do Supabase
SUPABASE_URL = "postgresql+pg8000://postgres.einluoeyetxrxfxgqfmc:Dbpfs2001$dbpfs2001@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

# Nova URL do MySQL (Hostinger ou Local) - Defina isto no .env como MYSQL_DATABASE_URL
# Exemplo: mysql+pymysql://usuario:senha@localhost/davi_finance
MYSQL_URL = os.getenv("MYSQL_DATABASE_URL")

if not MYSQL_URL:
    print("ERRO: MYSQL_DATABASE_URL não configurada no ficheiro .env")
    sys.exit(1)

# Engines
supabase_engine = create_engine(SUPABASE_URL)
mysql_engine = create_engine(MYSQL_URL)

# Criar tabelas no MySQL
models.Base.metadata.drop_all(bind=mysql_engine)
models.Base.metadata.create_all(bind=mysql_engine)

# Sessions
SupabaseSession = sessionmaker(bind=supabase_engine)
MysqlSession = sessionmaker(bind=mysql_engine)

supabase_db = SupabaseSession()
mysql_db = MysqlSession()

# Clean MySQL DB first
print("Limpando a base de dados MySQL (Destino)...")
mysql_db.query(models.InvestmentLog).delete()
mysql_db.query(models.Investment).delete()
mysql_db.query(models.Transaction).delete()
mysql_db.query(models.Category).delete()
mysql_db.query(models.User).delete()
mysql_db.commit()

print("A extrair dados do Supabase...")
users = supabase_db.query(models.User).all()
categories = supabase_db.query(models.Category).all()
transactions = supabase_db.query(models.Transaction).all()
investments = supabase_db.query(models.Investment).all()
investment_logs = supabase_db.query(models.InvestmentLog).all()

print(f"Encontrados: {len(users)} utilizadores, {len(categories)} categorias, {len(transactions)} transacoes, {len(investments)} investimentos, {len(investment_logs)} logs.")

print("A migrar utilizadores para MySQL...")
for user in users:
    mysql_db.merge(models.User(id=user.id, username=user.username, password_hash=user.password_hash, created_at=user.created_at, profile_image=user.profile_image))
mysql_db.commit()

print("A migrar categorias para MySQL...")
for cat in categories:
    mysql_db.merge(models.Category(id=cat.id, name=cat.name, type=cat.type, color=cat.color, user_id=cat.user_id, budget_limit=cat.budget_limit))
mysql_db.commit()

print("A migrar transacoes para MySQL...")
for t in transactions:
    mysql_db.merge(models.Transaction(
        id=t.id, 
        amount=t.amount, 
        type=t.type, 
        description=t.description, 
        date=t.date, 
        category_id=t.category_id, 
        user_id=t.user_id
    ))
mysql_db.commit()

print("A migrar investimentos para MySQL...")
for i in investments:
    mysql_db.merge(models.Investment(
        id=i.id,
        name=i.name,
        balance=i.balance,
        user_id=i.user_id,
        asset_type=i.asset_type,
        target=i.target
    ))
mysql_db.commit()

print("A migrar logs de investimentos para MySQL...")
for log in investment_logs:
    mysql_db.merge(models.InvestmentLog(
        id=log.id,
        investment_id=log.investment_id,
        amount=log.amount,
        date=log.date,
        type=log.type
    ))
mysql_db.commit()

print("Migração para MySQL concluída com sucesso!")
