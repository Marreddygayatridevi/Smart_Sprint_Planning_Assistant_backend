from openai import OpenAI
import json 
import hashlib
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from src.services.jira_service import JiraService
from src.services.team_service import TeamService
from src.schemas.sprint_schema import SprintAssignmentResponse, StoryPointEstimate, UserSkillAnalysis
from src.schemas.jira_schema import JiraIssueResponse
from src.models.user import User
from src.utils.config import settings

openai = OpenAI(api_key=settings.OPENAI_API_KEY)

class SprintConfig:
    """Centralized configuration for sprint planning"""
    
    # Status categories
    DONE_STATUSES = {'done', 'closed', 'resolved', 'completed'}
    IN_PROGRESS_STATUSES = {'in progress', 'inprogress', 'in-progress', 'development', 'coding'}
    TODO_STATUSES = {'to do', 'todo', 'open', 'new', 'backlog', 'ready for development'}
    
    # Fibonacci story points
    FIBONACCI_POINTS = [1, 2, 3, 5, 8, 13, 21]
    
    # Experience thresholds (data-driven)
    EXPERIENCE_THRESHOLDS = {
        'senior': 40,   
        'junior': 15,   
        'intern': 0     
    }
    
    # Story point rules by experience
    STORY_POINT_LIMITS = {
        'intern': {'min': 1, 'max': 3},
        'junior': {'min': 3, 'max': 8}, 
        'senior': {'min': 5, 'max': 21}
    }
    
    # Story point to days mapping
    DAYS_MAPPING = {1: 1, 2: 1, 3: 2, 5: 3, 8: 5, 13: 8, 21: 13}
    
    # Experience multipliers for time estimation
    EXPERIENCE_MULTIPLIERS = {'senior': 0.8, 'junior': 1.0, 'intern': 1.3}

