from pydantic import BaseModel, Field
from typing import List


class SprintReport(BaseModel):
    issue_key: str = Field(..., description="Jira issue key")
    assignee_name: str = Field(..., description="Assigned user name")
    title: str = Field(..., description="Issue title")
    summary: str = Field(..., description="Summary of what was done during the sprint")
    details: str = Field(..., description="Key implementation details")
    recommendations: List[str] = Field(..., description="AI-generated suggestions for improvement")


class RiskItem(BaseModel):
    risk: str = Field(..., description="Description of the risk")
    severity: str = Field(..., description="Risk severity: Low, Medium, High")
    impacted_person: List[str] = Field(..., description="Names of team member impacted")
