import sys
sys.path.append('.')
from sqlalchemy import create_engine, text

SUPABASE_URL = "postgresql+pg8000://postgres.einluoeyetxrxfxgqfmc:Dbpfs2001$dbpfs2001@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

engine = create_engine(SUPABASE_URL)

try:
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("DELETE FROM categories WHERE id IN (5, 17, 19, 20);"))
        print("Duplicates cleaned up!")
except Exception as e:
    print(f"Error: {e}")
