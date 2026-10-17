# Project Lead

<!-- toc -->

- [Summary](#summary)
- [Project Lead vs Tech Lead](#project-lead-vs-tech-lead)
- [Coordinate and Distribute the Work](#coordinate-and-distribute-the-work)
  * [Keep the Plan and the Board Current](#keep-the-plan-and-the-board-current)
  * [Assign the Work](#assign-the-work)
  * [Unblock People](#unblock-people)
  * [Keep the Review Queue Moving](#keep-the-review-queue-moving)
- [Keep the Agenda](#keep-the-agenda)
  * [Prepare the Meetings](#prepare-the-meetings)
  * [Run the Meetings](#run-the-meetings)
  * [Close the Loop After the Meetings](#close-the-loop-after-the-meetings)
- [Be GP's Right Hand](#be-gps-right-hand)
  * [Know the State of the Project](#know-the-state-of-the-project)
  * [Report Status](#report-status)
  * [Escalate Decisions](#escalate-decisions)
  * [Protect GP's Time](#protect-gps-time)
- [Checklist](#checklist)
- [Resources](#resources)

<!-- tocstop -->

## Summary

- This document describes the responsibilities of the project lead, i.e., the
  person who runs the team on a project
- The project lead has 3 jobs:
  - Coordinate and distribute the work
  - Keep the agenda
  - Be GP's right hand on the project
- The goal is that:
  - Everyone on the team always knows what to work on next
  - GP knows the state of the project without having to ask
- This document points to the existing docs instead of repeating them
  - See [Resources](#resources)

## Project Lead vs Tech Lead

- The project lead runs the team and the process
  - Works with the plan, the board, the meetings, and the people
- A tech lead earns the role by technical excellence
  - See "Tech leads" in
    [`all.organize_your_work.how_to_guide.md`](all.organize_your_work.how_to_guide.md#tech-leads)
- One person can be both, but the jobs are different
  - A project lead does not have to be the best coder on the team
  - A project lead has to make sure that the best technical ideas get done

## Coordinate and Distribute the Work

### Keep the Plan and the Board Current

- Own the plan of the project
  - See [`all.plan_work.how_to_guide.md`](../planning/all.plan_work.how_to_guide.md)
- Keep every task as a GitHub issue on the project board
  - Each issue has an owner, a status, and an ETA
  - See [`all.use_github.how_to_guide.md`](all.use_github.how_to_guide.md)
- File issues only for the immediate work, i.e., the next version of the plan
  - The plan often changes after the first iteration
  - In each issue, point to the section of the plan instead of copying it
- Keep the backlog ordered by priority
  - Priority changes are announced to the team, not applied silently
- Create the milestones in GitHub and Asana
  - See "How to set up a new project" in
    [`all.github_projects_process.reference.md`](all.github_projects_process.reference.md#how-to-set-up-a-new-project)
- Name the PRs of the master plan by component
  - E.g., `PR_S11`, see "Rules for the Plan" in
    [`all.plan_work.how_to_guide.md`](../planning/all.plan_work.how_to_guide.md#rules-for-the-plan)
- Update the plan and the progress log after every merged PR

### Assign the Work

- Make sure each person has 2 issues at the same time
  - One issue is blocked or in review while the other one is in progress
  - See "Ping Team Leaders when you are out of tasks" in
    [`all.team_collaboration.how_to_guide.md`](all.team_collaboration.how_to_guide.md#ping-team-leaders-when-you-are-out-of-tasks)
- Assign a new issue before a person runs out of work
  - Watch the board for people with all PRs in review
- Assign the issues as soon as they are filed
  - If the plan is clear, the assignee can start executing right away
  - Do not wait for the next meeting
- Ask the assignee to start an issue like this:
  - Mark the issue as `In Progress`
  - Post a realistic ETA
  - Post a short plan of 3-4 bullet points to show that the goal is understood
  - See "Updating an Issue" in
    [`all.use_github.how_to_guide.md`](all.use_github.how_to_guide.md#updating-an-issue)
- Discuss what, by when, and how in the issue and in the project channel
  - Move to execution only when everyone agrees
- Match the task to the person:
  - Skills and interests
  - Availability and weekly commitment
  - Level of experience (small issues first for new members)
- Keep one accountable owner per issue
  - Pairing is fine, but one name is on the issue
- Split big tasks into issues that fit in a few days
  - Avoid tasks that nobody can review in one sitting

### Unblock People

- Read the blockers reported in the issues every day
  - Do not wait for the weekly meeting
- For each blocker, find the one who can help and ping that person
  - Record the action and the owner in the issue
- If a blocker is outside the team, escalate it to GP
  - See [Escalate Decisions](#escalate-decisions)
- Help new team members get started
  - Point to the onboarding docs
  - Answer questions or find someone who can

### Keep the Review Queue Moving

- Check the open PRs every day
- Make sure each PR has a reviewer assigned
- Chase reviews that are waiting for more than a day or two
- Push authors to address review comments quickly
- Do not become the bottleneck
  - Delegate reviews to the team
  - Review only what needs a lead decision

## Keep the Agenda

### Prepare the Meetings

- The project lead owns the agenda of the project meetings
  - Technical sync-up (one or two times per week)
  - Weekly blocker meeting
  - See "Sync-ups" in
    [`all.team_collaboration.how_to_guide.md`](all.team_collaboration.how_to_guide.md#sync-ups)
- Update the agenda in the Gdoc one day before the meeting
  - Broadcast it by email or with a tag in the Gdoc
- Fill the agenda with 2-3 issues
  - Give priority to the issues that are controversial, blocking, or finished
  - Do not spend time on successes or easy stuff
- Skip a meeting when the agenda is empty
  - Keep it short when there is not much to discuss

### Run the Meetings

- Start on time and keep the discussion on the agenda
- Move deep technical discussions to a follow-up with the people involved
- For each topic, end with a decision, an owner, and a date
- Make sure that the team picks a facilitator for the blocker meeting
  - See "Meeting facilitators" in
    [`all.organize_your_work.how_to_guide.md`](all.organize_your_work.how_to_guide.md#meeting-facilitators)

### Close the Loop After the Meetings

- Write down the decisions, the action items, the owners, and the dates
  - Put them in the issue or in the weekly summary
- Send the notes to the team and to GP
- At the next meeting, start by reviewing the open action items
- Read the morning TODO emails of the team
  - See "Morning TODO email" in
    [`all.team_collaboration.how_to_guide.md`](all.team_collaboration.how_to_guide.md#morning-todo-email)
  - Check that the issues, the hours, and the blockers match the plan

## Be GP's Right Hand

### Know the State of the Project

- Be able to answer these questions at any time:
  - What is done, what is in progress, and what is next
  - Who is working on what
  - What is blocked and why
  - What is late and what is the new ETA
- Read the issues, the PRs, and the progress log
  - Do not rely on people to tell you

### Report Status

- Send GP a short status update on a fixed cadence
  - Agree with GP on the cadence (e.g., weekly)
- Use the same format every time:
  - Done since the last update
  - Next steps
  - Blockers and risks
  - Decisions needed from GP
- Report bad news early
  - A late task reported on day 1 is a scheduling problem
  - A late task reported on the deadline is a crisis
- Avoid surprises: GP should never learn about a problem from someone else

### Escalate Decisions

- Decide what you can decide
  - Do not bring GP what the team can resolve
- Escalate only when:
  - The decision changes the scope, the priority, or the deadline
  - The decision needs access or budget that the team does not have
  - Two people disagree and cannot converge
- For each escalation, bring:
  - The problem in 1-2 lines
  - The options with pros and cons
  - Your recommendation
  - The date by which you need an answer
- After GP decides, communicate the decision to the team
  - Record it in the issue or in the decision log

### Protect GP's Time

- Handle the follow-ups yourself
  - Chase the owners, the reviewers, and the dates
- Prepare GP for the meetings that need GP
  - Share the agenda and the context ahead of time
- Make GP's reviews easy:
  - Small PRs with a clear description
  - A link to the issue and the plan
- Act on behalf of GP inside the agreed scope
  - Check with GP on the first few cases to calibrate the scope

## Checklist

- Daily:
  - [ ] Read the blockers on the board and unblock them
  - [ ] Check the open PRs and chase the reviews
  - [ ] Read the morning TODO emails
  - [ ] Check that each person has enough work for the next days
- Before each meeting:
  - [ ] Update the agenda one day before
  - [ ] Broadcast the agenda
- After each meeting:
  - [ ] Write down decisions, owners, and dates
  - [ ] Send the notes to the team and to GP
- Weekly:
  - [ ] Update the plan, the board, and the progress log
  - [ ] Send the status update to GP
  - [ ] List the decisions that need GP

## Resources

- Plan, PR loop, and progress log:
  [`all.plan_work.how_to_guide.md`](../planning/all.plan_work.how_to_guide.md)
- Idea, project, and task:
  [`all.issue_workflow.explanation.md`](all.issue_workflow.explanation.md)
- Issues, PRs, labels, and review:
  [`all.use_github.how_to_guide.md`](all.use_github.how_to_guide.md)
- Board, statuses, sprints, and carryover:
  [`all.github_projects_process.reference.md`](all.github_projects_process.reference.md)
- Sync-ups, morning TODO email, and communication:
  [`all.team_collaboration.how_to_guide.md`](all.team_collaboration.how_to_guide.md)
- Roles (tech lead, issue owner, reviewer) and blockers:
  [`all.organize_your_work.how_to_guide.md`](all.organize_your_work.how_to_guide.md)
- Weekly blocker meeting:
  [`all.scrum.explanation.md`](all.scrum.explanation.md#weekly-blocker-meeting)
- Feedback to contributors:
  [`all.contributor_feedback.how_to_guide.md`](all.contributor_feedback.how_to_guide.md)
