from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.db import Base

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    sprint_name = Column(String, nullable=False, index=True)
    issue_key = Column(String, nullable=False, index=True)
    assignee_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    estimated_days = Column(Integer, nullable=False)
    story_points = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Sprint(id={self.id}, sprint_name='{self.sprint_name}', issue_key='{self.issue_key}', assignee='{self.assignee_name}')>"
