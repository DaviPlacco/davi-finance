import sys
sys.path.append('.')
from sqlalchemy import create_engine
import models
from sqlalchemy.orm import sessionmaker

RENDER_URL = "postgresql+pg8000://daviplacco:U9u9yJy8wWpidBjTdDqSwxQN4VzdLbF2@dpg-d97r05d7vvec73covi80-a.ohio-postgres.render.com/davi_finance"
SUPABASE_URL = "postgresql+pg8000://postgres.einluoeyetxrxfxgqfmc:Dbpfs2001$dbpfs2001@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

# Engines
render_engine = create_engine(RENDER_URL)
supabase_engine = create_engine(SUPABASE_URL)

# Criar tabelas no Supabase
models.Base.metadata.create_all(bind=supabase_engine)

# Sessions
RenderSession = sessionmaker(bind=render_engine)
SupabaseSession = sessionmaker(bind=supabase_engine)

render_db = RenderSession()
supabase_db = SupabaseSession()

# Clean Supabase DB first
print("Limpando a base de dados do Supabase...")
supabase_db.query(models.Investment).delete()
supabase_db.query(models.Transaction).delete()
supabase_db.query(models.Category).delete()
supabase_db.query(models.User).delete()
supabase_db.commit()

print("A migrar utilizadores...")
for user in render_db.query(models.User).all():
    supabase_db.merge(models.User(id=user.id, username=user.username, password_hash=user.password_hash))
supabase_db.commit()

print("A migrar categorias...")
for cat in render_db.query(models.Category).all():
    supabase_db.merge(models.Category(id=cat.id, name=cat.name, type=cat.type, color=cat.color, user_id=cat.user_id))
supabase_db.commit()

print("A migrar transacoes...")
for t in render_db.query(models.Transaction).all():
    supabase_db.merge(models.Transaction(
        id=t.id, 
        amount=t.amount, 
        type=t.type, 
        description=t.description, 
        date=t.date, 
        category_id=t.category_id, 
        user_id=t.user_id
    ))
supabase_db.commit()

print("A migrar investimentos...")
for i in render_db.query(models.Investment).all():
    supabase_db.merge(models.Investment(
        id=i.id,
        name=i.name,
        balance=i.balance,
        user_id=i.user_id,
        asset_type=getattr(i, 'asset_type', 'Outro') or 'Outro',
        target=getattr(i, 'target', None)
    ))
supabase_db.commit()

print("Migração concluída com sucesso!")
