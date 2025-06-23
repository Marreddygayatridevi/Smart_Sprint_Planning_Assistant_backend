from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.api.dependencies import db_dependency, current_user_dependency
from src.schemas.sprint_schema import SprintAssignmentResponse, SprintCreateRequest
from src.services.sprint_service import SprintService
from src.models.sprint import Sprint

router = APIRouter(prefix="/sprint", tags=["sprint"])
@router.post("/create-assignments", response_model=List[SprintAssignmentResponse])
async def create_sprint_assignments(
    request: SprintCreateRequest,
    db: db_dependency,
    current_user: current_user_dependency
):
    """Create and save sprint assignments"""
    try:
        assignments = await SprintService.create_sprint_assignments(
            project_key=request.project_key,
            sprint_name=request.sprint_name,
            team_name=request.team_name,
            db=db
        )
        return assignments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sprint assignments: {str(e)}"
        )


@router.get("/assignments", response_model=List[SprintAssignmentResponse])
async def get_all_sprint_assignments(
    db: db_dependency,
    current_user: current_user_dependency
):
    """Get all existing sprint assignments"""
    try:
        # Query all sprint assignments from database
        assignments = db.query(Sprint).order_by(Sprint.sprint_name, Sprint.created_at).all()
        
        # Convert to response model
        return [
            SprintAssignmentResponse(
                sprint_name=assignment.sprint_name,
                issue_key=assignment.issue_key,
                assignee_name=assignment.assignee_name,
                title=assignment.title,
                estimated_days=assignment.estimated_days,
                story_points=assignment.story_points
            )
            for assignment in assignments
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sprint assignments: {str(e)}"
        )