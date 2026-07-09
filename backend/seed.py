from sqlalchemy.orm import Session
from database import engine, get_db
import models
from auth import get_password_hash

def seed_db():
    models.Base.metadata.create_all(bind=engine)
    db = next(get_db())
    
    # Check if user already exists
    user = db.query(models.User).filter(models.User.username == "Davi Placco").first()
    
    if not user:
        print("Seeding initial user 'Davi Placco'...")
        hashed_pw = get_password_hash("Dbpfs2001$dbpfs2001")
        new_user = models.User(username="Davi Placco", password_hash=hashed_pw)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Add some default categories
        categories = [
            models.Category(user_id=new_user.id, name="Salário", color="#10b981", type=models.CategoryType.INCOME),
            models.Category(user_id=new_user.id, name="Alimentação", color="#ef4444", type=models.CategoryType.EXPENSE),
            models.Category(user_id=new_user.id, name="Habitação", color="#f59e0b", type=models.CategoryType.EXPENSE),
            models.Category(user_id=new_user.id, name="Ações", color="#8b5cf6", type=models.CategoryType.INVESTMENT),
        ]
        db.add_all(categories)
        db.commit()
        print("Database seeded successfully.")
    else:
        print("User 'Davi Placco' already exists. Skipping seed.")

if __name__ == "__main__":
    seed_db()
