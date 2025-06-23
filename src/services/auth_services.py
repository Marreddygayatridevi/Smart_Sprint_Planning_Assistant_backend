from datetime import timedelta, datetime, timezone
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.user import User
from src.models.team import Team  
from src.utils.config import SECRET_KEY, ALGORITHM, JWT_EXPIRE_MINUTES

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt_context.verify(plain_password, hashed_password)

    @staticmethod
    def authenticate_user(username: str, password: str, db: Session) -> User:
        # Accept either username or email for login
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        if not user or not AuthService.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        return user

    @staticmethod
    def create_access_token(
        username: str,
        user_id: int,
        expires_delta: timedelta = None
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=JWT_EXPIRE_MINUTES)

        payload = {
            'sub': username,
            'id': user_id,
            'exp': datetime.now(timezone.utc) + expires_delta
        }

        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        db: Session,
        is_active: bool = True,
        role: str = "developer",
        team: str = "alpha",
        tickets_solved: int = 0
    ) -> User:
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            raise ValueError("Username or email already exists")
        
        existing_team = db.query(Team).filter(Team.name == team).first()
        if not existing_team:
            raise ValueError(f"Team '{team}' does not exist. Please create the team first.")

        hashed_password = AuthService.hash_password(password)

        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            role=role,
            team=team,
            tickets_solved=tickets_solved
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user
