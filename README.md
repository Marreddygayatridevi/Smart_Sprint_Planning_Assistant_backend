# Smart Sprint Planning System - Backend

A powerful FastAPI backend for the Smart Sprint Planning System that provides secure authentication, AI-powered sprint planning, JIRA integration, and comprehensive team management for agile development teams.

## 🚀 Features

- **🔐 JWT Authentication** - Secure user authentication with bcrypt password hashing
- **🎫 JIRA Integration** - Seamless JIRA API integration for ticket management
- **🤖 AI-Powered Sprint Planning** - OpenAI integration for intelligent task assignment
- **📊 Intelligent Story Point Estimation** - AI-enhanced Fibonacci-based story points
- **⚠️ Risk Analysis** - AI-driven risk identification and assessment
- **📈 Sprint Reports** - Comprehensive AI-generated sprint analytics
- **🎯 Smart Task Assignment** - Experience-based round-robin assignment algorithm
- **📊 Database Integration** - PostgreSQL with SQLAlchemy ORM

## 🛠️ Tech Stack

- **Framework:** FastAPI (Python 3.8+)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** JWT (JSON Web Tokens) with python-jose
- **Password Hashing:** passlib with bcrypt
- **AI Integration:** OpenAI GPT-4 API
- **JIRA Integration:** JIRA REST API v3
- **Environment:** python-dotenv
- **CORS:** FastAPI CORS middleware
- **Validation:** Pydantic schemas

## 📋 Prerequisites

Before running this application, make sure you have the following installed:

- **Python** (version 3.8 or higher)
- **pip** (Python package manager)
- **PostgreSQL** (version 12.0 or higher)
- **Git**
- **OpenAI API Key** (for AI features)
- **JIRA Account** (for JIRA integration)

## 🔧 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/Marreddygayatridevi/Smart_Sprint_Planning_System_Backend.git
cd Smart_Sprint_Planning_System_Backend
```

### 2. Create virtual environment and install dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```bash
touch .env
```

Add the following environment variables:
```env
# Server Configuration
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/smart_sprint_planner
# For production:
# DATABASE_URL=postgresql://username:password@your-postgres-host:5432/smart_sprint_planner

# JWT Configuration
SECRET_KEY=your_super_secret_jwt_key_here_make_it_very_long_and_random
ALGORITHM=HS256
JWT_EXPIRE_MINUTES=43200

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# JIRA Configuration
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-jira-email@example.com
JIRA_API_TOKEN=your_jira_api_token

# Frontend URL
FRONTEND_URL=http://localhost:5173

```

### 6. Start the server

#### Development mode
```bash
uvicorn src.main:app --reload
```


The server will be available at `http://localhost:8000`


## 🏗️ Project Structure

```
src/
├── controllers/        # Route handlers
├── models/            # SQLAlchemy database models
│   ├── user.py
│   ├── team.py
│   ├── jira_issue.py
│   └── sprint.py
├── schemas/           # Pydantic schemas
│   ├── auth_schema.py
│   ├── ai_schema.py
│   ├── jira_schema.py
│   └── sprint_schema.py
├── services/          # Business logic
│   ├── auth_service.py
│   ├── ai_service.py
│   ├── jira_service.py
│   ├── team_service.py
│   └── sprint_service.py
├── routers/           # API route definitions
│   ├── auth.py
│   ├── ai.py
│   ├── jira.py
│   ├── teams.py
│   └── sprints.py
├── utils/             # Utility functions
│   ├── config.py
│   ├── database.py
│   └── dependencies.py
├── middleware/        # Custom middleware
│   └── auth.py
└── main.py           # FastAPI application entry point
```


## 🔒 Authentication & Authorization

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```
## 📊 API Documentation

Once the server is running, you can access:

- **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
- **Alternative API Docs (ReDoc):** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

## 🔧 Configuration

### Database Configuration
Configure PostgreSQL connection in `src/utils/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### OpenAI Configuration
Configure OpenAI client in your services:

```python
from openai import OpenAI
from src.utils.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)
```


**OpenAI API Issues:**
- Ensure OPENAI_API_KEY is set correctly in environment variables
- Check API key validity at OpenAI dashboard
- Verify sufficient API credits

**JIRA Integration Issues:**
- Verify JIRA_BASE_URL format (https://your-domain.atlassian.net)
- Check JIRA_API_TOKEN validity
- Ensure JIRA_EMAIL has proper permissions

**Database Migration Issues:**
```bash
# Reset database (careful - this deletes all data)
python -c "from src.database import engine; from src.models import Base; Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)"
```

## 👥 Authors

- **Gayatri Devi Marreddy** - *Initial work* - [Marreddygayatridevi](https://github.com/Marreddygayatridevi)

