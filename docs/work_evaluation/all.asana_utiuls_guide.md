<!-- toc -->

- [Asana Analytics Guide](#asana-analytics-guide)
  * [Overview](#overview)
  * [Extract Asana Access Token](#extract-asana-access-token)
    + [Method 1: Personal Access Token (Recommended for Personal Use)](#method-1-personal-access-token-recommended-for-personal-use)
    + [Method 2: Oauth Application (For Production/Multi-User Apps)](#method-2-oauth-application-for-productionmulti-user-apps)
    + [Security Best Practices](#security-best-practices)
  * [Installation & Setup](#installation--setup)
    + [Required Dependencies](#required-dependencies)
    + [Import the Module](#import-the-module)
  * [Quick Start](#quick-start)
    + [Basic Usage - Individual User Stats](#basic-usage---individual-user-stats)
    + [Generate a Team Report](#generate-a-team-report)
    + [Function Reference](#function-reference)
    + [Convenience Functions](#convenience-functions)
    + [Visualization Functions](#visualization-functions)
  * [Usage Examples](#usage-examples)
    + [Example 1: Analyze Specific Team Members](#example-1-analyze-specific-team-members)
    + [Example 2: Custom Date Range Analysis](#example-2-custom-date-range-analysis)
    + [Example 3: Team Report with Date Range](#example-3-team-report-with-date-range)
    + [Example 4: Project Completion Analysis](#example-4-project-completion-analysis)
    + [Example 5: List Available Users](#example-5-list-available-users)
  * [Visualization Examples](#visualization-examples)
    + [Create Completion Rate Chart](#create-completion-rate-chart)
    + [Create Task Metrics Comparison](#create-task-metrics-comparison)
    + [Create Activity Metrics Chart](#create-activity-metrics-chart)
    + [Create Complete Dashboard](#create-complete-dashboard)
  * [Understanding the Stats Output](#understanding-the-stats-output)
    + [User Stats Dictionary Structure](#user-stats-dictionary-structure)
    + [Team Report Structure](#team-report-structure)
  * [Tips & Best Practices](#tips--best-practices)
    + [Performance Optimization](#performance-optimization)
    + [Common Use Cases](#common-use-cases)

<!-- tocstop -->

# Asana Analytics Guide

We have a asana utils code at : [`/helpers/asana_utils.py`](/helpers/asana_utils.py) which is a comprehensive Python module for analyzing team performance and productivity metrics in Asana.

## Overview

The Asana Analytics module provides powerful tools to:

- Track individual and team task completion rates
- Analyze productivity across different time periods
- Generate comprehensive team performance reports
- Visualize metrics with publication-ready charts
- Calculate project completion percentages

## Extract Asana Access Token

### Method 1: Personal Access Token (Recommended for Personal Use)

- Log into Asana at app.asana.com
- Click your profile photo in the top right corner
- Select "My Settings"
- Navigate to the "Apps" tab
- Scroll down to "Developer apps"
- Click "Manage Developer Apps"
- Click "+ Create new token"
- Give your token a descriptive name (e.g., "Analytics Script")
- Click "Create token"
- Copy the token immediately - you won't be able to see it again!
- Store it securely (see setup instructions below)

### Method 2: Oauth Application (For Production/Multi-User Apps)

If you're building an application that multiple users will access:

- Go to the Asana Developer Console
- Create a new OAuth application
- Follow the OAuth 2.0 flow to get access tokens

### Security Best Practices

- Never commit your token to version control!

## Installation & Setup

### Required Dependencies

```bash
pip install asana python-dateutil matplotlib numpy
```
- We need to install the dependencies on the fly, for example in a notebook:

```bash
!sudo /bin/bash -c "(source /venv/bin/activate; pip install -- asana python-dateutil)"
```

### Import the Module
```python
import helpers.asana_utils as hasautil
```

## Quick Start

### Basic Usage - Individual User Stats

```python
# Option 1: Pass Token Directly.
analytics = hasautil.AsanaAnalytics(access_token='your_token')

# Option 2: Use Environment Variable (Recommended).
analytics = hasautil.AsanaAnalytics()  # Reads ASANA_ACCESS_TOKEN.

# Get Workspace.
workspace_gid = analytics.get_workspace_gid()

# Calculate Stats for a User (Last 3 Months).
stats = analytics.calculate_user_stats(
    workspace_gid,
    'John Doe',  # Can use username or GID.
    months_back=3
)

print(f"Tasks created: {stats['tasks_created']}")
print(f"Completion rate: {stats['completion_rate']:.1f}%")
```
### Generate a Team Report

```python
# Full Team Report Across Multiple Time Periods.
report = analytics.generate_team_report(
    workspace_gid,
    time_periods=[1, 3, 12]  # Last month, quarter, year.
)

# Or Use Convenience Function.
report = hasautil.get_team_report(
    'My Workspace',
    time_periods=[1, 3, 12]
)
```

### Function Reference

- Core Class: `AsanaAnalytics`

| Function | Purpose | Key Parameters | Returns |
|----------|---------|----------------|---------|
| `__init__()` | Initialize the analytics client | `access_token` (optional) | AsanaAnalytics instance |
| `get_workspace_gid()` | Get workspace ID | `workspace_name` (optional) | Workspace GID string |
| `get_team_members()` | List all workspace members | `workspace_gid` | List of user dicts with gid, name, email |
| `get_user_by_name()` | Find user by name | `workspace_gid`, `username` | User dict or None |
| `get_user_tasks()` | Get tasks for a user | `workspace_gid`, `user_identifier`, `start_date`, `end_date` | List of task dicts |
| `calculate_user_stats()` | Calculate user metrics | `workspace_gid`, `user_identifier`, `months_back` or `start_date`/`end_date` | Stats dictionary |
| `generate_team_report()` | Full team analysis | `workspace_gid`, `time_periods` or `start_date`/`end_date`, `usernames` (optional) | Team report dict |
| `get_project_completion_percentage()` | Project progress | `project_gid`, `user_identifier` (optional) | Completion stats dict |

### Convenience Functions

| Function | Purpose | Use Case |
|----------|---------|----------|
| `get_user_stats()` | Quick user stats | One-line user analysis without instantiating class |
| `get_team_report()` | Quick team report | One-line team analysis with workspace name |
| `list_workspace_users()` | List all usernames | Discover available users in workspace |

### Visualization Functions

| Function | Creates | Best For |
|----------|---------|----------|
| `plot_completion_rates()` | Horizontal bar chart | Comparing completion rates across team |
| `plot_task_metrics()` | Grouped bar chart | Comparing created vs completed vs in-progress |
| `plot_activity_metrics()` | Bar chart | Analyzing comments and activity levels |
| `create_summary_dashboard()` | 4-panel dashboard | Executive overview with all metrics |\

## Usage Examples

### Example 1: Analyze Specific Team Members

```python
# Analyze Only Specific Team Members.
report = hasautil.get_team_report(
    'Engineering',
    usernames=['GP', 'Krishna', 'Heanh'],
    time_periods=[1, 3]
)
```

### Example 2: Custom Date Range Analysis

```python
# Analyze Q1 2025.
start = datetime(2025, 1, 1, tzinfo=timezone.utc)
end = datetime(2025, 3, 31, tzinfo=timezone.utc)

stats = analytics.calculate_user_stats(
    workspace_gid,
    'Shaunak Dhande',
    start_date=start,
    end_date=end
)
```

### Example 3: Team Report with Date Range

```python
# Full Team Report for Specific Date Range.
report = analytics.generate_team_report(
    workspace_gid,
    start_date=start,
    end_date=end
)
```

### Example 4: Project Completion Analysis

```python
# Check Project Completion Percentage.
project_stats = analytics.get_project_completion_percentage(
    project_gid='1234567890',
    user_identifier='John Doe'  # Optional: filter to specific user.
)

print(f"Project: {project_stats['project_name']}")
print(f"Completion: {project_stats['completion_percentage']:.1f}%")
print(f"Progress: {project_stats['completed_tasks']}/{project_stats['total_tasks']} tasks")
```

### Example 5: List Available Users

```python
# See All Users in Workspace.
usernames = hasautil.list_workspace_users('Marketing')
print(f"Available users: {', '.join(usernames)}")
```

## Visualization Examples

### Create Completion Rate Chart

```python
# Generate Team Report First.
report = hasautil.get_team_report('Engineering', time_periods=[1, 3, 12])

# Create and Save Completion Rate Chart.
hasautil.plot_completion_rates(
    report,
    period_key='3_month',  # Focus on quarterly data.
    save_path='completion_rates.png'
)
```

### Create Task Metrics Comparison

```python
# Compare Tasks Created, Completed, and In-Progress.
hasautil.plot_task_metrics(
    report,
    period_key='1_month',
    figsize=(16, 8),
    save_path='task_metrics.png'
)
```

### Create Activity Metrics Chart

```python
# Show Comments and Activity Levels.
hasautil.plot_activity_metrics(
    report,
    period_key='1_month',
    save_path='activity_metrics.png'
)
```

### Create Complete Dashboard

```python
# Generate Comprehensive 4-Panel Dashboard.
hasautil.create_summary_dashboard(
    report,
    period_key='3_month',
    figsize=(18, 12),
    save_path='team_dashboard.png'
)
```

## Understanding the Stats Output

### User Stats Dictionary Structure

```python
{
    'user_gid': '1234567890',
    'username': 'John Doe',
    'period_label': '3_months',
    'start_date': '2024-07-10T00:00:00+00:00',
    'end_date': '2024-10-10T00:00:00+00:00',
    'tasks_created': 45,
    'tasks_completed': 38,
    'tasks_in_progress': 7,
    'completion_rate': 84.4,  # Percentage.
    'projects': ['Project A', 'Project B', 'Project C'],
    'total_comments': 156,
    'total_activity': 203,
    'tasks_by_project': {
        'Project A': 20,
        'Project B': 15,
        'Project C': 10
    },
    'completed_by_project': {
        'Project A': 18,
        'Project B': 12,
        'Project C': 8
    }
}
```

### Team Report Structure

```python
{
    'generated_at': '2024-10-10T15:30:00',
    'workspace_gid': '0987654321',
    'time_periods': [1, 3, 12],  # or 'date_range' if using explicit dates.
    'team_members': [
        {
            'user': {
                'gid': '1234567890',
                'name': 'John Doe',
                'email': 'john@example.com'
            },
            'stats_by_period': {
                '1_month': { ... },
                '3_month': { ... },
                '12_month': { ... }
            }
        },
        # ... more team members
    ]
}
```

## Tips & Best Practices

### Performance Optimization

- `Rate Limiting`: The `Asana API` has rate limits. For large teams, the script includes automatic handling and logging of rate limit issues
- `Caching`: For repeated analyses, store workspace and user GIDs to avoid redundant API calls
- `Batch Processing`: When analyzing multiple users, use `generate_team_report()` instead of calling `calculate_user_stats()` repeatedly

### Common Use Cases

| Scenario | Best Function | Parameters |
|----------|--------------|------------|
| Monthly performance review | `generate_team_report()` | `time_periods=[1]` |
| Quarterly planning | `generate_team_report()` | `time_periods=[3]` |
| Sprint retrospective | `calculate_user_stats()` | Custom `start_date`/`end_date` |
| Project health check | `get_project_completion_percentage()` | `project_gid` |
| Individual 1-on-1s | `calculate_user_stats()` | `user_identifier`, `months_back=1` |
