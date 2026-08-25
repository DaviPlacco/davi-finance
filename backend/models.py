from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean, Text
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
    name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    profile_image = Column(Text(length=4294967295), nullable=True)

    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    category_groups = relationship("CategoryGroup", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="user", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")

class CategoryGroup(Base):
    __tablename__ = "category_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(50), default="#6366f1")
    type = Column(Enum(CategoryType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="category_groups")
    categories = relationship("Category", back_populates="group")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(50), default="#3b82f6")
    type = Column(Enum(CategoryType), nullable=False)
    budget_limit = Column(Float, nullable=True)
    group_id = Column(Integer, ForeignKey("category_groups.id", ondelete="SET NULL"), nullable=True)
    
    user = relationship("User", back_populates="categories")
    group = relationship("CategoryGroup", back_populates="categories")
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
    receipt_image = Column(Text(length=4294967295), nullable=True)

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

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    incomes_data = Column(Text(length=4294967295), nullable=False)
    expenses_data = Column(Text(length=4294967295), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="simulations")

class InvestmentLog(Base):
    __tablename__ = "investment_logs"

    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    type = Column(Enum(InvestmentLogType), nullable=False)
    
    investment = relationship("Investment", back_populates="logs")

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    goal_type = Column(String(50), nullable=False)  # investment_deposit, expense_ceiling, savings_rate, net_savings
    target_amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")
    category = relationship("Category")
    investment = relationship("Investment")
