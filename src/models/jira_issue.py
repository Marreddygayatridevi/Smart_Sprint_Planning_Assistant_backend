from sqlalchemy import Column, String, Integer, Date,Text, Float, DateTime, func
from src.database.db import Base

class JiraIssue(Base):
    __tablename__ = "jira_issues"

    id = Column(Integer, primary_key=True,index=True,autoincrement=True) 
    key = Column(String, unique=True, nullable=False)  
    project_key = Column(String, nullable=False)  
    title = Column(String, nullable=False)  
    description = Column(Text)  
    priority = Column(String, default="Medium")  
    story_points = Column(Float)  
    assignee = Column(String)  
    status = Column(String, nullable=False) 
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())  
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  
    last_synced_at = Column(DateTime, default=func.now())  