import sys
sys.path.append('.')
from sqlalchemy import create_engine, text

SUPABASE_URL = "postgresql+pg8000://postgres.einluoeyetxrxfxgqfmc:Dbpfs2001$dbpfs2001@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

engine = create_engine(SUPABASE_URL)

with engine.connect() as conn:
    conn.execute(text("SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));"))
    conn.execute(text("SELECT setval('categories_id_seq', (SELECT COALESCE(MAX(id), 1) FROM categories));"))
    conn.execute(text("SELECT setval('transactions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM transactions));"))
    conn.execute(text("SELECT setval('investments_id_seq', (SELECT COALESCE(MAX(id), 1) FROM investments));"))
    conn.commit()

print("Sequences reset successfully!")
