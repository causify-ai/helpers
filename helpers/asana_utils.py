"""
Enhanced Asana Analytics with Time Estimation and Team Grouping.

Import as:

import helpers.asana_utils as hasautil
"""

import datetime as datetime_lib
import json
import logging
import os
from typing import Any, Dict, List, Optional

import asana
import asana.rest as arest
import dateutil.parser as dateutil_parser
import pandas as pd

_LOG = logging.getLogger(__name__)


# #############################################################################
# EnhancedAsanaAnalytics
# #############################################################################


class EnhancedAsanaAnalytics:
    """
    Enhanced Asana Analytics with time estimation and team grouping.
    """

    def __init__(self, access_token: Optional[str] = None) -> None:
        # Get token from parameter or environment variable.
        token = access_token or os.getenv("ASANA_ACCESS_TOKEN")
        if not token:
            raise ValueError(
                "Asana access token must be provided or set in ASANA_ACCESS_TOKEN"
            )
        # Initialize Asana API client with access token.
        configuration = asana.Configuration()
        configuration.access_token = token
        self.api_client = asana.ApiClient(configuration)
        # Initialize API endpoints.
        self.workspaces_api = asana.WorkspacesApi(self.api_client)
        self.users_api = asana.UsersApi(self.api_client)
        self.tasks_api = asana.TasksApi(self.api_client)
        self.stories_api = asana.StoriesApi(self.api_client)
        self.projects_api = asana.ProjectsApi(self.api_client)
        self.custom_fields_api = asana.CustomFieldsApi(self.api_client)

    def get_workspace_gid(self, workspace_name: Optional[str] = None) -> str:
        """
        Get the workspace GID by name or return the first available workspace.

        Retrieve the GID (Global ID) for an Asana workspace. If no
        workspace name is provided, return the GID of the first
        workspace available to the user.

        :param workspace_name: name of the workspace to find.
        :return: workspace GID as a string
        """
        _LOG.info(
            "Fetching workspace GID for workspace: %s",
            workspace_name or "first available",
        )
        # Fetch all available workspaces.
        opts: Dict[str, Any] = {}
        workspaces = self.workspaces_api.get_workspaces(opts)
        # Convert to list if needed.
        workspace_list = list(workspaces) if workspaces else []
        _LOG.info("Found %s workspaces", len(workspace_list))
        # Check if any workspaces exist.
        if not workspace_list:
            raise ValueError("No workspaces found")
        result = None
        # Search for specific workspace by name if provided.
        if workspace_name:
            for ws in workspace_list:
                if ws["name"].lower() == workspace_name.lower():
                    _LOG.info(
                        "Found workspace '%s' with GID: %s",
                        workspace_name,
                        ws["gid"],
                    )
                    result = str(ws["gid"])
                    break
            if result is None:
                raise ValueError(f"Workspace '{workspace_name}' not found")
        else:
            # Return first workspace if no name specified.
            _LOG.info(
                "Using first workspace: %s (GID: %s)",
                workspace_list[0]["name"],
                workspace_list[0]["gid"],
            )
            result = str(workspace_list[0]["gid"])
        return result

    def get_team_members(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all team members in a workspace.

        :param workspace_gid: workspace GID to query for users
        :return: user information with keys 'gid','name', and 'email'
        """
        _LOG.info("Fetching team members for workspace: %s", workspace_gid)
        # Fetch all users in the workspace.
        opts: Dict[str, Any] = {}
        users = self.users_api.get_users_for_workspace(workspace_gid, opts)
        # Convert to list if needed.
        users_list = list(users) if users else []
        _LOG.info("Found %s team members", len(users_list))
        # Extract relevant user information.
        result = [
            {"gid": u["gid"], "name": u["name"], "email": u.get("email", "N/A")}
            for u in users_list
        ]
        # Log member names.
        member_names = [r["name"] for r in result]
        _LOG.debug("Team members: %s", ", ".join(member_names))
        return result

    def get_user_by_name(
        self, workspace_gid: str, username: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific user by their name in a workspace.

        Search for a user by their display name (case-insensitive
        partial match).

        :param workspace_gid: workspace GID to search in
        :param username: username or partial name to search for
        :return: user with 'gid', 'name', and 'email', or None if not
            found
        """
        _LOG.info("Searching for user: %s", username)
        team_members = self.get_team_members(workspace_gid)
        res = None
        # Search for exact match first.
        for team_member in team_members:
            if team_member["name"].lower() == username.lower():
                _LOG.info("Found exact match: %s", team_member["name"])
                res = team_member
        # Search for partial match.
        for team_member in team_members:
            if username.lower() in team_member["name"].lower():
                _LOG.info("Found partial match: %s", team_member["name"])
                res = team_member
        if res is None:
            _LOG.warning("User '%s' not found in workspace", username)
        return res

    def get_user_tasks_detailed(
        self,
        workspace_gid: str,
        user_identifier: str,
        *,
        start_date: Optional[datetime_lib.datetime] = None,
        end_date: Optional[datetime_lib.datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get detailed task information including estimated time.

        Fetch all tasks for a user with extended fields including custom
        fields for time estimates, projects, tags, sections, and dates.

        :param workspace_gid: workspace GID to query
        :param user_identifier: user GID or username to retrieve tasks
            for
        :param start_date: start date for filtering tasks by creation
            date.
        :param end_date: end date for filtering tasks by creation date.
        :return: data with name, completion status, timestamps, custom
            fields, and project associations
        """
        # Resolve username to GID if needed.
        if not user_identifier.isdigit():
            _LOG.info("Resolving username '%s' to GID", user_identifier)
            user = self.get_user_by_name(workspace_gid, user_identifier)
            if not user:
                _LOG.error("User '%s' not found", user_identifier)
                return []
            user_gid = user["gid"]
            _LOG.debug("Resolved '%s' to GID: %s", user_identifier, user_gid)
        else:
            user_gid = user_identifier
        _LOG.info("Fetching detailed tasks for user GID: %s", user_gid)
        try:
            # Define query parameters for task retrieval with extended fields.
            opts = {
                "assignee": user_gid,
                "workspace": workspace_gid,
                "opt_fields": (
                    "name,completed,completed_at,created_at,modified_at,"
                    "projects.name,projects.gid,num_subtasks,memberships.section.name,"
                    "custom_fields,custom_fields.name,custom_fields.display_value,"
                    "custom_fields.number_value,due_on,due_at,start_on,"
                    "assignee.name,tags.name"
                ),
            }
            # Fetch all tasks for the user.
            _LOG.debug("Querying Asana API for detailed tasks...")
            tasks = self.tasks_api.get_tasks(opts)
            # Convert to list if generator.
            tasks_list = list(tasks) if tasks else []
            _LOG.info(
                "Retrieved %d tasks from API for user GID: %s",
                len(tasks_list),
                user_gid,
            )
            # Make start_date and end_date timezone-aware if they aren't already.
            if start_date and start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=datetime_lib.timezone.utc)
            if end_date and end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=datetime_lib.timezone.utc)
            # Filter tasks by date range if specified.
            filtered_tasks = []
            for task in tasks_list:
                # Parse creation date.
                created_at = (
                    dateutil_parser.parse(task["created_at"])
                    if task.get("created_at")
                    else None
                )
                # Apply start date filter.
                if start_date and created_at and created_at < start_date:
                    continue
                # Apply end date filter.
                if end_date and created_at and created_at > end_date:
                    continue
                # Add task to filtered results.
                filtered_tasks.append(task)
            _LOG.info(
                "Filtered to %d tasks within date range for user GID: %s",
                len(filtered_tasks),
                user_gid,
            )
            return filtered_tasks
        except arest.ApiException as e:
            _LOG.error("API error fetching detailed tasks: %s", e)
            raise
        except Exception as e:
            _LOG.error("Unexpected error fetching detailed tasks: %s", e)
            return []

    def extract_time_estimate(self, task: Dict[str, Any]) -> Optional[float]:
        """
        Extract time estimate from custom fields.

        Search through task custom fields for time estimation values.
        Looks for common field names like 'estimated time', 'estimate',
        'hours', etc.

        :param task: task data containing custom_fields
        :return: estimated hours as float, or None if not found
        """
        result = None
        if not task.get("custom_fields"):
            _LOG.debug(
                "No custom fields found for task: %s", task.get("gid", "unknown")
            )
            return result
        # Common field names for time estimates.
        time_field_names = [
            "estimated time",
            "estimate",
            "time estimate",
            "hours",
            "estimated hours",
            "effort",
        ]
        for field in task["custom_fields"]:
            field_name = field.get("name", "").lower()
            # Check if field name matches any time estimation pattern.
            if any(time_name in field_name for time_name in time_field_names):
                # Try number_value first, then display_value.
                if field.get("number_value") is not None:
                    result = float(field["number_value"])
                    _LOG.debug(
                        "Found time estimate %s hours in field '%s' for task: %s",
                        result,
                        field.get("name"),
                        task.get("gid", "unknown"),
                    )
                    break
                elif field.get("display_value"):
                    try:
                        result = float(field["display_value"])
                        _LOG.debug(
                            "Found time estimate %s hours in field '%s' for task: %s",
                            result,
                            field.get("name"),
                            task.get("gid", "unknown"),
                        )
                        break
                    except (ValueError, TypeError):
                        _LOG.warning(
                            "Could not parse display_value '%s' as float for task: %s",
                            field.get("display_value"),
                            task.get("gid", "unknown"),
                        )
        return result

    def create_task_dataframe(
        self,
        workspace_gid: str,
        user_identifiers: Optional[List[str]] = None,
        *,
        project_names: Optional[List[str]] = None,
        start_date: Optional[datetime_lib.datetime] = None,
        end_date: Optional[datetime_lib.datetime] = None,
        team_mapping: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """
        Create comprehensive task DataFrame for all users.

        Build a detailed DataFrame containing all task information for
        specified users, with optional filtering by project and date
        range. Includes time estimates, sprint information, and team
        assignments.

        :param workspace_gid: workspace GID to query
        :param user_identifiers: usernames or GIDs to analyze. If None,
            analyze all users in workspace
        :param project_names: project names to filter by and use as team
            names (e.g., ["tech-now", "tech-next"]). If provided, team
            will be determined from project name
        :param start_date: start date for filtering tasks by creation
            date
        :param end_date: end date for filtering tasks by creation date
        :param team_mapping: map username to team name. Only used if
            project_names is not provided
        :return: data with columns including user info, task details,
            dates, completion status, time estimates, project, sprint,
            section, tags, and subtasks
        """
        _LOG.info("Creating comprehensive task DataFrame")
        # Get users to analyze.
        team_members = []
        if user_identifiers:
            for user_id in user_identifiers:
                if user_id.isdigit():
                    # If GID, fetch user info.
                    opts = {"opt_fields": "name,email"}
                    user_info = self.users_api.get_user(user_id, opts)
                    team_members.append(
                        {
                            "gid": user_id,
                            "name": user_info["name"],
                            "email": user_info.get("email", "N/A"),
                        }
                    )
                else:
                    # If username, resolve to user.
                    user = self.get_user_by_name(workspace_gid, user_id)
                    if user:
                        team_members.append(user)
        else:
            # Get all team members if no specific users provided.
            team_members = self.get_team_members(workspace_gid)
        all_task_data = []
        # Process tasks for each team member.
        for member in team_members:
            _LOG.info("Processing tasks for: %s", member["name"])
            # Fetch detailed tasks for this user.
            tasks = self.get_user_tasks_detailed(
                workspace_gid,
                member["gid"],
                start_date=start_date,
                end_date=end_date,
            )
            # Process each task.
            for task in tasks:
                # Parse dates.
                created_at = (
                    dateutil_parser.parse(task["created_at"])
                    if task.get("created_at")
                    else None
                )
                completed_at = (
                    dateutil_parser.parse(task["completed_at"])
                    if task.get("completed_at")
                    else None
                )
                due_at = (
                    dateutil_parser.parse(task["due_at"])
                    if task.get("due_at")
                    else None
                )
                # Check if task is overdue.
                is_overdue = False
                if not task.get("completed") and due_at:
                    is_overdue = due_at < datetime_lib.datetime.now(
                        datetime_lib.timezone.utc
                    )
                # Extract time estimate from custom fields.
                estimated_hours = self.extract_time_estimate(task)
                # Calculate actual hours if task is completed.
                actual_hours = None
                if completed_at and created_at:
                    actual_hours = (
                        completed_at - created_at
                    ).total_seconds() / 3600
                # Extract projects, tags, and sections.
                projects = [p["name"] for p in task.get("projects", [])]
                project_gids = [p["gid"] for p in task.get("projects", [])]
                tags = [t["name"] for t in task.get("tags", [])]
                # Extract sections (sprints in Asana).
                sections = []
                sprints = []
                if task.get("memberships"):
                    for membership in task["memberships"]:
                        if membership.get("section"):
                            section_name = membership["section"]["name"]
                            sections.append(section_name)
                            # Identify sprint sections using common patterns.
                            if any(
                                keyword in section_name.lower()
                                for keyword in [
                                    "sprint",
                                    "iteration",
                                    "cycle",
                                    "week",
                                ]
                            ):
                                sprints.append(section_name)
                # Build task data dictionary.
                task_data = {
                    # User info.
                    "user_name": member["name"],
                    "user_email": member["email"],
                    "user_gid": member["gid"],
                    # Task info.
                    "task_name": task.get("name", "Untitled"),
                    "task_gid": task["gid"],
                    # Dates.
                    "created_at": created_at,
                    "completed_at": completed_at,
                    "due_on": task.get("due_on"),
                    "due_at": due_at,
                    "start_on": task.get("start_on"),
                    # Status.
                    "is_completed": task.get("completed", False),
                    "is_overdue": is_overdue,
                    # Time tracking.
                    "estimated_hours": estimated_hours,
                    "actual_hours": actual_hours,
                    # Organization.
                    "project": projects[0] if projects else None,
                    "all_projects": ", ".join(projects) if projects else None,
                    "project_gid": project_gids[0] if project_gids else None,
                    "tags": ", ".join(tags) if tags else None,
                    "section": sections[0] if sections else None,
                    "sprint": sprints[0] if sprints else None,
                    "all_sprints": ", ".join(sprints) if sprints else None,
                    "num_subtasks": task.get("num_subtasks", 0),
                }
                # Add team - either from project name or mapping.
                if project_names:
                    # Determine team from project name.
                    task_data["team"] = task_data["project"]
                elif team_mapping:
                    task_data["team"] = team_mapping.get(
                        member["name"], "Unassigned"
                    )
                else:
                    # No team mapping, use project as team (default).
                    task_data["team"] = task_data["project"]
                all_task_data.append(task_data)
        # Create DataFrame.
        df = pd.DataFrame(all_task_data)
        # Filter by project if specified.
        if project_names and len(df) > 0:
            df = df[df["project"].isin(project_names)]
            _LOG.info(
                "Filtered to %d tasks from projects: %s", len(df), project_names
            )
        _LOG.info("Created DataFrame with %d tasks", len(df))
        result = df
        return result

    def create_team_comparison_df(
        self, task_df: pd.DataFrame, metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Create team-level comparison DataFrame from task DataFrame.

        Aggregate task-level data to team-level metrics for comparison
        across teams. Requires task DataFrame to have 'team' column.

        :param task_df: data with 'team' column
        :param metrics: metrics to calculate. If None, calculate all
            available metrics including total_tasks, completed_tasks,
            completion_rate, estimated hours, and overdue rates
        :return: data with team-level aggregated metrics
        """
        if "team" not in task_df.columns:
            _LOG.error(
                "task_df missing 'team' column. Available columns: %s",
                task_df.columns.tolist(),
            )
            raise ValueError(
                "task_df must have 'team' column. Pass team_mapping or "
                "project_names to create_task_dataframe()"
            )

        _LOG.info("Creating team comparison DataFrame")
        _LOG.info("Found %d unique teams in data", task_df["team"].nunique())

        # Set default metrics if not provided.
        if metrics is None:
            metrics = [
                "total_tasks",
                "completed_tasks",
                "in_progress_tasks",
                "completion_rate",
                "total_estimated_hours",
                "avg_estimated_hours",
                "total_actual_hours",
                "overdue_tasks",
                "overdue_rate",
                "unique_users",
            ]
        team_stats = []
        # Calculate metrics for each team.
        for team_name in task_df["team"].unique():
            if team_name is None or (
                isinstance(team_name, float) and pd.isna(team_name)
            ):
                _LOG.warning("Skipping None/NaN team name")
                continue

            team_data = task_df[task_df["team"] == team_name]
            _LOG.debug(
                "Processing team: %s (%d tasks)", team_name, len(team_data)
            )

            stats = {"team": team_name}
            # Calculate each requested metric.
            if "total_tasks" in metrics:
                stats["total_tasks"] = len(team_data)
            if "completed_tasks" in metrics:
                stats["completed_tasks"] = team_data["is_completed"].sum()
            if "in_progress_tasks" in metrics:
                stats["in_progress_tasks"] = (~team_data["is_completed"]).sum()
            if "completion_rate" in metrics:
                if len(team_data) > 0:
                    stats["completion_rate"] = (
                        stats["completed_tasks"] / len(team_data)
                    ) * 100
                else:
                    stats["completion_rate"] = 0.0
            if "total_estimated_hours" in metrics:
                stats["total_estimated_hours"] = team_data[
                    "estimated_hours"
                ].sum()
            if "avg_estimated_hours" in metrics:
                stats["avg_estimated_hours"] = team_data["estimated_hours"].mean()
            if "total_actual_hours" in metrics:
                stats["total_actual_hours"] = team_data["actual_hours"].sum()
            if "overdue_tasks" in metrics:
                stats["overdue_tasks"] = team_data["is_overdue"].sum()
            if "overdue_rate" in metrics:
                active_tasks = (~team_data["is_completed"]).sum()
                if active_tasks > 0:
                    stats["overdue_rate"] = (
                        stats["overdue_tasks"] / active_tasks
                    ) * 100
                else:
                    stats["overdue_rate"] = 0.0
            if "unique_users" in metrics:
                stats["unique_users"] = team_data["user_name"].nunique()
            team_stats.append(stats)

        _LOG.info("Team comparison completed for %d teams", len(team_stats))
        result = pd.DataFrame(team_stats)
        return result

    def create_user_comparison_df(
        self, task_df: pd.DataFrame, metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Create user-level comparison DataFrame with aggregated metrics.

        Aggregate task-level data to user-level metrics for individual
        performance comparison.

        :param task_df: task data
        :param metrics: metrics to calculate. If None, calculate all
            available metrics including total_tasks, completed_tasks,
            completion_rate, estimated hours, and unique_projects
        :return: data with user-level aggregated metrics
        """
        # Set default metrics if not provided.
        if metrics is None:
            metrics = [
                "total_tasks",
                "completed_tasks",
                "completion_rate",
                "total_estimated_hours",
                "avg_estimated_hours",
                "overdue_tasks",
                "unique_projects",
            ]
        user_stats = []
        # Calculate metrics for each user.
        for user_name in task_df["user_name"].unique():
            user_data = task_df[task_df["user_name"] == user_name]
            stats = {
                "user_name": user_name,
                "user_email": user_data["user_email"].iloc[0],
            }
            # Add team if available.
            if "team" in task_df.columns:
                stats["team"] = user_data["team"].iloc[0]
            # Calculate each requested metric.
            if "total_tasks" in metrics:
                stats["total_tasks"] = len(user_data)
            if "completed_tasks" in metrics:
                stats["completed_tasks"] = user_data["is_completed"].sum()
            if "completion_rate" in metrics:
                if len(user_data) > 0:
                    stats["completion_rate"] = (
                        stats["completed_tasks"] / len(user_data)
                    ) * 100
                else:
                    stats["completion_rate"] = 0.0
            if "total_estimated_hours" in metrics:
                stats["total_estimated_hours"] = user_data[
                    "estimated_hours"
                ].sum()
            if "avg_estimated_hours" in metrics:
                stats["avg_estimated_hours"] = user_data["estimated_hours"].mean()
            if "overdue_tasks" in metrics:
                stats["overdue_tasks"] = user_data["is_overdue"].sum()
            if "unique_projects" in metrics:
                projects = user_data["all_projects"].dropna()
                unique_projects = set()
                for proj_str in projects:
                    unique_projects.update(proj_str.split(", "))
                stats["unique_projects"] = len(unique_projects)
            user_stats.append(stats)
        result = pd.DataFrame(user_stats)
        return result


# #############################################################################
# Convenience functions
# #############################################################################


def list_workspace_users(
    workspace_name: str, *, access_token: Optional[str] = None
) -> List[str]:
    """
    Get all usernames in a workspace.

    Convenience function to quickly see all available users in a
    workspace.

    :param workspace_name: name of workspace to query
    :param access_token: Asana access token
    :return: usernames (display names)
    """
    # Initialize analytics instance.
    analytics_instance = EnhancedAsanaAnalytics(access_token)
    # Get workspace GID.
    workspace_gid_local = analytics_instance.get_workspace_gid(workspace_name)
    # Get team members.
    team_members = analytics_instance.get_team_members(workspace_gid_local)
    # Extract usernames.
    result = [member["name"] for member in team_members]
    return result


def get_user_by_name(
    workspace_name: str,
    username: str,
    *,
    access_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a specific user by their name in a workspace.

    Convenience function to find a user without instantiating the class.

    :param workspace_name: name of workspace to search in
    :param username: username or partial name to search for
    :param access_token: Asana access token
    :return: user with 'gid', 'name', and 'email', or None if not found
    """
    # Initialize analytics instance.
    analytics_instance = EnhancedAsanaAnalytics(access_token)
    # Get workspace GID.
    workspace_gid_local = analytics_instance.get_workspace_gid(workspace_name)
    # Find user.
    result = analytics_instance.get_user_by_name(workspace_gid_local, username)
    return result


def create_kibana_ready_dataset(
    workspace_name: str,
    start_date: datetime_lib.datetime,
    end_date: datetime_lib.datetime,
    *,
    project_names: Optional[List[str]] = None,
    team_mapping: Optional[Dict[str, str]] = None,
    access_token: Optional[str] = None,
    user_list: Optional[List[str]] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Create Kibana-ready datasets with all metrics.

    Generate three DataFrames suitable for Kibana visualization: detailed
    task-level data, user-level aggregates, and team-level aggregates.
    By default, extracts ALL tasks from ALL users and ALL projects.
    The 'project' column can be used for filtering in Kibana.

    :param workspace_name: Asana workspace name to analyze
    :param start_date: start date for analysis period
    :param end_date: end date for analysis period
    :param project_names: project names to filter by
        (e.g., ["tech-now", "tech-next"]). If None, extract ALL projects.
        When provided, also uses project names as team names
    :param team_mapping: dict mapping usernames to team names.
        Alternative to project_names. If both are None, uses project as
        team
        - Example: {"John Doe": "tech-now", "Jane Smith": "tech-next"}
    :param access_token: Asana access token. If None, reads from
        environment variable ASANA_ACCESS_TOKEN
    :param user_list: list of specific usernames or GIDs to analyze. If
        None, analyze ALL team members
    :return: three DataFrames:
        - 'tasks': detailed task-level data with sprint/section info
        - 'users': user-level aggregated metrics
        - 'teams': team-level aggregated metrics
    """
    _LOG.info("=" * 70)
    _LOG.info("STARTING KIBANA DATASET CREATION")
    _LOG.info("=" * 70)
    _LOG.info("Workspace: %s", workspace_name)
    _LOG.info("Date range: %s to %s", start_date.date(), end_date.date())
    _LOG.info("Project filter: %s", project_names if project_names else "ALL")
    _LOG.info("User filter: %s", user_list if user_list else "ALL")

    # Initialize analytics instance.
    _LOG.info("Initializing Asana Analytics client...")
    analytics = EnhancedAsanaAnalytics(access_token)

    # Get workspace GID.
    _LOG.info("Resolving workspace GID for: %s", workspace_name)
    workspace_gid = analytics.get_workspace_gid(workspace_name)
    _LOG.info("Workspace GID resolved: %s", workspace_gid)

    # Create detailed task DataFrame.
    _LOG.info("-" * 70)
    _LOG.info("STEP 1/3: Creating detailed task DataFrame...")
    _LOG.info("-" * 70)
    task_df = analytics.create_task_dataframe(
        workspace_gid,
        user_identifiers=user_list,
        project_names=project_names,
        start_date=start_date,
        end_date=end_date,
        team_mapping=team_mapping,
    )
    _LOG.info("Task DataFrame created with %d rows", len(task_df))

    # Create user-level comparison DataFrame.
    _LOG.info("-" * 70)
    _LOG.info("STEP 2/3: Creating user-level aggregates...")
    _LOG.info("-" * 70)
    user_df = analytics.create_user_comparison_df(task_df)
    _LOG.info("User DataFrame created with %d rows", len(user_df))

    # Create team-level comparison DataFrame.
    _LOG.info("-" * 70)
    _LOG.info("STEP 3/3: Creating team-level aggregates...")
    _LOG.info("-" * 70)
    team_df = analytics.create_team_comparison_df(task_df)
    _LOG.info("Team DataFrame created with %d rows", len(team_df))

    _LOG.info("=" * 70)
    _LOG.info("DATASET CREATION COMPLETE!")
    _LOG.info("=" * 70)
    _LOG.info("Summary:")
    _LOG.info("  Tasks: %d rows", len(task_df))
    _LOG.info("  Users: %d rows", len(user_df))
    _LOG.info("  Teams: %d rows", len(team_df))
    _LOG.info("=" * 70)

    result = {"tasks": task_df, "users": user_df, "teams": team_df}
    return result


def save_to_ndjson(
    df: pd.DataFrame, filepath: str, index_name: Optional[str] = None
) -> None:
    """
    Save DataFrame to NDJSON format for Kibana/OpenSearch bulk upload.

    Convert DataFrame to newline-delimited JSON format suitable for
    Elasticsearch/OpenSearch bulk API ingestion.

    :param df: data to save
    :param filepath: output file path (e.g., 'asana_tasks.ndjson')
    :param index_name: optional index name to include in bulk action
        metadata. If None, only document data is written
    """
    _LOG.info("Saving DataFrame to NDJSON: %s", filepath)
    _LOG.info("DataFrame shape: %d rows, %d columns", len(df), len(df.columns))

    # Convert DataFrame to records (list of dicts).
    records = df.to_dict(orient="records")

    # Open file for writing.
    with open(filepath, "w") as f:
        for record in records:
            # Convert timestamps to ISO format strings.
            for key, value in record.items():
                if pd.isna(value):
                    # Convert NaN/None to null.
                    record[key] = None
                elif isinstance(value, pd.Timestamp):
                    # Convert pandas Timestamp to ISO string.
                    record[key] = value.isoformat()

            if index_name:
                # Write bulk API metadata line.
                action = {"index": {"_index": index_name}}
                f.write(json.dumps(action) + "\n")
            # Write document data line.
            f.write(json.dumps(record) + "\n")
    _LOG.info("Successfully saved %d records to %s", len(records), filepath)


def save_datasets_for_kibana(
    datasets: Dict[str, pd.DataFrame],
    output_dir: str = ".",
    *,
    use_ndjson: bool = True,
    index_prefix: str = "asana",
) -> Dict[str, str]:
    """
    Save all datasets to files for Kibana ingestion.

    Save task, user, and team DataFrames to either NDJSON or CSV format
    for Kibana/OpenSearch ingestion.

    :param datasets: data with 'tasks', 'users', 'teams'
    :param output_dir: directory to save files (default: current
        directory)
    :param use_ndjson: if True, save as NDJSON format. If False, save as
        CSV (default: True)
    :param index_prefix: prefix for index names when using NDJSON
        (default: 'asana')
    :return: mapping dataset names to saved file paths
    """
    _LOG.info("=" * 70)
    _LOG.info("SAVING DATASETS FOR KIBANA")
    _LOG.info("=" * 70)
    _LOG.info("Output directory: %s", output_dir)
    _LOG.info("Format: %s", "NDJSON" if use_ndjson else "CSV")
    saved_files = {}
    extension = "ndjson" if use_ndjson else "csv"
    for dataset_name, df in datasets.items():
        # Construct file path.
        filename = "{}_{}_{}.{}".format(
            index_prefix, dataset_name, "kibana", extension
        )
        filepath = "{}/{}".format(output_dir, filename)
        _LOG.info("Saving %s dataset (%d rows)...", dataset_name, len(df))
        if use_ndjson:
            # Save as NDJSON with index name.
            index_name = "{}-{}".format(index_prefix, dataset_name)
            save_to_ndjson(df, filepath, index_name=index_name)
        else:
            # Save as CSV.
            df.to_csv(filepath, index=False)
            _LOG.info("Saved to CSV: %s", filepath)
        saved_files[dataset_name] = filepath
    _LOG.info("=" * 70)
    _LOG.info("ALL DATASETS SAVED!")
    _LOG.info("=" * 70)
    for dataset_name, filepath in saved_files.items():
        _LOG.info("  %s: %s", dataset_name, filepath)
    _LOG.info("=" * 70)
    result = saved_files
    return result
