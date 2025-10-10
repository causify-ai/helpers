"""
Import as:

import helpers.asana_utils as hasautil
"""

import collections as collections_lib
import datetime as datetime_lib
import logging
import os
from typing import Any, Dict, List, Optional

import asana
import asana.rest as arest
import dateutil.parser as dateutil_parser
import matplotlib.pyplot as plt
import numpy as np

_LOG = logging.getLogger(__name__)


# #############################################################################
# AsanaAnalytics
# #############################################################################


class AsanaAnalytics:

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
        # Search for specific workspace by name if provided.
        if workspace_name:
            for ws in workspace_list:
                if ws["name"].lower() == workspace_name.lower():
                    _LOG.info(
                        "Found workspace '%s' with GID: %s",
                        workspace_name,
                        ws["gid"],
                    )
                    return str(ws["gid"])
            raise ValueError(f"Workspace '{workspace_name}' not found")
        # Return first workspace if no name specified.
        _LOG.info(
            "Using first workspace: %s (GID: %s)",
            workspace_list[0]["name"],
            workspace_list[0]["gid"],
        )
        work = workspace_list[0]["gid"]
        return str(work)

    def get_team_members(self, workspace_gid_param: str) -> List[Dict[str, Any]]:
        """
        Get all team members in a workspace.

        :param workspace_gid_param: workspace GID to query for users
        :return: user information with keys 'gid','name', and 'email'
        """
        _LOG.info("Fetching team members for workspace: %s", workspace_gid_param)
        # Fetch all users in the workspace.
        opts: Dict[str, Any] = {}
        users = self.users_api.get_users_for_workspace(workspace_gid_param, opts)
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
        self, workspace_gid_param: str, username: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific user by their name in a workspace.

        Search for a user by their display name (case-insensitive
        partial match).

        :param workspace_gid_param: workspace GID to search in
        :param username: username or partial name to search for
        :return: user with 'gid', 'name', and 'email', or None if not
            found
        """
        _LOG.info("Searching for user: %s", username)
        team_members = self.get_team_members(workspace_gid_param)
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
        _LOG.warning("User '%s' not found in workspace", username)
        return res

    def get_users_by_names(
        self, workspace_gid_param: str, usernames: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get multiple users by their names in a workspace.

        :param workspace_gid_param: workspace GID to search in
        :param usernames: usernames or partial names to search for
        :return: user dictionaries that were found
        """
        _LOG.info("Searching for %s users", len(usernames))
        users = []
        for username in usernames:
            user = self.get_user_by_name(workspace_gid_param, username)
            if user:
                users.append(user)
        _LOG.info(
            "Found %s out of %s requested users", len(users), len(usernames)
        )
        return users

    def list_all_usernames(self, workspace_gid_param: str) -> List[str]:
        """
        Get all usernames in a workspace.

        :param workspace_gid_param: workspace GID to query
        :return: usernames (display names)
        """
        _LOG.info("Listing all usernames in workspace: %s", workspace_gid_param)
        team_members = self.get_team_members(workspace_gid_param)
        usernames = [team_member["name"] for team_member in team_members]
        _LOG.info("Found %s usernames", len(usernames))
        return usernames

    def get_user_tasks(
        self,
        workspace_gid_param: str,
        user_identifier: str,
        *,
        start_date: Optional[datetime_lib.datetime] = None,
        end_date: Optional[datetime_lib.datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks assigned to a user within a date range.

        :param workspace_gid_param: workspace GID to query
        :param user_identifier: user GID or username to retrieve tasks
            for
        :param start_date: start date for filtering tasks by creation
            date.
        :param end_date: end date for filtering tasks by creation date.
        :return: data including name, completion status, timestamps, and
            project associations
        """
        # Resolve username to GID if needed.
        if not user_identifier.isdigit():
            _LOG.info("Resolving username '%s' to GID", user_identifier)
            user = self.get_user_by_name(workspace_gid_param, user_identifier)
            if not user:
                _LOG.error("User '%s' not found", user_identifier)
                return []
            user_gid = user["gid"]
        else:
            user_gid = user_identifier
        _LOG.info("Fetching tasks for user: %s", user_gid)
        try:
            # Define query parameters for task retrieval.
            opts = {
                "assignee": user_gid,
                "workspace": workspace_gid_param,
                "opt_fields": (
                    "name,completed,completed_at,created_at,modified_at,"
                    "projects.name,num_subtasks,memberships.section.name"
                ),
            }
            # Fetch all tasks for the user.
            _LOG.debug("Querying Asana API for tasks...")
            tasks = self.tasks_api.get_tasks(opts)
            # Convert to list if generator.
            tasks_list = list(tasks) if tasks else []
            _LOG.info("Retrieved %s tasks from API", len(tasks_list))
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
                "Filtered to %s tasks within date range", len(filtered_tasks)
            )
            return filtered_tasks
        except arest.ApiException as e:
            _LOG.error("Error fetching user tasks: %s", e)
            raise
        except Exception as e:
            _LOG.error("Unexpected error fetching user tasks: %s", e)
            return []

    def get_task_stories(self, task_gid: str) -> List[Dict[str, Any]]:
        """
        Get all comments and activity entries for a task.

        :param task_gid: task GID to query for activity
        :return: data containing activity type, text content, creator
            information, and timestamps
        """
        _LOG.debug("Fetching stories for task: %s", task_gid)
        # Fetch all stories (comments and activity) for the task.
        opts = {"opt_fields": "type,text,created_by.name,created_at"}
        stories = self.stories_api.get_stories_for_task(task_gid, opts)
        # Convert to list if generator.
        stories_list = list(stories) if stories else []
        _LOG.debug("Found %s stories for task %s", len(stories_list), task_gid)
        return stories_list

    def calculate_user_stats(
        self,
        workspace_gid_param: str,
        user_identifier: str,
        *,
        months_back: Optional[int] = None,
        start_date: Optional[datetime_lib.datetime] = None,
        end_date: Optional[datetime_lib.datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a user over a time period.

        Analyze a user's task activity including creation, completion, project
        involvement, and engagement metrics over a specified time period. Support
        both relative time periods (months back) and absolute date ranges.

        :param workspace_gid_param: workspace GID to query
        :param user_identifier: user GID or username to calculate statistics for
        :param months_back: number of months to look back from current date. Ignored
            if start_date and end_date are provided
            - 1: last month
            - 3: last quarter
            - 12: last year
        :param start_date: explicit start date for analysis period. If provided with
            end_date, overrides months_back parameter
        :param end_date: explicit end date for analysis period. If None and start_date
            is provided, defaults to current time
        :return: data containing comprehensive user statistics including:
            - tasks_created: total tasks created in period
            - tasks_completed: total tasks completed in period
            - completion_rate: percentage of created tasks that were completed
            - projects: list of project names user is involved in
            - total_comments: total comments made across all tasks
            - tasks_by_project: breakdown of tasks per project
            - completed_by_project: breakdown of completed tasks per project
        """
        # Resolve username to GID if needed.
        if not user_identifier.isdigit():
            _LOG.info("Resolving username '%s' to GID", user_identifier)
            user = self.get_user_by_name(workspace_gid_param, user_identifier)
            if not user:
                _LOG.error("User '%s' not found", user_identifier)
                raise ValueError(
                    f"User '{user_identifier}' not found in workspace"
                )
            user_gid = user["gid"]
            username = user["name"]
        else:
            user_gid = user_identifier
            username = user_identifier
        _LOG.info("Calculating stats for user: %s (GID: %s)", username, user_gid)
        # Determine the date range for analysis.
        if start_date is not None and end_date is not None:
            # Use explicit date range.
            analysis_start = start_date
            analysis_end = end_date
            period_label = f"{start_date.date()} to {end_date.date()}"
        elif start_date is not None:
            # Start date provided but no end date, use current time.
            analysis_start = start_date
            analysis_end = datetime_lib.datetime.now(datetime_lib.timezone.utc)
            period_label = f"{start_date.date()} to {analysis_end.date()}"
        else:
            # Use months_back (default behavior).
            if months_back is None:
                months_back = 1
            analysis_end = datetime_lib.datetime.now(datetime_lib.timezone.utc)
            analysis_start = analysis_end - datetime_lib.timedelta(
                days=30 * months_back
            )
            period_label = f"{months_back}_months"
        _LOG.info(
            "Analysis period: %s to %s",
            analysis_start.date(),
            analysis_end.date(),
        )
        # Ensure dates are timezone-aware.
        if analysis_start.tzinfo is None:
            analysis_start = analysis_start.replace(
                tzinfo=datetime_lib.timezone.utc
            )
        if analysis_end.tzinfo is None:
            analysis_end = analysis_end.replace(tzinfo=datetime_lib.timezone.utc)
        # Fetch all tasks for the user in the date range.
        tasks = self.get_user_tasks(
            workspace_gid_param,
            user_gid,
            start_date=analysis_start,
            end_date=analysis_end,
        )
        # Initialize statistics dictionary.
        user_stats = {
            "user_gid": user_gid,
            "username": username,
            "period_label": period_label,
            "start_date": analysis_start.isoformat(),
            "end_date": analysis_end.isoformat(),
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_in_progress": 0,
            "projects": set(),
            "total_comments": 0,
            "total_activity": 0,
            "completion_rate": 0.0,
            "tasks_by_project": collections_lib.defaultdict(int),
            "completed_by_project": collections_lib.defaultdict(int),
        }
        _LOG.info("Processing %s tasks for statistics", len(tasks))
        # Process each task to gather statistics.
        for task in tasks:
            # Increment task creation counter.
            user_stats["tasks_created"] += 1
            # Debug log task structure.
            _LOG.debug("Processing task: %s", task.get("name", "Unnamed"))
            _LOG.debug("Task has projects: %s", task.get("projects", "None"))
            # Process project associations.
            if task.get("projects"):
                for project in task["projects"]:
                    # Extract project name.
                    project_name = project.get("name", "Unknown")
                    _LOG.debug("  Found project: %s", project_name)
                    user_stats["projects"].add(project_name)
                    user_stats["tasks_by_project"][project_name] += 1
                    # Track completions per project.
                    if task.get("completed"):
                        completed_at = (
                            dateutil_parser.parse(task["completed_at"])
                            if task.get("completed_at")
                            else None
                        )
                        if (
                            completed_at
                            and analysis_start <= completed_at <= analysis_end
                        ):
                            user_stats["completed_by_project"][project_name] += 1
            else:
                _LOG.debug(
                    "  Task '%s' has no projects associated",
                    task.get("name", "Unnamed"),
                )
            # Count completed tasks within the period.
            if task.get("completed"):
                completed_at = (
                    dateutil_parser.parse(task["completed_at"])
                    if task.get("completed_at")
                    else None
                )
                if (
                    completed_at
                    and analysis_start <= completed_at <= analysis_end
                ):
                    user_stats["tasks_completed"] += 1
            else:
                user_stats["tasks_in_progress"] += 1
            # Fetch comments and activity for the task.
            try:
                stories = self.get_task_stories(task["gid"])
                comments = [s for s in stories if s.get("type") == "comment"]
                user_stats["total_comments"] += len(comments)
                # Count all activity (not just comments).
                user_stats["total_activity"] = user_stats.get(
                    "total_activity", 0
                ) + len(stories)
            except Exception as e:
                # Handle rate limiting or API errors gracefully.
                _LOG.warning(
                    "Could not fetch stories for task %s: %s", task["gid"], e
                )
        # Calculate completion rate percentage.
        if user_stats["tasks_created"] > 0:
            user_stats["completion_rate"] = (
                user_stats["tasks_completed"] / user_stats["tasks_created"]
            ) * 100
        _LOG.info(
            "Stats calculated: %s created, %s completed, %.1f%% completion rate",
            user_stats["tasks_created"],
            user_stats["tasks_completed"],
            user_stats["completion_rate"],
        )
        # Convert sets to lists for JSON serialization.
        user_stats["projects"] = list(user_stats["projects"])
        user_stats["tasks_by_project"] = dict(user_stats["tasks_by_project"])
        user_stats["completed_by_project"] = dict(
            user_stats["completed_by_project"]
        )
        return user_stats

    def get_project_completion_percentage(
        self, project_gid: str, *, user_identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate the completion percentage for a project or board.

        Analyze all tasks in a project to determine overall completion status,
        optionally filtered to a specific user's tasks.

        :param project_gid: project GID to analyze
        :param user_identifier: user GID or username to filter tasks. If None, include
            all tasks in the project
        :return: data containing project completion statistics:
            - project_gid: the analyzed project's GID
            - project_name: the project's name
            - total_tasks: total number of tasks in project
            - completed_tasks: number of completed tasks
            - in_progress_tasks: number of incomplete tasks
            - completion_percentage: percentage of tasks completed
        """
        # Resolve username to GID if needed.
        user_gid = None
        if user_identifier:
            if not user_identifier.isdigit():
                _LOG.info("Resolving username '%s' to GID", user_identifier)
                # Need workspace_gid to resolve username.
                workspace_gid_local = self.get_workspace_gid()
                user = self.get_user_by_name(workspace_gid_local, user_identifier)
                if not user:
                    _LOG.warning(
                        "User '%s' not found, analyzing all users",
                        user_identifier,
                    )
                else:
                    user_gid = user["gid"]
            else:
                user_gid = user_identifier
        try:
            # First, get the project details to fetch the name.
            _LOG.info("Fetching project details for GID: %s", project_gid)
            project_opts = {"opt_fields": "name"}
            project_info = self.projects_api.get_project(
                project_gid, project_opts
            )
            project_name = project_info.get("name", "Unknown Project")
            _LOG.info("Project name: %s", project_name)
            # Define query parameters for task retrieval.
            opts = {"opt_fields": "name,completed,assignee.gid"}
            # Fetch all tasks in the project.
            _LOG.info("Fetching tasks for project: %s", project_name)
            tasks = self.tasks_api.get_tasks_for_project(project_gid, opts)
            tasks_list = list(tasks) if tasks else []
            # Filter tasks by user if specified.
            if user_gid:
                tasks_list = [
                    t
                    for t in tasks_list
                    if t.get("assignee") and t["assignee"].get("gid") == user_gid
                ]
                _LOG.info(
                    "Filtered to %s tasks for user %s",
                    len(tasks_list),
                    user_identifier,
                )
            # Calculate task counts.
            total_tasks = len(tasks_list)
            completed_tasks = sum(1 for t in tasks_list if t.get("completed"))
            # Calculate completion percentage.
            completion_percentage = (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            )
            _LOG.info(
                "Project '%s': %s/%s tasks completed (%.1f%%)",
                project_name,
                completed_tasks,
                total_tasks,
                completion_percentage,
            )
            return {
                "project_gid": project_gid,
                "project_name": project_name,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": total_tasks - completed_tasks,
                "completion_percentage": completion_percentage,
            }
        except arest.ApiException as e:
            _LOG.error("Error calculating project completion: %s", e)
            raise
        except Exception as e:
            _LOG.error("Unexpected error calculating project completion: %s", e)
            return {
                "project_gid": project_gid,
                "project_name": "Error",
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "completion_percentage": 0,
                "error": str(e),
            }

    def generate_team_report(
        self,
        workspace_gid_param: str,
        *,
        time_periods: Optional[List[int]] = None,
        start_date: Optional[datetime_lib.datetime] = None,
        end_date: Optional[datetime_lib.datetime] = None,
        usernames: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive statistics for all team members across multiple
        time periods.

        Create a complete team performance report that analyzes all members across
        different time horizons or a specific date range. This provides a holistic
        view of team productivity and engagement.

        :param workspace_gid_param: workspace GID to analyze
        :param time_periods: list of time periods in months to analyze. Each value
            represents the number of months to look back from present. Ignored if
            start_date and end_date are provided
            - Default: [1, 3, 12] for monthly, quarterly, and yearly analysis
        :param start_date: explicit start date for analysis. If provided with end_date,
            overrides time_periods and analyzes only this single date range
        :param end_date: explicit end date for analysis. If None and start_date provided,
            defaults to current time
        :param usernames: list of specific usernames to analyze. If None, analyze all
            team members in the workspace
        :return: data containing team-wide report with:
            - generated_at: timestamp of report generation
            - workspace_gid: analyzed workspace
            - team_members: list of member statistics for each time period or date range
            - time_periods: analyzed time periods (if using relative periods)
            - date_range: analyzed date range (if using explicit dates)
        """
        _LOG.info("=" * 60)
        _LOG.info("Starting team report generation")
        _LOG.info("=" * 60)
        # Fetch team members - either specific users or all.
        if usernames:
            _LOG.info("Filtering report to specific users: %s", usernames)
            team_members = self.get_users_by_names(workspace_gid_param, usernames)
            if not team_members:
                _LOG.error("None of the specified users were found")
                raise ValueError(f"No users found matching: {usernames}")
        else:
            _LOG.info("Analyzing all team members")
            team_members = self.get_team_members(workspace_gid_param)
        # Determine analysis mode: date range vs time periods.
        if start_date is not None or end_date is not None:
            # Use explicit date range mode.
            use_date_range = True
            if time_periods is None:
                time_periods = []
            _LOG.info("Using date range mode: %s to %s", start_date, end_date)
        else:
            # Use time periods mode.
            use_date_range = False
            if time_periods is None:
                time_periods = [1, 3, 12]
            _LOG.info("Using time periods mode: %s months", time_periods)
        # Initialize report structure.
        team_report: Dict[str, Any] = {
            "generated_at": datetime_lib.datetime.now().isoformat(),
            "workspace_gid": workspace_gid_param,
            "team_members": [],
        }
        # Add appropriate metadata based on mode.
        if use_date_range:
            team_report["date_range"] = {
                "start": start_date.isoformat() if start_date else None,
                "end": (
                    end_date.isoformat()
                    if end_date
                    else datetime_lib.datetime.now().isoformat()
                ),
            }
        else:
            team_report["time_periods"] = time_periods
        # Calculate statistics for each team member.
        for idx, team_member in enumerate(team_members, 1):
            _LOG.info(
                "Processing member %s/%s: %s",
                idx,
                len(team_members),
                team_member["name"],
            )
            # Initialize member statistics container.
            member_stats = {"user": team_member, "stats_by_period": {}}
            if use_date_range:
                # Analyze single date range.
                try:
                    # Compute user statistics for the date range.
                    period_stats = self.calculate_user_stats(
                        workspace_gid_param,
                        team_member["gid"],
                        start_date=start_date,
                        end_date=end_date,
                    )
                    period_key = period_stats["period_label"]
                    member_stats["stats_by_period"][period_key] = period_stats
                    _LOG.info(
                        "  ✓ Completed analysis for %s", team_member["name"]
                    )
                except Exception as e:
                    # Log error and continue with other members.
                    _LOG.error(
                        "  ✗ Error calculating stats for %s: %s",
                        team_member["name"],
                        e,
                    )
                    member_stats["stats_by_period"]["custom_range"] = {
                        "error": str(e)
                    }
            else:
                # Analyze multiple time periods.
                for months in time_periods:
                    _LOG.info(
                        "  Analyzing %s-month period for %s",
                        months,
                        team_member["name"],
                    )
                    try:
                        # Compute user statistics for the period.
                        period_stats = self.calculate_user_stats(
                            workspace_gid_param,
                            team_member["gid"],
                            months_back=months,
                        )
                        member_stats["stats_by_period"][
                            f"{months}_month"
                        ] = period_stats
                        _LOG.info("  ✓ Completed %s-month analysis", months)
                    except Exception as e:
                        # Log error and continue with other periods.
                        _LOG.error(
                            "  ✗ Error calculating %s-month stats for %s: %s",
                            months,
                            team_member["name"],
                            e,
                        )
                        member_stats["stats_by_period"][f"{months}_month"] = {
                            "error": str(e)
                        }
            # Add member statistics to report.
            team_report["team_members"].append(member_stats)
        _LOG.info("=" * 60)
        _LOG.info(
            "Team report generation completed for %s members", len(team_members)
        )
        _LOG.info("=" * 60)
        return team_report


# Convenience functions for quick access.
def get_user_stats(
    user_identifier: str,
    workspace_gid_param: str,
    months: int,
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get user statistics with a single function call.

    Convenience wrapper around AsanaAnalytics.calculate_user_stats() for
    quick access to user statistics without instantiating the class
    directly.

    :param user_identifier: user GID or username to analyze
    :param workspace_gid_param: workspace GID where user belongs
    :param months: number of months to analyze (1, 3, or 12)
    :param access_token: Asana access token
    :return: user statistics with performance metrics
    """
    # Initialize analytics instance.
    analytics_instance = AsanaAnalytics(access_token)
    # Calculate and return user statistics.
    result = analytics_instance.calculate_user_stats(
        workspace_gid_param, user_identifier, months_back=months
    )
    return result


def get_team_report(
    workspace_name: str,
    *,
    time_periods: Optional[List[int]] = None,
    start_date: Optional[datetime_lib.datetime] = None,
    end_date: Optional[datetime_lib.datetime] = None,
    usernames: Optional[List[str]] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a full team performance report with a single function call.

    Convenience wrapper around AsanaAnalytics.generate_team_report() for
    quick access to team-wide statistics without instantiating the class
    directly. Support both relative time periods and explicit date
    ranges.

    :param workspace_name: name of workspace to analyze
    :param time_periods: list of time periods in months to analyze.
        Ignored if start_date and end_date are provided (default: [1, 3,
        12])
    :param start_date: explicit start date for analysis period. If
        provided with end_date, analyze only this date range
    :param end_date: explicit end date for analysis period. If None and
        start_date provided, defaults to current time
    :param usernames: list of specific usernames to analyze. If None,
        analyze all team members
    :param access_token: Asana access token.
    :return: comprehensive team report with statistics for all members
        across all specified time periods or the given date range
    """
    # Initialize analytics instance.
    analytics_instance = AsanaAnalytics(access_token)
    # Get workspace GID.
    workspace_gid_local = analytics_instance.get_workspace_gid(workspace_name)
    # Generate and return team report.
    result = analytics_instance.generate_team_report(
        workspace_gid_local,
        time_periods=time_periods,
        start_date=start_date,
        end_date=end_date,
        usernames=usernames,
    )
    return result


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
    analytics_instance = AsanaAnalytics(access_token)
    # Get workspace GID.
    workspace_gid_local = analytics_instance.get_workspace_gid(workspace_name)
    # Get and return usernames.
    result = analytics_instance.list_all_usernames(workspace_gid_local)
    return result


# Visualization functions.
def plot_completion_rates(
    team_report: Dict[str, Any],
    *,
    period_key: Optional[str] = None,
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None,
) -> Any:
    """
    Create a bar chart of task completion rates for team members.

    Generate a horizontal bar chart showing completion rates for each
    team member from the report data.

    :param team_report: team report from get_team_report()
    :param period_key: specific period to visualize (e.g., '1_month',
        '3_month'). If None, use first available
    :param figsize: figure size as (width, height)
    :param save_path: path to save the figure
    :return: matplotlib figure object
    """
    _LOG.info("Creating completion rates bar chart")
    # Extract data for visualization.
    names = []
    completion_rates = []
    for member_info in team_report["team_members"]:
        user_info = member_info["user"]
        # Get the specified period or first available.
        if period_key:
            period_stats = member_info["stats_by_period"].get(period_key, {})
        else:
            period_key = list(member_info["stats_by_period"].keys())[0]
            period_stats = member_info["stats_by_period"][period_key]
        # Skip if error or no data.
        if "error" in period_stats or period_stats.get("tasks_created", 0) == 0:
            continue
        names.append(user_info["name"])
        completion_rates.append(period_stats["completion_rate"])
    # Create bar chart.
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(names, completion_rates, color="steelblue")
    # Add value labels on bars.
    for i, (name, rate) in enumerate(zip(names, completion_rates)):
        ax.text(
            rate,
            i,
            f"{rate:.1f}%",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
        )
    # Formatting.
    ax.set_xlabel("Completion Rate (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Team Member", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Task Completion Rates - {period_key}", fontsize=14, fontweight="bold"
    )
    ax.set_xlim(0, 110)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    # Save if path provided.
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        _LOG.info("Saved chart to %s", save_path)
    return fig


def plot_task_metrics(
    team_report: Dict[str, Any],
    *,
    period_key: Optional[str] = None,
    figsize: tuple = (14, 6),
    save_path: Optional[str] = None,
) -> Any:
    """
    Create a grouped bar chart of task creation and completion metrics.

    Generate a comparison chart showing tasks created, tasks completed,
    and tasks in progress for each team member.

    :param team_report: team report from get_team_report()
    :param period_key: specific period to visualize. If None, use first
        available
    :param figsize: figure size as (width, height)
    :param save_path: path to save the figure. If None, display only
    :return: matplotlib figure object
    """
    _LOG.info("Creating task metrics grouped bar chart")
    # Extract data.
    names = []
    created = []
    completed = []
    in_progress = []
    for member_info in team_report["team_members"]:
        user_info = member_info["user"]
        # Get the specified period or first available.
        if period_key:
            period_stats = member_info["stats_by_period"].get(period_key, {})
        else:
            period_key = list(member_info["stats_by_period"].keys())[0]
            period_stats = member_info["stats_by_period"][period_key]
        # Skip if error.
        if "error" in period_stats:
            continue
        names.append(user_info["name"])
        created.append(period_stats.get("tasks_created", 0))
        completed.append(period_stats.get("tasks_completed", 0))
        in_progress.append(period_stats.get("tasks_in_progress", 0))
    # Set up grouped bars.
    x = np.arange(len(names))
    width = 0.25
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(x - width, created, width, label="Created", color="#3498db")
    ax.bar(x, completed, width, label="Completed", color="#2ecc71")
    ax.bar(x + width, in_progress, width, label="In Progress", color="#f39c12")
    # Formatting.
    ax.set_xlabel("Team Member", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of Tasks", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Task Metrics by Team Member - {period_key}",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    # Save if path provided.
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        _LOG.info("Saved chart to %s", save_path)
    return fig


def plot_activity_metrics(
    team_report: Dict[str, Any],
    *,
    period_key: Optional[str] = None,
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None,
) -> Any:
    """
    Create a bar chart of comments and activity metrics.

    Generate a chart showing total comments and total activity for each
    team member.

    :param team_report: team report from get_team_report()
    :param period_key: specific period to visualize. If None, use first
        available
    :param figsize: figure size as (width, height)
    :param save_path: path to save the figure. If None, display only
    :return: matplotlib figure object
    """
    _LOG.info("Creating activity metrics bar chart")
    # Extract data.
    names = []
    comments = []
    activity = []
    for member_info in team_report["team_members"]:
        user_info = member_info["user"]
        # Get the specified period or first available.
        if period_key:
            period_stats = member_info["stats_by_period"].get(period_key, {})
        else:
            period_key = list(member_info["stats_by_period"].keys())[0]
            period_stats = member_info["stats_by_period"][period_key]
        # Skip if error.
        if "error" in period_stats:
            continue
        names.append(user_info["name"])
        comments.append(period_stats.get("total_comments", 0))
        activity.append(period_stats.get("total_activity", 0))
    # Set up grouped bars.
    x = np.arange(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(x - width / 2, comments, width, label="Comments", color="#9b59b6")
    ax.bar(
        x + width / 2, activity, width, label="Total Activity", color="#e74c3c"
    )
    # Formatting.
    ax.set_xlabel("Team Member", fontsize=12, fontweight="bold")
    ax.set_ylabel("Count", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Comments & Activity by Team Member - {period_key}",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    # Save if path provided.
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        _LOG.info("Saved chart to %s", save_path)
    return fig


def create_summary_dashboard(
    team_report: Dict[str, Any],
    *,
    period_key: Optional[str] = None,
    figsize: tuple = (16, 10),
    save_path: Optional[str] = None,
) -> Any:
    """
    Create a comprehensive dashboard with all metrics.

    Generate a multi-panel dashboard showing completion rates, task
    metrics, and activity metrics in a single figure.

    :param team_report: team report from get_team_report()
    :param period_key: specific period to visualize. If None, use first
        available
    :param figsize: figure size as (width, height)
    :param save_path: path to save the figure. If None, display only
    :return: matplotlib figure object
    """
    _LOG.info("Creating summary dashboard")
    # Extract data.
    names = []
    completion_rates = []
    created = []
    completed = []
    comments = []
    activity = []
    for member_info in team_report["team_members"]:
        user_info = member_info["user"]
        # Get the specified period or first available.
        if period_key:
            period_stats = member_info["stats_by_period"].get(period_key, {})
        else:
            period_key = list(member_info["stats_by_period"].keys())[0]
            period_stats = member_info["stats_by_period"][period_key]
        # Skip if error.
        if "error" in period_stats:
            continue
        names.append(user_info["name"])
        completion_rates.append(period_stats.get("completion_rate", 0))
        created.append(period_stats.get("tasks_created", 0))
        completed.append(period_stats.get("tasks_completed", 0))
        comments.append(period_stats.get("total_comments", 0))
        activity.append(period_stats.get("total_activity", 0))
    # Create subplots.
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle(
        f"Team Performance Dashboard - {period_key}",
        fontsize=16,
        fontweight="bold",
    )
    # 1. Completion Rates.
    ax1 = axes[0, 0]
    ax1.barh(names, completion_rates, color="steelblue")
    ax1.set_xlabel("Completion Rate (%)", fontweight="bold")
    ax1.set_title("Task Completion Rates", fontweight="bold")
    ax1.set_xlim(0, 110)
    ax1.grid(axis="x", alpha=0.3)
    # 2. Tasks Created vs Completed.
    ax2 = axes[0, 1]
    x = np.arange(len(names))
    width = 0.35
    ax2.bar(x - width / 2, created, width, label="Created", color="#3498db")
    ax2.bar(x + width / 2, completed, width, label="Completed", color="#2ecc71")
    ax2.set_ylabel("Number of Tasks", fontweight="bold")
    ax2.set_title("Tasks Created vs Completed", fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=45, ha="right")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)
    # 3. Comments and Activity.
    ax3 = axes[1, 0]
    ax3.bar(x - width / 2, comments, width, label="Comments", color="#9b59b6")
    ax3.bar(
        x + width / 2, activity, width, label="Total Activity", color="#e74c3c"
    )
    ax3.set_ylabel("Count", fontweight="bold")
    ax3.set_title("Comments & Activity", fontweight="bold")
    ax3.set_xticks(x)
    ax3.set_xticklabels(names, rotation=45, ha="right")
    ax3.legend()
    ax3.grid(axis="y", alpha=0.3)
    # 4. Summary Stats Table.
    ax4 = axes[1, 1]
    ax4.axis("off")
    # Calculate totals.
    total_created = sum(created)
    total_completed = sum(completed)
    avg_completion = np.mean(completion_rates) if completion_rates else 0
    total_comments = sum(comments)
    summary_text = f"""
    SUMMARY STATISTICS
    {'=' * 40}

    Total Tasks Created:     {total_created}
    Total Tasks Completed:   {total_completed}
    Average Completion Rate: {avg_completion:.1f}%
    Total Comments:          {total_comments}
    Total Team Members:      {len(names)}

    Period: {period_key}
    """
    ax4.text(
        0.1,
        0.5,
        summary_text,
        fontsize=12,
        family="monospace",
        verticalalignment="center",
    )
    plt.tight_layout()
    # Save if path provided.
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        _LOG.info("Saved dashboard to %s", save_path)
    return fig


# Example usage and testing.
if __name__ == "__main__":
    # Configure logging for example usage.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Initialize analytics client.
    analytics = AsanaAnalytics()
    # Get the first available workspace.
    workspace_gid = analytics.get_workspace_gid()
    _LOG.info("Using workspace: %s", workspace_gid)
    # Generate comprehensive team report for multiple time periods.
    report = analytics.generate_team_report(
        workspace_gid, time_periods=[1, 3, 12]
    )
    # Print summary statistics for each team member.
    _LOG.info("Team Report Generated at %s", report["generated_at"])
    for member_data in report["team_members"]:
        member = member_data["user"]
        _LOG.info("\n%s (%s)", member["name"], member["email"])
        # Display statistics for each time period.
        for period, stats in member_data["stats_by_period"].items():
            if "error" not in stats:
                _LOG.info("  %s:", period)
                _LOG.info("    Tasks Created: %s", stats["tasks_created"])
                _LOG.info("    Tasks Completed: %s", stats["tasks_completed"])
                _LOG.info("    Completion Rate: %.1f%%", stats["completion_rate"])
                _LOG.info("    Projects: %s", ", ".join(stats["projects"]))
                _LOG.info("    Total Comments: %s", stats["total_comments"])
