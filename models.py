from pydantic import BaseModel
from typing import List, Optional
import datetime

class TicketBase(BaseModel):
    query: str

class TicketCreate(TicketBase):
    pass

class Ticket(TicketBase):
    id: int
    owner_id: int
    response: Optional[str] = None
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str = "employee"

class User(UserBase):
    id: int
    is_active: bool
    role: str
    tickets: List[Ticket] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    