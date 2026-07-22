from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base

class CategoryType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    INVESTMENT = "investment"

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class InvestmentLogType(str, enum.Enum):
    CONTRIBUTION = "contribution"
    YIELD = "yield"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    profile_image = Column(String(255), nullable=True)

    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="user", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(50), default="#3b82f6")
    type = Column(Enum(CategoryType), nullable=False)
    budget_limit = Column(Float, nullable=True)
    
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String(500))
    type = Column(Enum(TransactionType), nullable=False)

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)
    balance = Column(Float, default=0.0)
    target = Column(Float, nullable=True)
    
    user = relationship("User", back_populates="investments")
    logs = relationship("InvestmentLog", back_populates="investment", cascade="all, delete-orphan")

class InvestmentLog(Base):
    __tablename__ = "investment_logs"

    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    type = Column(Enum(InvestmentLogType), nullable=False)
    
    investment = relationship("Investment", back_populates="logs")
