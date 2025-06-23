from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from src.api.dependencies import db_dependency
from src.services.ai_service import AIService
from src.schemas.ai_schema import SprintReport, RiskItem

router = APIRouter(prefix="/ai", tags=["AI"])

@router.get("/sprint-report/{issue_key}", response_model=SprintReport)
async def get_sprint_report(issue_key: str, db: db_dependency):  
    """
    Generate sprint report for a specific Jira issue.
    """
    try:
        report = await AIService.generate_task_report(issue_key=issue_key, db=db)  
        return report
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI failed: {str(e)}")


@router.get("/risk-identification", response_model=Dict[str, List[RiskItem]])
async def identify_sprint_risks(db: db_dependency):
    """
    Use OpenAI to identify risks across current sprint tasks.
    """
    try:
        risks = await AIService.identify_risks(db)
        return risks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")
