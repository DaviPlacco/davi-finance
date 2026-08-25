from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models import CategoryType, TransactionType, InvestmentLogType

# User Schemas
class UserBase(BaseModel):
    username: str
    name: Optional[str] = None
    profile_image: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdateProfileImage(BaseModel):
    profile_image: str

class UserUpdateProfile(BaseModel):
    name: Optional[str] = None
    profile_image: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Category Group Schemas
class CategoryGroupBase(BaseModel):
    name: str
    color: str = "#6366f1"
    type: CategoryType

class CategoryGroupCreate(CategoryGroupBase):
    category_ids: Optional[List[int]] = []

class CategoryGroupResponse(CategoryGroupBase):
    id: int
    user_id: int
    category_ids: Optional[List[int]] = []
    created_at: datetime
    class Config:
        from_attributes = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    color: str
    type: CategoryType
    budget_limit: Optional[float] = None
    group_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    group_name: Optional[str] = None
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionBase(BaseModel):
    category_id: int
    amount: float
    date: datetime
    description: Optional[str] = None
    type: TransactionType
    receipt_image: Optional[str] = None
    is_transfer: Optional[bool] = False

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class WithdrawalRequest(BaseModel):
    amount: float
    transfer_to_balance: bool = True

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

# Simulation Schemas
class SimulationBase(BaseModel):
    name: str
    incomes_data: str
    expenses_data: str

class SimulationCreate(SimulationBase):
    pass

class SimulationResponse(SimulationBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Goal Schemas
class GoalBase(BaseModel):
    title: str
    goal_type: str  # investment_deposit, expense_ceiling, savings_rate, net_savings
    target_amount: float
    category_id: Optional[int] = None
    investment_id: Optional[int] = None
    month: int
    year: int

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    goal_type: Optional[str] = None
    target_amount: Optional[float] = None
    category_id: Optional[int] = None
    investment_id: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None

class GoalResponse(GoalBase):
    id: int
    user_id: int
    created_at: datetime
    category_name: Optional[str] = None
    investment_name: Optional[str] = None
    class Config:
        from_attributes = True

