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

    @staticmethod
    def delete_team(team_name: str, db: Session) -> bool:
        team = db.query(Team).filter(Team.name == team_name).first()
        if not team:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
        
        # Check if team has users
        users_in_team = db.query(User).filter(User.team == team_name).count()
        if users_in_team > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete team '{team_name}'. It has {users_in_team} users assigned to it."
            )
        
        db.delete(team)
        db.commit()
        return True