class SprintService:
    
    @staticmethod
    async def create_sprint_assignments(
        project_key: str,
        sprint_name: str,
        team_name: str,
        db: Session
    ) -> List[SprintAssignmentResponse]:
        """Main method to create sprint assignments"""
        try:
            # Get data
            jira_issues = SprintService._get_jira_issues(project_key, db)
            team_users = TeamService.get_users_by_team(team_name, db)
            
            if not jira_issues:
                raise HTTPException(status_code=404, detail="No Jira issues found")
            if not team_users:
                raise HTTPException(status_code=404, detail=f"No users found in team '{team_name}'")

            # Process and assign
            assignable_issues, existing_assignments = SprintService._filter_assignable_issues(jira_issues)
            
            # Create assignments for unassigned tickets only
            new_assignments = []
            if assignable_issues:
                issues_with_points = await SprintService._assign_story_points(assignable_issues)
                user_analyses = SprintService._analyze_team(team_users)
                new_assignments = SprintService._create_assignments(issues_with_points, user_analyses, sprint_name)
            
            # Save and return ALL assignments (existing + new)
            all_assignments = existing_assignments + new_assignments
            await SprintService._save_to_db(all_assignments, db)
            return all_assignments
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating assignments: {str(e)}")

    @staticmethod
    def _get_jira_issues(project_key: str, db: Session) -> List[JiraIssueResponse]:
        """Get Jira issues from DB or API"""
        issues = JiraService.get_issues_from_db(project_key, db)
        if not issues:
            issues = JiraService.fetch_all_issues(project_key)
            if issues:
                JiraService.sync_issues_to_db(project_key, db)
        return issues or []

    @staticmethod
    def _filter_assignable_issues(issues: List[JiraIssueResponse]) -> Tuple[List[JiraIssueResponse], List[SprintAssignmentResponse]]:
        """
        FIXED LOGIC: Filter issues into assignable and existing assignments
        - Preserve ALL tickets that have assignees (regardless of status)
        - Only assign tickets that have NO assignee
        """
        assignable = []
        existing = []
        
        print(f"\n Filtering {len(issues)} issues...")
        
        for issue in issues:
            status = issue.status.lower().strip() if issue.status else 'unknown'
            has_assignee = SprintService._has_assignee(issue)
            assignee_name = getattr(issue, 'assignee', 'None')
            
            # Debug logging
            print(f"   {issue.key}: status='{status}', assignee='{assignee_name}', has_assignee={has_assignee}")
            
            # Skip completed work
            if status in SprintConfig.DONE_STATUSES:
                print(f"   → SKIPPED (Done status)")
                continue
            
            # FIXED: Preserve ANY ticket that has an assignee (regardless of status)
            if has_assignee:
                existing_assignment = SprintService._create_existing_assignment(issue)
                existing.append(existing_assignment)
                print(f"   → EXISTING assignment preserved (assigned to {assignee_name})")
            else:
                # Only assign tickets that have NO assignee
                assignable.append(issue)
                print(f"   → ASSIGNABLE (no current assignee)")
        
        print(f"\n Filtering Results:")
        print(f"   Existing assignments (preserved): {len(existing)}")
        print(f"   Assignable issues (unassigned): {len(assignable)}")
        
        return assignable, existing

    @staticmethod
    def _has_assignee(issue: JiraIssueResponse) -> bool:
        """Enhanced assignee check to handle different data formats"""
        if not hasattr(issue, 'assignee'):
            return False
        
        assignee = issue.assignee
        
        # Handle None or empty
        if not assignee:
            return False
        
        # Handle string assignee
        if isinstance(assignee, str):
            return bool(assignee.strip())
        
        # Handle dict assignee (Jira API sometimes returns objects)
        if isinstance(assignee, dict):
            return bool(
                assignee.get('name', '').strip() or 
                assignee.get('displayName', '').strip() or
                assignee.get('key', '').strip()
            )
        
        return False

    @staticmethod
    def _create_existing_assignment(issue: JiraIssueResponse) -> SprintAssignmentResponse:
        """Create assignment for existing assigned issue"""
        # Use existing story points or calculate basic ones
        if hasattr(issue, 'story_points') and issue.story_points:
            story_points = SprintService._get_closest_fibonacci(int(issue.story_points))
        else:
            story_points = SprintService._calculate_basic_story_points(issue)
        
        estimated_days = SprintConfig.DAYS_MAPPING.get(story_points, 3)
        
        # Handle different assignee formats
        assignee = issue.assignee
        if isinstance(assignee, dict):
            assignee_name = assignee.get('displayName') or assignee.get('name') or assignee.get('key', 'Unknown')
        else:
            assignee_name = str(assignee) if assignee else 'Unknown'
        
        return SprintAssignmentResponse(
            sprint_name="Current Sprint",  # You might want to make this dynamic
            issue_key=issue.key,
            assignee_name=assignee_name,
            title=issue.title,
            estimated_days=estimated_days,
            story_points=story_points
        )

    @staticmethod
    async def _assign_story_points(issues: List[JiraIssueResponse]) -> List[JiraIssueResponse]:
        """Assign story points using data-driven approach with AI enhancement"""
        print(f"\n Assigning story points to {len(issues)} issues...")
        
        for issue in issues:
            # Data-driven basic assignment
            basic_points = SprintService._calculate_basic_story_points(issue)
            
            # AI enhancement for complex cases only
            if SprintService._needs_ai_analysis(issue):
                try:
                    estimate = await SprintService._ai_estimate_story_points(issue, basic_points)
                    issue.story_points = estimate.estimated_story_points
                    print(f"   {issue.key}: AI estimated {issue.story_points} points")
                except Exception as e:
                    issue.story_points = basic_points  # Fallback to basic
                    print(f"   {issue.key}: AI failed, using basic {basic_points} points")
            else:
                issue.story_points = basic_points
                print(f"   {issue.key}: Basic estimation {basic_points} points")
                
        return issues

    @staticmethod
    def _calculate_basic_story_points(issue: JiraIssueResponse) -> int:
        """Data-driven story point calculation"""
        title_length = len(issue.title.split())
        desc_length = len((issue.description or "").split())
        total_length = title_length + desc_length
        
        # Simple length-based rules
        if total_length <= 5:
            points = 1
        elif total_length <= 10:
            points = 2
        elif total_length <= 20:
            points = 3
        elif total_length <= 35:
            points = 5
        elif total_length <= 50:
            points = 8
        else:
            points = 13
            
        return SprintService._get_closest_fibonacci(points)

    @staticmethod
    def _needs_ai_analysis(issue: JiraIssueResponse) -> bool:
        """Determine if issue needs AI analysis"""
        # Use AI for complex cases only
        desc_length = len(issue.description or "")
        title_lower = issue.title.lower()
        
        return (desc_length > 200 or 
                any(word in title_lower for word in ["integration", "complex", "architecture", "migration"]))

    @staticmethod
    async def _ai_estimate_story_points(issue: JiraIssueResponse, basic_points: int) -> StoryPointEstimate:
        """AI-enhanced story point estimation"""
        seed = abs(hash(f"{issue.title}{issue.description or ''}")) % 10000
        
        prompt = f"""
Analyze this task and refine the story point estimate.

Task: {issue.title}
Description: {issue.description or "No description"}
Basic Estimate: {basic_points}

Use only Fibonacci numbers: {SprintConfig.FIBONACCI_POINTS}
Consider: complexity, unknowns, integration points.

Return JSON: {{"estimated_story_points": <number>, "complexity_reasoning": "<brief reason>"}}
"""

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a software estimation expert. Use only Fibonacci numbers for story points."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            seed=seed
        )
        
        result = json.loads(response.choices[0].message.content)
        points = SprintService._get_closest_fibonacci(int(result["estimated_story_points"]))
        
        return StoryPointEstimate(
            issue_key=issue.key,
            title=issue.title,
            estimated_story_points=points,
            complexity_reasoning=result["complexity_reasoning"]
        )

    @staticmethod
    def _analyze_team(users: List[User]) -> List[UserSkillAnalysis]:
        """Analyze team using data-driven approach"""
        return [
            UserSkillAnalysis(
                user_id=user.id,
                username=user.username,
                role=user.role,
                team=user.team,
                tickets_solved=user.tickets_solved,
                skill_category=SprintService._get_skill_category(user.role),
                experience_level=SprintService._get_experience_level(user.tickets_solved),
                capacity_score=SprintService._calculate_capacity(user.tickets_solved)
            ) for user in users
        ]

    @staticmethod
    def _get_experience_level(tickets_solved: int) -> str:
        """Data-driven experience level determination"""
        if tickets_solved >= SprintConfig.EXPERIENCE_THRESHOLDS['senior']:
            return 'senior'
        elif tickets_solved >= SprintConfig.EXPERIENCE_THRESHOLDS['junior']:
            return 'junior'
        else:
            return 'intern'

    @staticmethod
    def _get_skill_category(role: str) -> str:
        """Simple skill categorization"""
        role_lower = role.lower()
        if 'frontend' in role_lower or 'ui' in role_lower:
            return 'frontend'
        elif 'backend' in role_lower or 'api' in role_lower:
            return 'backend'
        elif 'fullstack' in role_lower or 'full' in role_lower:
            return 'fullstack'
        elif 'test' in role_lower or 'qa' in role_lower:
            return 'testing'
        else:
            return 'backend'  # Default

    @staticmethod
    def _calculate_capacity(tickets_solved: int) -> float:
        """Calculate capacity score"""
        return min(tickets_solved * 2 + 10, 100.0)

    @staticmethod
    def _create_assignments(
        issues: List[JiraIssueResponse],
        users: List[UserSkillAnalysis],
        sprint_name: str
    ) -> List[SprintAssignmentResponse]:
        """Create assignments ensuring STRICT round-robin distribution - no user gets 2 tickets until all have 1"""
        
        if not users or not issues:
            print("  No users or issues to assign")
            return []
        
        print(f"\n Creating assignments for {len(issues)} unassigned issues among {len(users)} users...")
        
        # Sort users by experience level and capacity for consistent ordering
        sorted_users = sorted(users, key=lambda u: (
            {'senior': 3, 'junior': 2, 'intern': 1}[u.experience_level],
            u.capacity_score
        ), reverse=True)
        
        # Sort issues by story points (complex first)
        sorted_issues = sorted(issues, key=lambda i: int(i.story_points or 3), reverse=True)
        
        assignments = []
        user_index = 0  # Simple round-robin index
        
        def can_user_handle_points(user, story_points):
            """Check if user can handle the story points"""
            limits = SprintConfig.STORY_POINT_LIMITS[user.experience_level]
            return limits['min'] <= story_points <= limits['max']
        
        def adjust_story_points_for_user(user, original_points):
            """Adjust story points to fit user's capability"""
            limits = SprintConfig.STORY_POINT_LIMITS[user.experience_level]
            return max(limits['min'], min(limits['max'], original_points))
        
        def assign_issue_to_user(issue, user, adjusted_points=None):
            """Create assignment with proper point adjustment"""
            story_points = adjusted_points if adjusted_points else int(issue.story_points or 3)
            
            base_days = SprintConfig.DAYS_MAPPING.get(story_points, 3)
            multiplier = SprintConfig.EXPERIENCE_MULTIPLIERS.get(user.experience_level, 1.0)
            estimated_days = max(1, min(int(base_days * multiplier), 15))
            
            assignments.append(SprintAssignmentResponse(
                sprint_name=sprint_name,
                issue_key=issue.key,
                assignee_name=user.username,
                title=issue.title,
                estimated_days=estimated_days,
                story_points=story_points
            ))
            
            print(f" Assigned {issue.key} ({story_points} pts) to {user.username}")
        
        # STRICT Round-Robin Assignment
        for issue in sorted_issues:
            original_points = int(issue.story_points or 3)
            assigned = False
            attempts = 0
            
            # Try to find a user who can handle this issue, starting from current index
            while attempts < len(sorted_users) and not assigned:
                current_user = sorted_users[user_index]
                
                if can_user_handle_points(current_user, original_points):
                    # User can handle original points
                    assign_issue_to_user(issue, current_user, original_points)
                    assigned = True
                else:
                    # Adjust points to fit user's capability
                    adjusted_points = adjust_story_points_for_user(current_user, original_points)
                    assign_issue_to_user(issue, current_user, adjusted_points)
                    print(f"  Adjusted {issue.key} from {original_points} to {adjusted_points} points for {current_user.username}")
                    assigned = True
                
                # Move to next user for next issue (round-robin)
                user_index = (user_index + 1) % len(sorted_users)
                attempts += 1
            
            if not assigned:
                # This should never happen, but safety fallback
                fallback_user = sorted_users[user_index]
                adjusted_points = adjust_story_points_for_user(fallback_user, original_points)
                assign_issue_to_user(issue, fallback_user, adjusted_points)
                user_index = (user_index + 1) % len(sorted_users)
                print(f" Fallback assignment: {issue.key} to {fallback_user.username}")
        
        # Calculate final distribution
        user_assignment_count = {}
        for assignment in assignments:
            user_assignment_count[assignment.assignee_name] = user_assignment_count.get(assignment.assignee_name, 0) + 1
        
        print(f"\n Final NEW Assignment Distribution:")
        for user in sorted_users:
            count = user_assignment_count.get(user.username, 0)
            print(f"   {user.username} ({user.experience_level}): {count} new tickets")
        
        print(f"\nSummary:")
        print(f"   New assignments: {len(assignments)}")
        print(f"   Team size: {len(sorted_users)}")
        if user_assignment_count:
            print(f"   Min assignments per user: {min(user_assignment_count.values())}")
            print(f"   Max assignments per user: {max(user_assignment_count.values())}")
        
        return assignments

    @staticmethod
    def _group_by_experience(users: List[UserSkillAnalysis]) -> Dict[str, List[UserSkillAnalysis]]:
        """Group users by experience level"""
        groups = {'intern': [], 'junior': [], 'senior': []}
        for user in users:
            groups[user.experience_level].append(user)
        
        # Sort by capacity score
        for level in groups:
            groups[level].sort(key=lambda x: x.capacity_score, reverse=True)
        
        return groups

    @staticmethod
    def _group_issues_by_points(issues: List[JiraIssueResponse]) -> Dict[str, List[JiraIssueResponse]]:
        """Group issues by story points for experience matching"""
        groups = {'intern': [], 'junior': [], 'senior': []}
        
        for issue in issues:
            points = int(issue.story_points or 3)
            
            if points <= 3:
                groups['intern'].append(issue)
            elif points <= 8:
                groups['junior'].append(issue)
            else:
                groups['senior'].append(issue)
        
        return groups

    @staticmethod
    async def _save_to_db(assignments: List[SprintAssignmentResponse], db: Session):
        """Save assignments to database with overwrite logic - UPDATE by issue_key only"""
        if not assignments:
            print(" No assignments to save")
            return
            
        try:
            saved_count = 0
            updated_count = 0
            
            for assignment in assignments:
                # Check if assignment exists for this issue_key (regardless of sprint_name)
                existing = db.execute(text("""
                    SELECT id, assignee_name, sprint_name FROM sprints 
                    WHERE issue_key = :issue_key
                    ORDER BY created_at DESC
                    LIMIT 1
                """), {
                    "issue_key": assignment.issue_key
                }).fetchone()
                
                if existing:
                    existing_id, existing_assignee, existing_sprint = existing
                    
                    # Always UPDATE the existing record with new assignment details
                    db.execute(text("""
                        UPDATE sprints SET
                            sprint_name = :sprint_name,
                            assignee_name = :assignee_name,
                            title = :title,
                            estimated_days = :estimated_days,
                            story_points = :story_points,
                            updated_at = NOW()
                        WHERE id = :id
                    """), {
                        "sprint_name": assignment.sprint_name,
                        "assignee_name": assignment.assignee_name,
                        "title": assignment.title,
                        "estimated_days": assignment.estimated_days,
                        "story_points": assignment.story_points,
                        "id": existing_id
                    })
                    updated_count += 1
                    
                    if existing_assignee != assignment.assignee_name:
                        print(f"    {assignment.issue_key}: REASSIGNED from {existing_assignee} → {assignment.assignee_name}")
                    else:
                        print(f"    {assignment.issue_key}: Updated details (same assignee: {assignment.assignee_name})")
                    
                    # Optional: Delete any other duplicate entries for this issue_key
                    db.execute(text("""
                        DELETE FROM sprints 
                        WHERE issue_key = :issue_key AND id != :keep_id
                    """), {
                        "issue_key": assignment.issue_key,
                        "keep_id": existing_id
                    })
                    
                else:
                    # INSERT new assignment only if no existing record found
                    db.execute(text("""
                        INSERT INTO sprints (
                            sprint_name, issue_key, assignee_name, title, 
                            estimated_days, story_points, created_at
                        ) VALUES (
                            :sprint_name, :issue_key, :assignee_name, :title,
                            :estimated_days, :story_points, NOW()
                        )
                    """), {
                        "sprint_name": assignment.sprint_name,
                        "issue_key": assignment.issue_key,
                        "assignee_name": assignment.assignee_name,
                        "title": assignment.title,
                        "estimated_days": assignment.estimated_days,
                        "story_points": assignment.story_points
                    })
                    saved_count += 1
                    print(f"   ➕ {assignment.issue_key}: NEW assignment to {assignment.assignee_name}")
            
            db.commit()
            print(f"\n Database Summary:")
            print(f"   New assignments: {saved_count}")
            print(f"   Updated/Reassigned: {updated_count}")
            print(f"   Total processed: {saved_count + updated_count}")
            
        except Exception as e:
            db.rollback()
            print(f"Error saving assignments: {str(e)}")
            raise

    @staticmethod
    def _get_closest_fibonacci(value: int) -> int:
        """Get closest Fibonacci number"""
        if value <= 0:
            return 1
        
        return min(SprintConfig.FIBONACCI_POINTS, key=lambda x: abs(x - value))
