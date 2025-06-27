# from sqlalchemy.orm import Session
# from fastapi import HTTPException
# from src.models.user import User
# from src.models.team import Team
# from typing import List

# class TeamService:
#     @staticmethod
#     def get_users_by_team(team_name: str, db: Session) -> List[User]:
#         users = db.query(User).filter(User.team == team_name).all()
#         if not users:
#             raise HTTPException(status_code=404, detail=f"No users found in team '{team_name}'")
#         return users

#     @staticmethod
#     def get_all_teams(db: Session) -> List[Team]:
#         return db.query(Team).all()

#     @staticmethod
#     def get_team_by_name(team_name: str, db: Session) -> Team:
#         team = db.query(Team).filter(Team.name == team_name).first()
#         if not team:
#             raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
#         return team

from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.user import User
from src.models.team import Team
from typing import List

class TeamService:
    # Define default teams that should always be available
    DEFAULT_TEAMS = [
        {"id": 1, "name": "alpha"},
        {"id": 2, "name": "beta"},
        {"id": 3, "name": "delta"},
        {"id": 4, "name": "gamma"},
        {"id": 5, "name": "developer"},
        {"id": 6, "name": "designer"},
    ]
    
    @staticmethod
    def get_users_by_team(team_name: str, db: Session) -> List[User]:
        users = db.query(User).filter(User.team == team_name).all()
        if not users:
            raise HTTPException(status_code=404, detail=f"No users found in team '{team_name}'")
        return users

    @staticmethod
    def get_all_teams(db: Session) -> List[Team]:
        # Get teams from database
        db_teams = db.query(Team).all()
        
        # Convert database teams to a set of names for easy lookup
        db_team_names = {team.name.lower() for team in db_teams}
        
        # Create a list to store the final result
        all_teams = []
        
        # Add database teams first
        all_teams.extend(db_teams)
        
        # Add default teams that are not in database
        for default_team in TeamService.DEFAULT_TEAMS:
            if default_team["name"].lower() not in db_team_names:
                # Create a mock Team object for default teams
                # Note: These won't have real IDs or created_at from database
                mock_team = Team()
                mock_team.id = default_team["id"]
                mock_team.name = default_team["name"]
                mock_team.created_at = None  # or set a default datetime
                all_teams.append(mock_team)
        
        return all_teams

    @staticmethod
    def get_team_by_name(team_name: str, db: Session) -> Team:
        # First try to get from database
        team = db.query(Team).filter(Team.name == team_name).first()
        if team:
            return team
        
        # If not in database, check if it's a default team
        for default_team in TeamService.DEFAULT_TEAMS:
            if default_team["name"].lower() == team_name.lower():
                # Create a mock Team object for default team
                mock_team = Team()
                mock_team.id = default_team["id"]
                mock_team.name = default_team["name"]
                mock_team.created_at = None
                return mock_team
        
        # If not found in either database or defaults
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")