from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt, ExpiredSignatureError
from src.database.db import get_db
from src.models.user import User
from src.utils.config import SECRET_KEY, ALGORITHM

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Database dependency
db_dependency = Annotated[Session, Depends(get_db)]

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    """
    Dependency to get the current authenticated user from JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user (missing username or ID).'
            )
        
        # Fetch user from database to ensure they still exist
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found.'
            )
        
        return user
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token has expired.'
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Token is invalid or could not be decoded. Error: {str(e)}'
        )

# Current user dependency
current_user_dependency = Annotated[User, Depends(get_current_user)]