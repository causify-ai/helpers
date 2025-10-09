# %% [markdown]
# # Asana Guide

# %%
# !sudo /bin/bash -c "(source /venv/bin/activate; pip install -- asana python-dateutil)"

# %%
# %load_ext autoreload
# %autoreload 2

# %%
import datetime

import matplotlib.pyplot as plt
import pandas as pd

import helpers.asana_utils as hasautil

# %%
ASANA_ACCESS_TOKEN = "*"

# %% [markdown]
# # List All Available Users (Convenience Function)

# %%
# Get list of all usernames in workspace.
usernames = hasautil.list_workspace_users(
    workspace_name="Causify.AI", access_token=ASANA_ACCESS_TOKEN
)

print(f"\nFound {len(usernames)} users:")
for idx, name in enumerate(usernames, 1):
    print(f"  {idx}. {name}")

# %% [markdown]
# # Using the AsanaAnalytics Class Directly

# %%
# Create an instance of AsanaAnalytics.
analytics = hasautil.AsanaAnalytics(access_token=ASANA_ACCESS_TOKEN)
# Get workspace GID.
workspace_gid = analytics.get_workspace_gid(workspace_name="Causify.AI")
print(f"Workspace GID: {workspace_gid}")
# Get all team members.
team_members = analytics.get_team_members(workspace_gid)
print(f"\nTeam Members ({len(team_members)}):")
for member in team_members:
    print(f"  - {member['name']} ({member['email']}) [GID: {member['gid']}]")
# Get all usernames.
usernames_list = analytics.list_all_usernames(workspace_gid)
print(f"\nUsernames: {usernames_list}")

# %% [markdown]
# # Find Specific Users

# %%
# Find a single user by name (exact or partial match).
user = analytics.get_user_by_name(workspace_gid, "Shaunak")
if user:
    print(f"Found user: {user['name']} (GID: {user['gid']})")
else:
    print("User not found")

# Find multiple users by names.
target_users = ["Shaunak Dhande", "Jane Smith", "GP Saggese", "Krishna Taduri"]
found_users = analytics.get_users_by_names(workspace_gid, target_users)
print(f"\nSearched for: {target_users}")
print(f"Found {len(found_users)} users:")
for user in found_users:
    print(f"  - {user['name']}")

# %% [markdown]
# # Get tasks created for a Specific User in specified time

# %%
# Define date range.
start_date = datetime.datetime(2025, 10, 1, tzinfo=datetime.timezone.utc)
end_date = datetime.datetime(2025, 10, 9, tzinfo=datetime.timezone.utc)

# %%
username = "Shaunak Dhande"
tasks = analytics.get_user_tasks(
    workspace_gid,
    # Can use username OR GID!
    user_identifier=username,
    start_date=start_date,
    end_date=end_date,
)
print(f"\nTasks for {username}:")
print(f"Total tasks in period: {len(tasks)}")
# Show first 3 tasks.
for idx, task in enumerate(tasks, 1):
    print(f"\n  Task {idx}:")
    print(f"    Name: {task.get('name', 'N/A')}")
    print(f"    Completed: {task.get('completed', False)}")
    print(f"    Created: {task.get('created_at', 'N/A')}")
print("\n✓ You can also use GID instead of username if preferred")

# %% [markdown]
# # Calculate Statistics for a Single User (BY USERNAME!)

# %% [markdown]
# Comments (total_comments)
#
#     - What it is: Only the actual comments that users write on tasks
#     - Examples:
#         - "This looks good, approved!"
#         - "Can you update the deadline?"
#         - "I've completed the design mockups"
#     - Why it matters: Shows direct communication and collaboration on tasks
#
# Activity (total_activity)
#
#     - What it is: ALL events/actions on a task, including comments
#     - Examples:
#         - Comments (like above)
#         - Task status changes ("marked complete", "reopened")
#         - Assignee changes ("assigned to John")
#         - Due date changes ("due date changed to Oct 15")
#         - Attachments added
#         - Custom field updates
#         - Task moved to different section/project
#         - Subtasks created
#         - Followers added
#         - Likes/hearts on the task
#     - Why it matters: Shows overall engagement and how actively a task is being worked on

# %%
username = "Shaunak Dhande"

# Option A: Using months_back parameter with USERNAME.
stats_3m = analytics.calculate_user_stats(
    workspace_gid,
    user_identifier=username,  # Can use username OR GID!
    months_back=3,
)

print(f"\n3-Month Stats for {username}:")
print(f"  Period: {stats_3m['start_date']} to {stats_3m['end_date']}")
print(f"  Tasks Created: {stats_3m['tasks_created']}")
print(f"  Tasks Completed: {stats_3m['tasks_completed']}")
print(f"  Tasks In Progress: {stats_3m['tasks_in_progress']}")
print(f"  Completion Rate: {stats_3m['completion_rate']:.1f}%")
print(f"  Total Comments: {stats_3m['total_comments']}")
print(f"  Total Activity: {stats_3m['total_activity']}")
print(f"  Projects: {stats_3m['projects']}")

