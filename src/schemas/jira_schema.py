from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import date

class JiraIssueCreate(BaseModel):
    project_key: str
    title: str
    description: Optional[str] = ""
    priority: Literal["High", "Medium", "Low"] = "Medium"
    story_points: Optional[float] = None
    assignee: Optional[str] = None
    status: Literal["To Do", "In Progress", "Done"] = "To Do"
    due_date: Optional[date] = None 

class JiraIssueResponse(BaseModel):
    id: Optional[int] = None  
    key: str
    title: str
    description: str
    story_points: Optional[float] = None
    priority: Literal["High", "Medium", "Low"] = Field(default="")
    assignee: Optional[str] = None
    status: Optional[str]
    due_date: Optional[date] 
    
class JiraIssueUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    assignee: Optional[str]
    due_date: Optional[str]
    priority: Optional[str]
    status: Optional[str]
    due_date: Optional[date] = None 