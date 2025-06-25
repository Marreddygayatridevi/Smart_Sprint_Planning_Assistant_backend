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
        """Hash a password using bcrypt"""
        return bcrypt_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def authenticate_user(username: str, password: str, db: Session) -> User:
        """
        Authenticate user with username/email and password
        Returns User object if authentication successful, None otherwise
        """
        # Accept either username or email for login
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No account found with this username or email.",
            )
        
        if not AuthService.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Please try again.",
            )
        
        return user
    
    @staticmethod
    def create_access_token(
        username: str,
        user_id: int,
        expires_delta: timedelta = None
    ) -> str:
        """Create JWT access token"""
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
        """
        Create a new user with comprehensive validation
        """
        # Validate input data
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        
        if not email or not email.strip():
            raise ValueError("Email cannot be empty")
        
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Clean input data
        username = username.strip()
        email = email.strip().lower()
        role = role.strip() if role else "developer"
        team = team.strip() if team else "alpha"
        
        # Check for existing username
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            raise ValueError(
                f"Change username, there is already a user with that name. "
                f"User '{username}' already exists with role '{existing_username.role}' in team '{existing_username.team}'."
            )
        
        # Check for existing email
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise ValueError(
                f"This email is already registered. "
                f"User '{existing_email.username}' is already using this email address."
            )
        
        # Check if team exists, if not create it
        existing_team = db.query(Team).filter(Team.name == team).first()
        if not existing_team:
            # Auto-create team if it doesn't exist
            new_team = Team(name=team)
            db.add(new_team)
            try:
                db.commit()
                print(f"Team '{team}' created successfully")
            except Exception as e:
                db.rollback()
                raise ValueError(f"Failed to create team '{team}': {str(e)}")
        
        # Hash the password
        hashed_password = AuthService.hash_password(password)
        
        # Create new user
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            role=role,
            team=team,
            tickets_solved=tickets_solved
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def get_user_by_username(username: str, db: Session) -> User:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(email: str, db: Session) -> User:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def update_user_password(user_id: int, new_password: str, db: Session) -> bool:
        """Update user password"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.hashed_password = AuthService.hash_password(new_password)
        db.commit()
        return True