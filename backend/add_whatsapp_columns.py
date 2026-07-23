import os
import sys
from sqlalchemy import create_engine, text

# Make sure we can import from backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load env variables (if needed) or just use database.py's URL
from database import SQLALCHEMY_DATABASE_URL

print(f"Migrating database at: {SQLALCHEMY_DATABASE_URL}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

try:
    with engine.connect() as conn:
        # Add whatsapp_number
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN whatsapp_number VARCHAR(50) DEFAULT NULL"))
            print("Successfully added whatsapp_number column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("whatsapp_number column already exists.")
            else:
                print(f"Error adding whatsapp_number: {e}")
        
        # Add whatsapp_report_frequency
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN whatsapp_report_frequency VARCHAR(20) DEFAULT 'off'"))
            print("Successfully added whatsapp_report_frequency column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("whatsapp_report_frequency column already exists.")
            else:
                print(f"Error adding whatsapp_report_frequency: {e}")
                
        conn.commit()
except Exception as e:
    print(f"Failed to connect or migrate: {e}")
