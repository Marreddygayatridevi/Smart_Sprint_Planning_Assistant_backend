from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.dependencies import db_dependency, current_user_dependency
from src.services.jira_service import JiraService
from src.schemas.jira_schema import JiraIssueResponse, JiraIssueCreate,JiraIssueUpdate
from src.database.db import get_db

router = APIRouter(prefix="/jira", tags=["jira"])
    
@router.get("/issues", response_model=list[JiraIssueResponse])
async def fetch_jira_issues(
    project_key: str,
    db: db_dependency,
    current_user: current_user_dependency,
    sync: bool = True
):
    try:
        if sync:
            # Fetch from Jira Cloud and sync to local DB
            return JiraService.fetch_and_sync_issues(project_key=project_key, db=db)
        else:
            # Only fetch from local DB
            return JiraService.get_issues_from_db(project_key=project_key, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new_issues", response_model=JiraIssueResponse)
async def create_jira_issue(
    issue: JiraIssueCreate,
    db: db_dependency,
    current_user: current_user_dependency
):
    try:
        return JiraService.create_issue(issue_data=issue, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update_issue/{issue_key}", response_model=JiraIssueResponse)
async def update_jira_issue(
    issue_key: str,
    updated_issue: JiraIssueUpdate,
    db: db_dependency,
    current_user: current_user_dependency
):
    try:
        update_data = updated_issue.dict(exclude_unset=True)

        # Clean 'assignee': set to None if it's empty, whitespace, or "string"
        if "assignee" in update_data:
            assignee = update_data["assignee"]
            if not assignee or str(assignee).strip().lower() == "string":
                update_data["assignee"] = None

        clean_update = JiraIssueUpdate(**update_data)

        return JiraService.update_issue_by_key(
            issue_key=issue_key,
            updated_data=clean_update,
            db=db
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_issue/{issue_key}")
async def delete_jira_issue(
    issue_key: str,
    db: db_dependency,
    current_user: current_user_dependency
):
    try:
        JiraService.delete_issue_by_key(issue_key=issue_key, db=db)
        return {"detail": f"Issue {issue_key} deleted successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))