# %%
# Option B: Using specific date range with USERNAME.
stats_custom = analytics.calculate_user_stats(
    workspace_gid,
    user_identifier=username,  # Username works here too!
    start_date=datetime.datetime(2025, 7, 1, tzinfo=datetime.timezone.utc),
    end_date=datetime.datetime(2025, 10, 9, tzinfo=datetime.timezone.utc),
)

print(f"\nCustom Date Range Stats for {username}:")
print(f"  Period: {stats_custom['period_label']}")
print(f"  Tasks Created: {stats_custom['tasks_created']}")
print(f"  Completion Rate: {stats_custom['completion_rate']:.1f}%")

# %%
# Option C: You can still use GID if you have it.
if team_members:
    user_gid = team_members[0]["gid"]
    stats_by_gid = analytics.calculate_user_stats(
        workspace_gid, user_identifier=user_gid, months_back=1
    )
    print(f"\n✓ Stats calculated using GID: {user_gid}")

# %% [markdown]
# # Using Convenience Function with Username for stats

# %%
quick_stats = hasautil.get_user_stats(
    user_identifier="Shaunak Dhande",  # Username!
    workspace_gid=workspace_gid,
    months=3,
    access_token=ASANA_ACCESS_TOKEN,
)

print(f"Quick stats for Shaunak Dhande:")
print(f"  Completion Rate: {quick_stats['completion_rate']:.1f}%")
print(f"  Comments: {quick_stats['total_comments']}")

# %% [markdown]
# # Generate Team Report (All Users, Multiple Time Periods)

# %%
# Using convenience function - analyze last 1, 3, and 12 months.
report_periods = hasautil.get_team_report(
    workspace_name="Causify.AI",
    time_periods=[1, 3],
    access_token=ASANA_ACCESS_TOKEN,
)

print(f"\nReport generated at: {report_periods['generated_at']}")
print(f"Analyzed {len(report_periods['team_members'])} team members")
print(f"Time periods: {report_periods['time_periods']} months")

# Display summary for each member.
for member_data in report_periods["team_members"]:
    member = member_data["user"]
    print(f"\n{member['name']}:")

    for period, stats in member_data["stats_by_period"].items():
        if "error" not in stats:
            print(f"  {period}:")
            print(
                f"    Created: {stats['tasks_created']}, "
                f"Completed: {stats['tasks_completed']}, "
                f"Rate: {stats['completion_rate']:.1f}%"
            )

# %% [markdown]
# # Generate Team Report (Specific Date Range)

# %%
# Using convenience function - analyze specific date range.
start = datetime.datetime(2025, 9, 12)
end = datetime.datetime(2025, 10, 9)

report_daterange = hasautil.get_team_report(
    workspace_name="Causify.AI",
    start_date=start,
    end_date=end,
    access_token=ASANA_ACCESS_TOKEN,
)

print(f"\nDate range: {report_daterange['date_range']}")
print(f"Analyzed {len(report_daterange['team_members'])} team members")

# %% [markdown]
# # Generate Team Report (Specific Users Only)

# %%
# Generate report for only specific team members.
report_specific = hasautil.get_team_report(
    workspace_name="Causify.AI",
    start_date=start,
    end_date=end,
    usernames=["GP Saggese", "Chutian Ma"],
    access_token=ASANA_ACCESS_TOKEN,
)
print(f"Analyzed {len(report_specific['team_members'])} specific users")
for member_data in report_specific["team_members"]:
    member = member_data["user"]
    stats_key = list(member_data["stats_by_period"].keys())[0]
    stats = member_data["stats_by_period"][stats_key]
    if "error" not in stats:
        print(f"\n{member['name']}:")
        print(
            f"  Tasks: {stats['tasks_created']} created, "
            f"{stats['tasks_completed']} completed"
        )
        print(f"  Completion Rate: {stats['completion_rate']:.1f}%")

# %% [markdown]
# # Using Class Methods to Generate Report

# %%
# Create analytics instance.
analytics = hasautil.AsanaAnalytics(access_token=ASANA_ACCESS_TOKEN)
# Get workspace.
workspace_gid = analytics.get_workspace_gid("Causify.AI")
# Generate report using class method.
report_class = analytics.generate_team_report(
    workspace_gid, start_date=start, end_date=end, usernames=["Shaunak Dhande"]
)
print("Report generated using class methods!")

# %% [markdown]
# # Convert Report to Pandas DataFrame

# %%
members_data = []

for member_data in report_daterange["team_members"]:
    member = member_data["user"]
    stats_key = list(member_data["stats_by_period"].keys())[0]
    stats = member_data["stats_by_period"][stats_key]

    if "error" not in stats:
        members_data.append(
            {
                "Name": member["name"],
                "Email": member["email"],
                "Period": stats_key,
                "Tasks Created": stats["tasks_created"],
                "Tasks Completed": stats["tasks_completed"],
                "Tasks In Progress": stats["tasks_in_progress"],
                "Completion Rate (%)": round(stats["completion_rate"], 1),
                "Total Comments": stats["total_comments"],
                "Total Activity": stats["total_activity"],
                "Projects": ", ".join(stats["projects"][:3]),  # First 3 projects
            }
        )

