import sys
sys.path.append('.')
from sqlalchemy import create_engine, text

SUPABASE_URL = "postgresql+pg8000://postgres.einluoeyetxrxfxgqfmc:Dbpfs2001$dbpfs2001@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

engine = create_engine(SUPABASE_URL)

try:
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT c.id, c.name, c.type, count(t.id) as tx_count
            FROM categories c
            LEFT JOIN transactions t ON t.category_id = c.id
            GROUP BY c.id, c.name, c.type
            ORDER BY c.name;
        """))
        for row in res.fetchall():
            print(row)
except Exception as e:
    print(f"Error: {e}")
