from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.api.dependencies import db_dependency
from src.schemas.team_schema import (
    TeamResponse, 
    TeamWithUsersResponse
)
from src.services.team_service import TeamService
from src.api.dependencies import db_dependency, current_user_dependency

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/", response_model=List[TeamResponse])
async def list_all_teams(db: db_dependency):
    return TeamService.get_all_teams(db)

@router.get("/{team_name}", response_model=TeamWithUsersResponse)
async def get_team_details(team_name: str, db: db_dependency):
    team = TeamService.get_team_by_name(team_name, db)
    users = TeamService.get_users_by_team(team_name, db)
    
    return TeamWithUsersResponse(
        id=team.id,
        name=team.name,
        created_at=team.created_at,
        users=users
    )