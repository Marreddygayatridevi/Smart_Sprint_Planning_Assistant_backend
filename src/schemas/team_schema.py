from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class TeamCreate(BaseModel):
    name: str

    class Config:
        from_attributes:True

class TeamResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class TeamUserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    tickets_solved: int
    team: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TeamWithUsersResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    users: List[TeamUserResponse] = []

    class Config:
        from_attributes = True