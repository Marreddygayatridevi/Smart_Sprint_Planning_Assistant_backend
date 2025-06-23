import requests
import re
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from src.models.jira_issue import JiraIssue
from src.schemas.jira_schema import JiraIssueResponse, JiraIssueCreate, JiraIssueUpdate
from src.utils.config import settings

class JiraService:

    @staticmethod
    def fetch_and_sync_issues(project_key: str, db: Session) -> List[JiraIssueResponse]:
        url = f"{settings.JIRA_BASE_URL}/rest/api/3/search"
        auth = (settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
        headers = {"Accept": "application/json"}
        params = {
            "jql": f"project={project_key}",
            "maxResults": 100,
            "fields": "summary,description,priority,customfield_10016,assignee,status,duedate"
        }

        try:
            resp = requests.get(url, headers=headers, auth=auth, params=params)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Error fetching Jira issues: {e}")

        issues = resp.json().get("issues", [])

        def extract_text(adf):
            if not adf:
                return ""
            parts = []
            if isinstance(adf, dict):
                if adf.get("type") == "text":
                    parts.append(adf.get("text", ""))
                for key in ["content", "marks"]:
                    if key in adf:
                        for child in adf[key]:
                            parts.append(extract_text(child))
            elif isinstance(adf, list):
                for item in adf:
                    parts.append(extract_text(item))
            return " ".join(parts).strip()

        for it in issues:
            key = it["key"]
            f = it["fields"]
            title = f["summary"]
            description = extract_text(f.get("description"))
            priority = f.get("priority", {}).get("name", "Unknown")
            assignee = f.get("assignee", {}).get("displayName") if f.get("assignee") else None
            status = f.get("status", {}).get("name")
            story_pts = f.get("customfield_10016")
            due_date = None
            if f.get("duedate"):
                try:
                    due_date = datetime.strptime(f["duedate"], "%Y-%m-%d").date()
                except ValueError:
                    due_date = None

            rec = db.query(JiraIssue).filter(JiraIssue.key == key).first()
            if rec:
                rec.title = title
                rec.description = description
                rec.priority = priority
                rec.assignee = assignee
                rec.status = status
                rec.story_points = story_pts
                rec.due_date = due_date
                rec.last_synced_at = func.now()
            else:
                rec = JiraIssue(
                    key=key, project_key=project_key, title=title,
                    description=description, priority=priority,
                    assignee=assignee, status=status,
                    story_points=story_pts, due_date=due_date
                )
                db.add(rec)

        db.commit()
        return JiraService.get_issues_from_db(project_key, db)

    @staticmethod
    def get_issues_from_db(project_key: str, db: Session) -> List[JiraIssueResponse]:
        rows = db.query(JiraIssue).filter(JiraIssue.project_key == project_key).all()
        return [
            JiraIssueResponse(
                id=r.id, key=r.key, title=r.title,
                description=r.description or "", priority=r.priority,
                assignee=r.assignee, status=r.status,
                story_points=r.story_points, due_date=r.due_date
            ) for r in rows
        ]

    @staticmethod
    def create_issue(issue_data: JiraIssueCreate, db: Session) -> JiraIssueResponse:
        keys = db.query(JiraIssue.key).filter(JiraIssue.project_key == issue_data.project_key).all()
        max_no = 0
        pat = re.compile(rf"{re.escape(issue_data.project_key)}-(\d+)$")
        for (k,) in keys:
            m = pat.match(k)
            if m:
                max_no = max(max_no, int(m.group(1)))

        new_key = f"{issue_data.project_key}-{max_no+1}"
        ass = issue_data.assignee.strip() if issue_data.assignee and issue_data.assignee.strip().lower() != "string" else None
        sp = issue_data.story_points if issue_data.story_points not in (0, "0", "", None) else None

        rec = JiraIssue(
            key=new_key, project_key=issue_data.project_key,
            title=issue_data.title, description=issue_data.description,
            priority=issue_data.priority, assignee=ass,
            status=issue_data.status, story_points=sp,
            due_date=issue_data.due_date
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        return JiraIssueResponse(
            id=rec.id, key=rec.key, title=rec.title,
            description=rec.description, priority=rec.priority,
            assignee=rec.assignee, status=rec.status,
            story_points=rec.story_points, due_date=rec.due_date
        )

    @staticmethod
    def update_issue_by_key(issue_key: str, updated_data: JiraIssueUpdate, db: Session) -> JiraIssueResponse:
        rec = db.query(JiraIssue).filter(JiraIssue.key == issue_key).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Issue not found")

        for field, val in updated_data.dict(exclude_unset=True).items():
            setattr(rec, field, val)

        db.commit()
        db.refresh(rec)

        return JiraIssueResponse(
            id=rec.id, key=rec.key, title=rec.title,
            description=rec.description, priority=rec.priority,
            assignee=rec.assignee, status=rec.status,
            story_points=rec.story_points, due_date=rec.due_date
        )

    @staticmethod
    def delete_issue_by_key(issue_key: str, db: Session) -> None:
        rec = db.query(JiraIssue).filter(JiraIssue.key == issue_key).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Issue not found")
        db.delete(rec)
        db.commit()
