import sys
sys.path.append('.')
from sqlalchemy import create_engine, text

SUPABASE_URL = "postgresql+pg8000://postgres.einluoeyetxrxfxgqfmc:Dbpfs2001$dbpfs2001@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

engine = create_engine(SUPABASE_URL)

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, name, type FROM categories;"))
        rows = res.fetchall()
        for row in rows:
            print(row)
except Exception as e:
    print(f"Error: {e}")
