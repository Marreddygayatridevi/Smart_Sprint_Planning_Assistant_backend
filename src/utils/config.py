import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # JWT Configuration
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', '').strip()
    ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256').strip()
    JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', '1440'))

    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', '').strip()

    # Jira Configuration
    JIRA_BASE_URL = os.getenv('JIRA_URL', '').strip()  
    JIRA_EMAIL = os.getenv('JIRA_EMAIL', '').strip()
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', '').strip()

    # OpenAI Configuration 
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()

    # App Configuration
    FRONTEND_URL = os.getenv('FRONTEND_URL', '').strip()
    BACKEND_URL = os.getenv('BACKEND_URL', '').strip()

# Instantiate global settings object
settings = Settings()

# Optional: backward compatibility
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
JWT_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES
DATABASE_URL = settings.DATABASE_URL
