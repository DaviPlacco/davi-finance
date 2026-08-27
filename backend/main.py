from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import extract, text, func
from datetime import timedelta, datetime
import calendar
import random
from typing import Optional, List
import models, schemas, auth
from database import engine, get_db, SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

# Migrations & Table Creation
def run_migrations():
    models.Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN receipt_image TEXT"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE categories ADD COLUMN group_id INTEGER"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(255)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN profile_image TEXT"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN is_transfer BOOLEAN DEFAULT FALSE"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE categories ADD COLUMN icon VARCHAR(100)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE category_groups ADD COLUMN icon VARCHAR(100)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN payment_method VARCHAR(100)"))
            conn.commit()
        except Exception:
            pass
    try:
        db = SessionLocal()
        users = db.query(models.User).all()
        for u in users:
            deduplicate_user_categories(u.id, db)
        db.close()
    except Exception:
        pass

def deduplicate_user_categories(user_id: int, db: Session):
    """
    Encontra categorias do mesmo utilizador com o mesmo tipo e nome idêntico (case-insensitive).
    Unifica todas as transações e metas na categoria canónica e elimina os registos duplicados.
    """
    try:
        categories = db.query(models.Category).filter(models.Category.user_id == user_id).order_by(models.Category.id.asc()).all()
        groups: dict[tuple[str, str], list[models.Category]] = {}
        for c in categories:
            cleaned_name = c.name.strip().lower() if c.name else ""
            cat_type = str(c.type.value if hasattr(c.type, 'value') else c.type).lower()
            key = (cleaned_name, cat_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(c)
        
        modified = False
        for (c_name, c_type), cat_list in groups.items():
            if len(cat_list) > 1:
                # Escolhe a categoria canónica: prioridade para quem tem icon, group_id, budget_limit, ou menor ID
                canonical = sorted(
                    cat_list,
                    key=lambda x: (
                        0 if x.icon else 1,
                        0 if x.group_id else 1,
                        0 if (x.budget_limit and x.budget_limit > 0) else 1,
                        x.id
                    )
                )[0]
                
                duplicate_ids = [c.id for c in cat_list if c.id != canonical.id]
                
                # Fundir metadados para a canónica
                for dup in cat_list:
                    if dup.id != canonical.id:
                        if not canonical.icon and dup.icon:
                            canonical.icon = dup.icon
                        if not canonical.group_id and dup.group_id:
                            canonical.group_id = dup.group_id
                        if not canonical.budget_limit and dup.budget_limit:
                            canonical.budget_limit = dup.budget_limit
                        if (not canonical.color or canonical.color == '#3b82f6') and dup.color and dup.color != '#3b82f6':
                            canonical.color = dup.color
                
                if duplicate_ids:
                    # 1. Reatribuir transações
                    db.query(models.Transaction).filter(
                        models.Transaction.user_id == user_id,
                        models.Transaction.category_id.in_(duplicate_ids)
                    ).update({models.Transaction.category_id: canonical.id}, synchronize_session=False)
                    
                    # 2. Reatribuir metas
                    db.query(models.Goal).filter(
                        models.Goal.user_id == user_id,
                        models.Goal.category_id.in_(duplicate_ids)
                    ).update({models.Goal.category_id: canonical.id}, synchronize_session=False)
                    
                    # 3. Eliminar categorias duplicadas
                    db.query(models.Category).filter(
                        models.Category.user_id == user_id,
                        models.Category.id.in_(duplicate_ids)
                    ).delete(synchronize_session=False)
                    
                    modified = True
        if modified:
            db.commit()
    except Exception as e:
        print("Erro ao unificar categorias duplicadas:", e)
        db.rollback()

run_migrations()

app = FastAPI(title="Davi Finance API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
except ImportError:
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    limiter = DummyLimiter()

# ----------------- AUTH -----------------
@app.post("/token", response_model=schemas.Token)
@limiter.limit("15/minute")
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.put("/users/me/profile", response_model=schemas.UserResponse)
def update_user_profile(
    update_data: schemas.UserUpdateProfile,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if update_data.name is not None:
        trimmed = update_data.name.strip()
        current_user.name = trimmed if trimmed else None
    if update_data.profile_image is not None:
        current_user.profile_image = update_data.profile_image
    db.commit()
    db.refresh(current_user)
    return current_user

@app.put("/users/me/profile-image", response_model=schemas.UserResponse)
def update_profile_image(
    update_data: schemas.UserUpdateProfileImage,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    current_user.profile_image = update_data.profile_image
    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Utilizador já existe")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Criar categorias padrão
    default_categories = [
        models.Category(name="Salário", type=models.CategoryType.INCOME, color="#10b981", user_id=new_user.id),
        models.Category(name="Outras Receitas", type=models.CategoryType.INCOME, color="#34d399", user_id=new_user.id),
        models.Category(name="Alimentação", type=models.CategoryType.EXPENSE, color="#f43f5e", user_id=new_user.id),
        models.Category(name="Habitação", type=models.CategoryType.EXPENSE, color="#6366f1", user_id=new_user.id),
        models.Category(name="Transporte", type=models.CategoryType.EXPENSE, color="#f59e0b", user_id=new_user.id)
    ]
    db.add_all(default_categories)
    db.commit()
    
    return new_user

# ----------------- CATEGORY GROUPS -----------------
@app.get("/category-groups", response_model=List[schemas.CategoryGroupResponse])
def read_category_groups(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    groups = db.query(models.CategoryGroup).filter(models.CategoryGroup.user_id == current_user.id).all()
    res = []
    for g in groups:
        cat_ids = [c.id for c in g.categories]
        res.append(schemas.CategoryGroupResponse(
            id=g.id,
            user_id=g.user_id,
            name=g.name,
            color=g.color,
            icon=g.icon,
            type=g.type,
            created_at=g.created_at,
            category_ids=cat_ids
        ))
    return res

@app.post("/category-groups", response_model=schemas.CategoryGroupResponse)
def create_category_group(group_data: schemas.CategoryGroupCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_group = models.CategoryGroup(
        name=group_data.name,
        color=group_data.color,
        icon=group_data.icon,
        type=group_data.type,
        user_id=current_user.id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    if group_data.category_ids:
        for cat_id in group_data.category_ids:
            cat = db.query(models.Category).filter(models.Category.id == cat_id, models.Category.user_id == current_user.id).first()
            if cat:
                cat.group_id = db_group.id
        db.commit()
    
    return schemas.CategoryGroupResponse(
        id=db_group.id,
        user_id=db_group.user_id,
        name=db_group.name,
        color=db_group.color,
        icon=db_group.icon,
        type=db_group.type,
        created_at=db_group.created_at,
        category_ids=group_data.category_ids or []
    )

@app.put("/category-groups/{group_id}", response_model=schemas.CategoryGroupResponse)
def update_category_group(group_id: int, group_data: schemas.CategoryGroupCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_group = db.query(models.CategoryGroup).filter(models.CategoryGroup.id == group_id, models.CategoryGroup.user_id == current_user.id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Category group not found")
    
    db_group.name = group_data.name
    db_group.color = group_data.color
    db_group.icon = group_data.icon
    db_group.type = group_data.type
    
    # Reset old associations
    existing_cats = db.query(models.Category).filter(models.Category.group_id == group_id, models.Category.user_id == current_user.id).all()
    for c in existing_cats:
        c.group_id = None
    
    # Assign new associations
    if group_data.category_ids:
        for cat_id in group_data.category_ids:
            cat = db.query(models.Category).filter(models.Category.id == cat_id, models.Category.user_id == current_user.id).first()
            if cat:
                cat.group_id = db_group.id
                
    db.commit()
    db.refresh(db_group)
    
    return schemas.CategoryGroupResponse(
        id=db_group.id,
        user_id=db_group.user_id,
        name=db_group.name,
        color=db_group.color,
        icon=db_group.icon,
        type=db_group.type,
        created_at=db_group.created_at,
        category_ids=group_data.category_ids or []
    )

@app.delete("/category-groups/{group_id}")
def delete_category_group(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_group = db.query(models.CategoryGroup).filter(models.CategoryGroup.id == group_id, models.CategoryGroup.user_id == current_user.id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Category group not found")
    
    cats = db.query(models.Category).filter(models.Category.group_id == group_id, models.Category.user_id == current_user.id).all()
    for c in cats:
        c.group_id = None
        
    db.delete(db_group)
    db.commit()
    return {"message": "Category group deleted"}

# ----------------- CATEGORIES -----------------
@app.post("/categories", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    cleaned_name = category.name.strip() if category.name else ""
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="O nome da categoria não pode estar vazio.")
        
    # Verificar se já existe categoria com o mesmo nome e tipo (case-insensitive)
    existing = db.query(models.Category).filter(
        models.Category.user_id == current_user.id,
        models.Category.type == category.type,
        func.lower(func.trim(models.Category.name)) == func.lower(cleaned_name)
    ).first()
    
    if existing:
        type_label = "despesa" if str(category.type.value if hasattr(category.type, 'value') else category.type).lower() == "expense" else "receita"
        raise HTTPException(status_code=400, detail=f"Já existe uma categoria de {type_label} com o nome '{cleaned_name}'.")

    category_data = category.model_dump()
    category_data["name"] = cleaned_name
    db_category = models.Category(**category_data, user_id=current_user.id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    group_name = db_category.group.name if db_category.group else None
    return schemas.CategoryResponse(
        id=db_category.id,
        user_id=db_category.user_id,
        name=db_category.name,
        color=db_category.color,
        icon=db_category.icon,
        type=db_category.type,
        budget_limit=db_category.budget_limit,
        group_id=db_category.group_id,
        group_name=group_name
    )

@app.get("/categories", response_model=list[schemas.CategoryResponse])
def read_categories(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    deduplicate_user_categories(current_user.id, db)
    categories = db.query(models.Category).filter(models.Category.user_id == current_user.id).all()
    res = []
    for c in categories:
        group_name = c.group.name if c.group else None
        res.append(schemas.CategoryResponse(
            id=c.id,
            user_id=c.user_id,
            name=c.name,
            color=c.color,
            icon=c.icon,
            type=c.type,
            budget_limit=c.budget_limit,
            group_id=c.group_id,
            group_name=group_name
        ))
    return res

@app.post("/categories/merge-duplicates", response_model=list[schemas.CategoryResponse])
def merge_duplicate_categories(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    deduplicate_user_categories(current_user.id, db)
    return read_categories(db=db, current_user=current_user)

@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    category = db.query(models.Category).filter(models.Category.id == category_id, models.Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}

@app.put("/categories/{category_id}", response_model=schemas.CategoryResponse)
def update_category(category_id: int, category_update: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    category = db.query(models.Category).filter(models.Category.id == category_id, models.Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    cleaned_name = category_update.name.strip() if category_update.name else ""
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="O nome da categoria não pode estar vazio.")
        
    # Verificar se já existe OUTRA categoria com o mesmo nome e tipo (case-insensitive)
    existing = db.query(models.Category).filter(
        models.Category.user_id == current_user.id,
        models.Category.id != category_id,
        models.Category.type == category_update.type,
        func.lower(func.trim(models.Category.name)) == func.lower(cleaned_name)
    ).first()
    
    if existing:
        type_label = "despesa" if str(category_update.type.value if hasattr(category_update.type, 'value') else category_update.type).lower() == "expense" else "receita"
        raise HTTPException(status_code=400, detail=f"Já existe outra categoria de {type_label} com o nome '{cleaned_name}'.")
    
    for key, value in category_update.model_dump().items():
        if key == "name":
            setattr(category, key, cleaned_name)
        else:
            setattr(category, key, value)
        
    db.commit()
    db.refresh(category)
    group_name = category.group.name if category.group else None
    return schemas.CategoryResponse(
        id=category.id,
        user_id=category.user_id,
        name=category.name,
        color=category.color,
        icon=category.icon,
        type=category.type,
        budget_limit=category.budget_limit,
        group_id=category.group_id,
        group_name=group_name
    )

# ----------------- TRANSACTIONS -----------------
@app.post("/transactions", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    category = db.query(models.Category).filter(models.Category.id == transaction.category_id, models.Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category_id")
    
    db_transaction = models.Transaction(**transaction.model_dump(), user_id=current_user.id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.get("/transactions", response_model=list[schemas.TransactionResponse])
def read_transactions(
    year: Optional[int] = None,
    month: Optional[int] = None,
    type: Optional[str] = None,
    category_id: Optional[int] = None,
    payment_method: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    if year:
        query = query.filter(extract('year', models.Transaction.date) == year)
    if month:
        query = query.filter(extract('month', models.Transaction.date) == month)
    if type:
        query = query.filter(models.Transaction.type == type)
    if category_id:
        query = query.filter(models.Transaction.category_id == category_id)
    if payment_method:
        query = query.filter(models.Transaction.payment_method == payment_method)
        
    return query.order_by(models.Transaction.date.desc()).all()

@app.put("/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction(
    transaction_id: int, 
    transaction_update: schemas.TransactionUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    db_transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id, 
        models.Transaction.user_id == current_user.id
    ).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    update_data = transaction_update.model_dump(exclude_unset=True)
    if "category_id" in update_data and update_data["category_id"] is not None:
        cat = db.query(models.Category).filter(
            models.Category.id == update_data["category_id"], 
            models.Category.user_id == current_user.id
        ).first()
        if not cat:
            raise HTTPException(status_code=400, detail="Invalid category_id")

    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id, models.Transaction.user_id == current_user.id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted"}

# ----------------- INVESTMENTS -----------------
@app.post("/investments", response_model=schemas.InvestmentResponse)
def create_investment(investment: schemas.InvestmentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_investment = models.Investment(**investment.model_dump(), user_id=current_user.id)
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    
    log = models.InvestmentLog(
        investment_id=db_investment.id,
        amount=db_investment.balance,
        type=models.InvestmentLogType.CONTRIBUTION
    )
    db.add(log)
    db.commit()
    
    return db_investment

@app.get("/investments", response_model=list[schemas.InvestmentResponse])
def read_investments(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Investment).filter(models.Investment.user_id == current_user.id).all()

@app.put("/investments/{investment_id}", response_model=schemas.InvestmentResponse)
def update_investment(investment_id: int, investment: schemas.InvestmentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_investment = db.query(models.Investment).filter(models.Investment.id == investment_id, models.Investment.user_id == current_user.id).first()
    if not db_investment:
        raise HTTPException(status_code=404, detail="Investment not found")
        
    old_balance = db_investment.balance
    
    for key, value in investment.model_dump().items():
        setattr(db_investment, key, value)
        
    if old_balance != db_investment.balance:
        diff = db_investment.balance - old_balance
        log = models.InvestmentLog(
            investment_id=db_investment.id,
            amount=diff,
            type=models.InvestmentLogType.CONTRIBUTION if diff > 0 else models.InvestmentLogType.YIELD
        )
        db.add(log)
        
    db.commit()
    db.refresh(db_investment)
    return db_investment

@app.delete("/investments/{investment_id}")
def delete_investment(investment_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_investment = db.query(models.Investment).filter(models.Investment.id == investment_id, models.Investment.user_id == current_user.id).first()
    if not db_investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    db.delete(db_investment)
    db.commit()
    return {"message": "Investment deleted"}

@app.post("/investments/{investment_id}/withdraw")
@app.post("/investments/{investment_id}/withdraw/")
def withdraw_investment(
    investment_id: int, 
    req: schemas.WithdrawalRequest, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    db_investment = db.query(models.Investment).filter(
        models.Investment.id == investment_id, 
        models.Investment.user_id == current_user.id
    ).first()
    if not db_investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="O montante a retirar deve ser maior que zero")
    
    if req.amount > db_investment.balance:
        raise HTTPException(status_code=400, detail="Saldo insuficiente no investimento selecionado")
    
    # 1. Update investment balance
    db_investment.balance -= req.amount
    
    # 2. Log withdrawal in investment logs
    log = models.InvestmentLog(
        investment_id=db_investment.id,
        amount=req.amount,
        type=models.InvestmentLogType.YIELD,
        date=datetime.utcnow()
    )
    db.add(log)
    
    # 3. If transfer to current balance is requested
    if req.transfer_to_balance:
        # Find or create Category 'Investimento - Saída'
        cat = db.query(models.Category).filter(
            models.Category.user_id == current_user.id,
            models.Category.name == "Investimento - Saída"
        ).first()
        if not cat:
            cat = models.Category(
                user_id=current_user.id,
                name="Investimento - Saída",
                color="#3b82f6",
                type=models.CategoryType.INCOME
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)
        
        # Create transfer transaction
        trans = models.Transaction(
            user_id=current_user.id,
            category_id=cat.id,
            amount=req.amount,
            date=datetime.utcnow(),
            description=f"Investimento - Saída ({db_investment.name})",
            type=models.TransactionType.INCOME,
            is_transfer=True
        )
        db.add(trans)
    
    db.commit()
    db.refresh(db_investment)
    return {"message": "Retirada efetuada com sucesso", "balance": db_investment.balance}

@app.get("/investments/history")
def get_investment_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    investments = db.query(models.Investment).filter(models.Investment.user_id == current_user.id).all()
    
    # Backfill para utilizadores antigos que não tenham logs
    for inv in investments:
        if not inv.logs:
            initial_log = models.InvestmentLog(
                investment_id=inv.id,
                amount=inv.balance,
                type=models.InvestmentLogType.CONTRIBUTION,
                date=datetime.utcnow()
            )
            db.add(initial_log)
    db.commit()

    logs = db.query(models.InvestmentLog).join(models.Investment).filter(models.Investment.user_id == current_user.id).order_by(models.InvestmentLog.date.asc()).all()

    timeline = []
    current_total = 0.0
    
    if logs:
        first_date = logs[0].date - timedelta(days=1)
        timeline.append({
            "date": datetime(first_date.year, first_date.month, first_date.day),
            "total": 0.0
        })
        
    for log in logs:
        current_total += log.amount
        timeline.append({
            "date": log.date,
            "total": current_total
        })

    filtered = []
    for item in timeline:
        d = item["date"]
        if year and year != 0 and d.year != year:
            continue
        if month and month != 0 and d.month != month:
            continue
        if day and day != 0 and d.day != day:
            continue
        filtered.append(item)

    chart_data = []
    grouped_data = {}
    
    for item in filtered:
        d = item["date"]
        if day and day != 0:
            label = d.strftime("%H:00")
        elif month and month != 0:
            label = d.strftime("%d/%m")
        else:
            label = d.strftime("%d %b %Y")
        
        grouped_data[label] = round(item["total"], 2)
        
    for label, val in grouped_data.items():
        chart_data.append({
            "name": label,
            "valor": val
        })
        
    if not chart_data and investments:
        total_patrimony = sum(i.balance for i in investments)
        chart_data = [{"name": "Atual", "valor": round(total_patrimony, 2)}]

    return chart_data

# ----------------- SUMMARY -----------------
@app.get("/summary")
def get_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    now = datetime.now()
    
    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    all_transactions = query.all()
    investments = db.query(models.Investment).filter(models.Investment.user_id == current_user.id).all()
    
    selected_transactions = []
    for t in all_transactions:
        if year and t.date.year != year:
            continue
        if month and t.date.month != month:
            continue
        selected_transactions.append(t)
        
    effective_selected_transactions = [t for t in selected_transactions if t.date <= now]
    
    total_income = sum(t.amount for t in effective_selected_transactions if t.type == models.TransactionType.INCOME and not getattr(t, 'is_transfer', False))
    total_expense = sum(t.amount for t in effective_selected_transactions if t.type == models.TransactionType.EXPENSE)
    total_invested = sum(i.balance for i in investments)
    
    if year and month:
        last_day = calendar.monthrange(year, month)[1]
        end_of_period = datetime(year, month, last_day, 23, 59, 59)
        balance_cutoff = min(end_of_period, now)
    elif year:
        end_of_period = datetime(year, 12, 31, 23, 59, 59)
        balance_cutoff = min(end_of_period, now)
    else:
        balance_cutoff = now
        
    cumulative_income = sum(t.amount for t in all_transactions if t.type == models.TransactionType.INCOME and t.date <= balance_cutoff)
    cumulative_expense = sum(t.amount for t in all_transactions if t.type == models.TransactionType.EXPENSE and t.date <= balance_cutoff)
    cumulative_balance = cumulative_income - cumulative_expense
    
    chart_data = []
    
    if year and month:
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            daily_income = sum(t.amount for t in effective_selected_transactions if t.date.day == day and t.type == models.TransactionType.INCOME and not getattr(t, 'is_transfer', False))
            daily_expense = sum(t.amount for t in effective_selected_transactions if t.date.day == day and t.type == models.TransactionType.EXPENSE)
            chart_data.append({
                "name": str(day),
                "receitas": daily_income,
                "despesas": daily_expense,
                "saldo": round(daily_income - daily_expense, 2),
                "poupanca": round(max(0.0, daily_income - daily_expense), 2)
            })
    else:
        months_abbr = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        for m in range(1, 13):
            monthly_income = sum(t.amount for t in effective_selected_transactions if t.date.month == m and t.type == models.TransactionType.INCOME and not getattr(t, 'is_transfer', False))
            monthly_expense = sum(t.amount for t in effective_selected_transactions if t.date.month == m and t.type == models.TransactionType.EXPENSE)
            chart_data.append({
                "name": months_abbr[m-1],
                "receitas": monthly_income,
                "despesas": monthly_expense,
                "saldo": round(monthly_income - monthly_expense, 2),
                "poupanca": round(max(0.0, monthly_income - monthly_expense), 2)
            })

    return {
        "balance": cumulative_balance,
        "income": total_income,
        "expense": total_expense,
        "investments": total_invested,
        "chartData": chart_data
    }

@app.get("/reports/history")
def get_reports_history(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).all()
    
    history_map = {}
    for t in transactions:
        year = t.date.year
        month = t.date.month
        key = f"{year}-{month:02d}"
        
        if key not in history_map:
            history_map[key] = {
                "year": year,
                "month": month,
                "income": 0,
                "expense": 0,
            }
            
        if t.type == models.TransactionType.INCOME and not getattr(t, 'is_transfer', False):
            history_map[key]["income"] += t.amount
        elif t.type == models.TransactionType.EXPENSE:
            history_map[key]["expense"] += t.amount
            
    history_list = []
    for k, v in history_map.items():
        v["balance"] = v["income"] - v["expense"]
        history_list.append(v)
        
    history_list.sort(key=lambda x: (x["year"], x["month"]), reverse=True)
    return history_list

# ----------------- SIMULATIONS -----------------
@app.post("/simulations", response_model=schemas.SimulationResponse)
def create_simulation(sim: schemas.SimulationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_sim = models.Simulation(
        user_id=current_user.id,
        name=sim.name,
        incomes_data=sim.incomes_data,
        expenses_data=sim.expenses_data
    )
    db.add(db_sim)
    db.commit()
    db.refresh(db_sim)
    return db_sim

@app.get("/simulations", response_model=List[schemas.SimulationResponse])
def get_simulations(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Simulation).filter(models.Simulation.user_id == current_user.id).order_by(models.Simulation.created_at.desc()).all()

@app.delete("/simulations/{sim_id}")
def delete_simulation(sim_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_sim = db.query(models.Simulation).filter(models.Simulation.id == sim_id, models.Simulation.user_id == current_user.id).first()
    if not db_sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    db.delete(db_sim)
    db.commit()
    return {"message": "Simulation deleted"}

# ----------------- GOALS -----------------
@app.post("/goals", response_model=schemas.GoalResponse)
@app.post("/goals/", response_model=schemas.GoalResponse)
def create_goal(goal: schemas.GoalCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_goal = models.Goal(**goal.model_dump(), user_id=current_user.id)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    category_name = db_goal.category.name if db_goal.category else None
    investment_name = db_goal.investment.name if db_goal.investment else None
    return schemas.GoalResponse(
        id=db_goal.id,
        user_id=db_goal.user_id,
        title=db_goal.title,
        goal_type=db_goal.goal_type,
        target_amount=db_goal.target_amount,
        category_id=db_goal.category_id,
        investment_id=db_goal.investment_id,
        month=db_goal.month,
        year=db_goal.year,
        created_at=db_goal.created_at,
        category_name=category_name,
        investment_name=investment_name
    )

@app.get("/goals", response_model=List[schemas.GoalResponse])
@app.get("/goals/", response_model=List[schemas.GoalResponse])
def get_goals(year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = db.query(models.Goal).filter(models.Goal.user_id == current_user.id)
    if year is not None:
        query = query.filter(models.Goal.year == year)
    if month is not None:
        query = query.filter(models.Goal.month == month)
    goals = query.order_by(models.Goal.created_at.desc()).all()
    
    result = []
    for g in goals:
        category_name = g.category.name if g.category else None
        investment_name = g.investment.name if g.investment else None
        result.append(schemas.GoalResponse(
            id=g.id,
            user_id=g.user_id,
            title=g.title,
            goal_type=g.goal_type,
            target_amount=g.target_amount,
            category_id=g.category_id,
            investment_id=g.investment_id,
            month=g.month,
            year=g.year,
            created_at=g.created_at,
            category_name=category_name,
            investment_name=investment_name
        ))
    return result

@app.put("/goals/{goal_id}", response_model=schemas.GoalResponse)
def update_goal(goal_id: int, goal_data: schemas.GoalUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_goal = db.query(models.Goal).filter(models.Goal.id == goal_id, models.Goal.user_id == current_user.id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    update_dict = goal_data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(db_goal, k, v)
    
    db.commit()
    db.refresh(db_goal)
    category_name = db_goal.category.name if db_goal.category else None
    investment_name = db_goal.investment.name if db_goal.investment else None
    return schemas.GoalResponse(
        id=db_goal.id,
        user_id=db_goal.user_id,
        title=db_goal.title,
        goal_type=db_goal.goal_type,
        target_amount=db_goal.target_amount,
        category_id=db_goal.category_id,
        investment_id=db_goal.investment_id,
        month=db_goal.month,
        year=db_goal.year,
        created_at=db_goal.created_at,
        category_name=category_name,
        investment_name=investment_name
    )

@app.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_goal = db.query(models.Goal).filter(models.Goal.id == goal_id, models.Goal.user_id == current_user.id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(db_goal)
    db.commit()
    return {"message": "Goal deleted"}

