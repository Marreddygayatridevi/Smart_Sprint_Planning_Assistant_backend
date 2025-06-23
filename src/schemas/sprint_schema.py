from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class SprintCreateRequest(BaseModel):
    project_key: str = Field(..., description="Jira project key")
    sprint_name: str = Field(..., description="Name of the sprint")
    team_name: str = Field(..., description="Team name for assignment")

    class Config:
        json_schema_extra = {
            "example": {
                "project_key": "string",
                "sprint_name": "string",
                "team_name": "string"
            }
        }

class SprintAssignmentResponse(BaseModel):
    sprint_name: str = Field(..., description="Name of the sprint")
    issue_key: str = Field(..., description="Jira issue key")
    assignee_name: str = Field(..., description="Assigned user name")
    title: str = Field(..., description="Issue title")
    estimated_days: int = Field(..., description="Estimated days to complete")
    story_points: int = Field(..., description="Story points assigned to the issue")
    
    class Config:
        from_attributes = True

class StoryPointEstimate(BaseModel):
    issue_key: str = Field(..., description="Jira issue key")
    title: str = Field(..., description="Issue title")
    estimated_story_points: int = Field(..., description="Estimated story points (1-10)")
    complexity_reasoning: str = Field(..., description="Reasoning for the complexity assessment")
    
    class Config:
        from_attributes = True

class UserSkillAnalysis(BaseModel):
    user_id: int
    username: str
    role: str
    team: str
    tickets_solved: int
    skill_category: Literal["frontend", "backend", "testing", "fullstack"] = Field(..., description="Primary skill category")
    experience_level: Literal["intern", "junior", "senior"] = Field(..., description="Experience level")
    capacity_score: float = Field(..., description="Current capacity score based on tickets solved")
    
    class Config:
        from_attributes = True