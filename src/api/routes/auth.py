from datetime import timedelta
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.database.db import get_db
from src.schemas.user_schema import CreateUserRequest, UserResponse, Token
from src.services.auth_services import AuthService
from src.api.dependencies import current_user_dependency
from src.models.user import User 

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    try:
        user = AuthService.create_user(
            username=create_user_request.username,
            email=create_user_request.email,
            password=create_user_request.password,
            db=db,
            is_active=create_user_request.is_active,
            role=create_user_request.role,
            team=create_user_request.team,
            tickets_solved=create_user_request.tickets_solved
        )

        return {
            "message": "User created successfully",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "team": user.team,
            "tickets_solved": user.tickets_solved
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: db_dependency
):
    """
    Login endpoint to get JWT access token
    """
    user = AuthService.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials'
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Account is inactive'
        )
    
    token = AuthService.create_access_token(
        username=user.username, 
        user_id=user.id, 
        expires_delta=timedelta(hours=24)
    )
    
    return {'access_token': token, 'token_type': 'bearer'}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: current_user_dependency):
    """
    Get current authenticated user information
    """
    return current_user

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: current_user_dependency, 
    db: db_dependency
):
    return db.query(User).all()  