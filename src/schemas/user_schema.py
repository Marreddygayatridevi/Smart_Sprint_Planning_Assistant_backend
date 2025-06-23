from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_active: bool = True
    role: Optional[str] = "developer"
    team: Optional[str] = "alpha"
    tickets_solved: Optional[int] = 0


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    role: str
    tickets_solved: int
    team:str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
