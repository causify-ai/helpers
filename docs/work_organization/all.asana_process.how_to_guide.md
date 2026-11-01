# Asana Process

## Summary

- This document describes how we use Asana to track projects
- This document points to the existing docs instead of repeating them
  - See [Resources](#resources)
- Asana complements GitHub:
  - GitHub tracks the technical work
  - Asana tracks the non-technical work and the high-level view of a project

## What Goes in Asana

- Asana is for non-technical and high-level work:
  - Work organization tasks
  - Marketing and funding
  - Onboarding
  - Hiring and contributor feedback
  - Work that does not map easily to coding
  - Work that is not ready to be filed as a GitHub issue
- GitHub is for technical work:
  - Specs and questions about an issue or PR
  - Debugging help
  - PR reviews
- The boundary is not strict
  - A GitHub Project includes many GitHub issues
  - Work can live in a GitHub Project, in Asana tasks, or in a Google Doc
  - Each person can pick the tool that is more comfortable
- Do not discuss in Slack what can be discussed in GitHub or Asana
  - A Slack message cannot be referenced from other places
- See
  [`all.team_collaboration.how_to_guide.md`](/docs/work_organization/all.team_collaboration.how_to_guide.md)
  for the full communication rules

## Set Up a Project in Asana

- Create one Asana project for each GitHub project
- Name the Asana project `Proj - <project name>`
- Use the Asana project to:
  - Track non-technical work
  - Track the project at a higher level than GitHub
- The project lead uses the Asana board to communicate status to other teams and
  team leaders
- Link the Asana project from:
  - The GitHub project details
  - The `Channel Overview` canvas of the `proj-<project-name>` Slack channel
- Each team (e.g., Infra/Devops, DataPull) has a catch-all project for its issues
- See "How to set up a new project" in
  [`all.github_projects_process.reference.md`](/docs/work_organization/all.github_projects_process.reference.md)
  for all the steps

## Track Milestones

- Create each milestone in both GitHub and Asana
  - Use the same name and the same date
  - In GitHub, use the `Milestones` page of the repository
  - In Asana, use a milestone task in the project
- Each milestone is a deliverable that a person can run or demo
- Link the milestone to the section of the master plan
  - Do not copy the plan
- The project lead owns the milestones
  - See [`all.project_lead.how_to_guide.md`](/docs/work_organization/all.project_lead.how_to_guide.md)

## Report Status

- Sprints run from Sunday to Saturday
- The project owner posts a status update every Friday
  - First, the GitHub project status update
  - Then, the Asana status update
- The GitHub status update is often the source for the Asana update
- See "Sprint process" in
  [`all.github_projects_process.reference.md`](/docs/work_organization/all.github_projects_process.reference.md)
  for the deadlines and the sections of the update

## Track Requests

- Acknowledge a request with a link to where the work is done or tracked
  - E.g., a PR, a GitHub issue, an Asana task
- If the work cannot be done now, track the request before replying
  - Create a scratch Asana task (or a GitHub issue) to collect the requests
  - Paste the text of each request, one per bullet or checkbox
  - Reply with the link to the scratch task
  - Check off each request when done
- See "Acknowledge a request with a link" in
  [`all.team_collaboration.how_to_guide.md`](/docs/work_organization/all.team_collaboration.how_to_guide.md)

## Track Leads

- Use one Asana task to track each lead
- Post all the emails of the lead thread in the task
  - Post one email per comment
  - Post the emails in chronological order, oldest first, when possible
  - Include the sender, the date, and the text of each email
- The goal is to track what was said, what was answered, and what is still open
  - Anyone can read the task and understand the status of the lead without
    opening the mailbox
- Keep the task up to date
  - Post each new email when it arrives
  - Post your own replies too
  - Do not summarize or merge several emails in one comment

## Receive Asana Notifications

- Asana sends emails from `no-reply@asana.com` about:
  - The tasks assigned to you for today
  - New activity in your tasks
  - New task assignments
- See "Asana" in
  [`all.organize_email.how_to_guide.md`](/docs/onboarding/all.organize_email.how_to_guide.md)
  for how to filter these emails

## Other Uses of Asana

- **Hiring**: the HiringMeister manages the Hiring project and creates one task
  per intern
  - See [`all.hiring_process.how_to_guide.md`](/docs/onboarding/all.hiring_process.how_to_guide.md)
- **Contributor feedback**: the scoring forms are distributed to the scorers in
  Asana
  - See [`all.contributor_feedback.how_to_guide.md`](/docs/work_organization/all.contributor_feedback.how_to_guide.md)
- **Onboarding**: Asana tasks are the channel for business and high-level
  questions of a new teammate
  - See [`all.onboarding_checklist.reference.md`](/docs/onboarding/all.onboarding_checklist.reference.md)

## Analyze Asana Data

- Use `helpers/asana_utils.py` to compute task completion rates and team activity
  reports from Asana
  - See [`all.asana_utils.how_to_guide.md`](/docs/work_organization/all.asana_utils.how_to_guide.md) for
    how to get an access token and run the reports
- The tutorial `tutorials/Asana` shows the Asana REST API in notebooks

## Resources

- Project setup, milestones, and sprint status updates:
  [`all.github_projects_process.reference.md`](/docs/work_organization/all.github_projects_process.reference.md)
- Where to communicate and how to acknowledge requests:
  [`all.team_collaboration.how_to_guide.md`](/docs/work_organization/all.team_collaboration.how_to_guide.md)
- Project lead responsibilities:
  [`all.project_lead.how_to_guide.md`](/docs/work_organization/all.project_lead.how_to_guide.md)
- Issues, PRs, and labels in GitHub:
  [`all.use_github.how_to_guide.md`](/docs/work_organization/all.use_github.how_to_guide.md)
- Asana analytics code and API access:
  [`all.asana_utils.how_to_guide.md`](/docs/work_organization/all.asana_utils.how_to_guide.md)
- Asana notification emails:
  [`all.organize_email.how_to_guide.md`](/docs/onboarding/all.organize_email.how_to_guide.md)
- Hiring project:
  [`all.hiring_process.how_to_guide.md`](/docs/onboarding/all.hiring_process.how_to_guide.md)
