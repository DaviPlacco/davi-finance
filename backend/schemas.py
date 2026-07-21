from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models import CategoryType, TransactionType, InvestmentLogType

# User Schemas
class UserBase(BaseModel):
    username: str
    profile_image: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdateProfileImage(BaseModel):
    profile_image: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    color: str
    type: CategoryType
    budget_limit: Optional[float] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionBase(BaseModel):
    category_id: int
    amount: float
    date: datetime
    description: Optional[str] = None
    type: TransactionType

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

# Investment Schemas
class InvestmentBase(BaseModel):
    name: str
    asset_type: str
    balance: float = 0.0
    target: Optional[float] = None

class InvestmentCreate(InvestmentBase):
    pass

class InvestmentResponse(InvestmentBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True
