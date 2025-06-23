from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from src.utils.config import settings
from src.schemas.ai_schema import RiskItem, SprintReport
from src.models.sprint import Sprint
import json

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class AIService:
    @staticmethod
    async def generate_task_report(issue_key: str, db: Session) -> SprintReport:
        sprint_task: Optional[Sprint] = db.query(Sprint).filter(Sprint.issue_key == issue_key).first()

        if not sprint_task:
            raise ValueError(f"Issue with key {issue_key} not found in database.")

        prompt = (
            f"Generate a structured AI report for the following completed sprint task:\n\n"
            f"Issue Key: {sprint_task.issue_key}\n"
            f"Title: {sprint_task.title}\n"
            f"Assignee: {sprint_task.assignee_name}\n"
            f"Story Points: {sprint_task.story_points}\n"
            f"Estimated Duration (Days): {sprint_task.estimated_days}\n\n"
            f"The report should include:\n"
            f"1. A concise summary of assigned task to respective assignee.\n"
            f"2. Key technical or strategic details about the implementation.\n"
            f"3. 3 to 5 tailored recommendations for improving similar future tasks.\n"
            f"Format the response as JSON with fields: summary, details, recommendations (as list).\n"
        )

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        result = response.choices[0].message.content.strip()

        try:
            parsed = json.loads(result)
            return SprintReport(
                issue_key=sprint_task.issue_key,
                assignee_name=sprint_task.assignee_name,
                title=sprint_task.title,
                summary=parsed.get("summary", ""),
                details=parsed.get("details", ""),
                recommendations=parsed.get("recommendations", []),
            )
        except Exception as e:
            raise ValueError(f"AI response could not be parsed as JSON: {e}\n\nRaw Output:\n{result}")

    @staticmethod
    async def identify_risks(db: Session) -> Dict[str, List[RiskItem]]:
        results = db.execute(text("""
            SELECT assignee_name, title, story_points, estimated_days, issue_key
            FROM sprints
        """)).fetchall()

        if not results:
            return {"risks": []}

        issue_to_assignee = {row.issue_key: row.assignee_name for row in results}
        valid_assignees = set(row.assignee_name for row in results)

        issue_contexts = [
            f"- Issue Key: {row.issue_key}, Title: '{row.title}', Assignee: {row.assignee_name}, "
            f"Story Points: {row.story_points}, Days: {row.estimated_days}"
            for row in results
        ]

        prompt = (
            f"Below is a list of sprint tasks:\n"
            f"{chr(10).join(issue_contexts)}\n\n"
            f"Analyze each task individually and identify specific risks related to complexity, workload, or other factors. "
            f"For each risk, return exactly one team member (the assignee of the task) in the impacted_person field. "
            f"Only include assignees from the provided tasks: {', '.join(valid_assignees)}. "
            f"Do not include risks about multiple task assignments, as each team member has only one task. "
            f"Return a list of JSON objects, each with the following structure:\n"
            """[
  {
    "risk": "Description of the risk for this specific task",
    "severity": "Low/Medium/High",
    "impacted_person": ["<assignee_name>"]
  }
]"""
        )

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a project management AI. Ensure each risk is specific to one task and its assignee."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )

        content = response.choices[0].message.content.strip()

        try:
            risks_list = json.loads(content)
            validated_risks = []
            for risk in risks_list:
                if (
                    isinstance(risk, dict)
                    and "impacted_person" in risk
                    and isinstance(risk["impacted_person"], list)
                    and len(risk["impacted_person"]) == 1
                    and risk["impacted_person"][0] in valid_assignees
                    and "risk" in risk
                    and "severity" in risk
                    and risk["severity"] in ["Low", "Medium", "High"]
                ):
                    validated_risks.append(RiskItem(**risk))
                else:
                    print(f"Skipping invalid risk: {risk}")
            return {"risks": validated_risks}
        except Exception as e:
            raise ValueError(f"Failed to parse AI risk response: {e}\n\nRaw Output:\n{content}")