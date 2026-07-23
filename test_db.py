import sys
sys.path.append("./backend")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

SUPABASE_URL = "postgresql+pg8000://postgres.einluoeyetxrxfxgqfmc:Dbpfs2001$dbpfs2001@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"
engine = create_engine(SUPABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()
users = db.query(models.User).all()
for u in users:
    print(f"Username: '{u.username}', Hash: '{u.password_hash}'")
