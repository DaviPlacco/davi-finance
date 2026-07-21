import sys
sys.path.append('.')
from sqlalchemy import create_engine, text

SUPABASE_URL = "postgresql+pg8000://postgres.einluoeyetxrxfxgqfmc:Dbpfs2001$dbpfs2001@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

engine = create_engine(SUPABASE_URL)

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE categories ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE investments ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE investment_logs ENABLE ROW LEVEL SECURITY;"))
    conn.commit()

print("RLS enabled successfully!")
