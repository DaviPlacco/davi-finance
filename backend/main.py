from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import timedelta, datetime
import calendar
import random
from typing import Optional
import models, schemas, auth
from database import engine, get_db
import os
from dotenv import load_dotenv

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Davi Finance API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- AUTH -----------------
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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

# ----------------- CATEGORIES -----------------
@app.post("/categories", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_category = models.Category(**category.model_dump(), user_id=current_user.id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories", response_model=list[schemas.CategoryResponse])
def read_categories(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Category).filter(models.Category.user_id == current_user.id).all()

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
    
    for key, value in category_update.model_dump().items():
        setattr(category, key, value)
        
    db.commit()
    db.refresh(category)
    return category

# ----------------- TRANSACTIONS -----------------
@app.post("/transactions", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Verify category belongs to user
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
        
    return query.order_by(models.Transaction.date.desc()).all()

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
    
    # O primeiro ponto do gráfico começa no dia anterior ao primeiro log com saldo 0
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

# Get summary
@app.get("/summary")
def get_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    if year:
        query = query.filter(extract('year', models.Transaction.date) == year)
    if month:
        query = query.filter(extract('month', models.Transaction.date) == month)
        
    transactions = query.all()
    investments = db.query(models.Investment).filter(models.Investment.user_id == current_user.id).all()
    
    total_income = sum(t.amount for t in transactions if t.type == models.TransactionType.INCOME)
    total_expense = sum(t.amount for t in transactions if t.type == models.TransactionType.EXPENSE)
    total_invested = sum(i.balance for i in investments)
    
    chart_data = []
    
    # Group chart data
    if year and month:
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            daily_income = sum(t.amount for t in transactions if t.date.day == day and t.type == models.TransactionType.INCOME)
            daily_expense = sum(t.amount for t in transactions if t.date.day == day and t.type == models.TransactionType.EXPENSE)
            chart_data.append({
                "name": str(day),
                "receitas": daily_income,
                "despesas": daily_expense
            })
    else:
        months_abbr = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        for m in range(1, 13):
            monthly_income = sum(t.amount for t in transactions if t.date.month == m and t.type == models.TransactionType.INCOME)
            monthly_expense = sum(t.amount for t in transactions if t.date.month == m and t.type == models.TransactionType.EXPENSE)
            chart_data.append({
                "name": months_abbr[m-1],
                "receitas": monthly_income,
                "despesas": monthly_expense
            })

    return {
        "balance": total_income - total_expense,
        "income": total_income,
        "expense": total_expense,
        "investments": total_invested,
        "chartData": chart_data
    }
