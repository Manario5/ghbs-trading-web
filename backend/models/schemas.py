from pydantic import BaseModel
from typing import Optional, List, Any

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: str

# System
class SystemHealth(BaseModel):
    status: str
    timestamp: str

class SystemVersion(BaseModel):
    ghbs_version: str
    tasi_version: str

# Endpoints
class DashboardSummary(BaseModel):
    equity: float
    open_positions: int
    portfolio_heat: float
    regime: str

class AccountSummary(BaseModel):
    starting_equity: float
    current_equity: float
    net_pnl: float
    win_rate: float
    total_trades: int

class PerformanceSummary(BaseModel):
    total_trades: int
    winners: int
    total_pnl: float
    avg_r: Optional[float]
    best_r: Optional[float]
    worst_r: Optional[float]

# Action Plan
class ActionPlanCreate(BaseModel):
    ticker: str
    action_type: str
    planned_price: Optional[float] = None
    planned_quantity: Optional[int] = None
    notes: Optional[str] = None

class ActionPlanItem(ActionPlanCreate):
    id: int
    status: str
    created_at: str

# Journal
class JournalCreate(BaseModel):
    ticker: str
    position_id: Optional[int] = None
    transaction_id: Optional[int] = None
    note_type: str
    note_text: str

class JournalEntry(JournalCreate):
    id: int
    created_at: str
