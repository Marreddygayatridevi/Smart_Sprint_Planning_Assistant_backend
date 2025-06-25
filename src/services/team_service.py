from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.user import User
from src.models.team import Team
from typing import List

class TeamService:
    @staticmethod
    def get_users_by_team(team_name: str, db: Session) -> List[User]:
        users = db.query(User).filter(User.team == team_name).all()
        if not users:
            raise HTTPException(status_code=404, detail=f"No users found in team '{team_name}'")
        return users

    @staticmethod
    def get_all_teams(db: Session) -> List[Team]:
        return db.query(Team).all()

    @staticmethod
    def get_team_by_name(team_name: str, db: Session) -> Team:
        team = db.query(Team).filter(Team.name == team_name).first()
        if not team:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
        return team