df = pd.DataFrame(members_data)
print("\nTeam Performance DataFrame:")
print(df.head())

# Save to CSV.
# df.to_csv('asana_team_report.csv', index=False)
# print("\n✓ Saved to asana_team_report.csv")


# %%
df["Projects"].unique

# %% [markdown]
# # Visualization - Completion Rates Bar Chart

# %%
fig1 = hasautil.plot_completion_rates(
    report_daterange,
    figsize=(12, 6),
    # save_path='charts/completion_rates.png'  # Optional: save to file
)
plt.show()

print("Completion rates chart created")

# %% [markdown]
# # Visualization - Task Metrics (Created/Completed/In Progress)

# %%
fig2 = hasautil.plot_task_metrics(
    report_daterange,
    figsize=(14, 6),
    # save_path='charts/task_metrics.png'
)
plt.show()

print("Task metrics chart created")

# %% [markdown]
# # Visualization - Activity Metrics (Comments & Activity)

# %%
fig3 = hasautil.plot_activity_metrics(
    report_daterange,
    figsize=(12, 6),
    # save_path='charts/activity_metrics.png'
)
plt.show()

print("Activity metrics chart created")

# %% [markdown]
# # Visualization - Complete Dashboard (All Metrics)

# %%
fig4 = hasautil.create_summary_dashboard(
    report_daterange,
    figsize=(16, 10),
    # save_path='charts/dashboard.png'
)
plt.show()

print("Dashboard created with 4 panels showing all metrics")


# %% [markdown]
# # Visualization for Specific Time Period

# %%
# If you have multiple time periods, specify which one to visualize.
if "time_periods" in report_periods:
    # Visualize 3-month period specifically.
    fig5 = hasautil.plot_completion_rates(
        report_periods, period_key="3_month", figsize=(12, 6)
    )
    plt.title("Completion Rates - 3 Month Period")
    plt.show()

    print("Created chart for 3-month period")

# %% [markdown]
# # Compare Multiple Time Periods

# %%
# Create comparison for each time period.
if "time_periods" in report_periods:
    for period in report_periods["time_periods"]:
        period_key = f"{period}_month"
        print(f"\nCreating charts for {period}-month period...")

        fig = hasautil.plot_completion_rates(
            report_periods, period_key=period_key, figsize=(10, 5)
        )
        plt.show()

# %% [markdown]
# # Advanced - Get Project Completion Percentage

# %%
# You need a project GID for this (get from Asana URL).
# Example: https://app.asana.com/0/1234567890/list
# Project GID is 1234567890

# Uncomment and use your actual project GID:
project_gid = "1211138327783762"

project_stats = analytics.get_project_completion_percentage(
    project_gid=project_gid
)

print(f"Project: {project_stats['project_name']}")
print(f"Project: {project_gid}")
print(f"Total Tasks: {project_stats['total_tasks']}")
print(f"Completed: {project_stats['completed_tasks']}")
print(f"In Progress: {project_stats['in_progress_tasks']}")
print(f"Completion: {project_stats['completion_percentage']:.1f}%")

# %%
import json

# Save full report to JSON file.
with open("asana_team_report.json", "w") as f:
    json.dump(report_daterange, f, indent=2)

print("✓ Report saved to asana_team_report.json")

# %% [markdown]
# # Quick Usage Examples Summary

# %%
summary = """
CONVENIENCE FUNCTIONS (Easiest to use):
----------------------------------------
1. asautil.list_workspace_users(workspace_name, access_token)
   → Get list of all usernames

2. asautil.get_team_report(workspace_name, time_periods, access_token)
   → Generate report for all users, multiple time periods

3. asautil.get_team_report(workspace_name, start_date, end_date, access_token)
   → Generate report for specific date range

4. asautil.get_team_report(..., usernames=["John", "Jane"])
   → Generate report for specific users only

5. asautil.plot_completion_rates(report)
   → Create completion rates bar chart

6. asautil.plot_task_metrics(report)
   → Create task metrics grouped bar chart

7. asautil.plot_activity_metrics(report)
   → Create comments & activity chart

8. asautil.create_summary_dashboard(report)
   → Create comprehensive 4-panel dashboard


CLASS METHODS (More control):
------------------------------
analytics = asautil.AsanaAnalytics(access_token)

1. analytics.get_workspace_gid(workspace_name)
2. analytics.get_team_members(workspace_gid)
3. analytics.list_all_usernames(workspace_gid)
4. analytics.get_user_by_name(workspace_gid, username)
5. analytics.get_users_by_names(workspace_gid, usernames_list)
6. analytics.get_user_tasks(workspace_gid, user_gid, start_date, end_date)
7. analytics.calculate_user_stats(workspace_gid, user_gid, months_back)
8. analytics.generate_team_report(workspace_gid, time_periods, start_date, end_date)
9. analytics.get_project_completion_percentage(project_gid)
"""
