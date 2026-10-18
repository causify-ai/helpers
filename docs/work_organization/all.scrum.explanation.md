# Refs

- From "Lacey, The Scrum Field Guide: Practical Advice for Your First Year,
  2012"

# Roles

## Goal of Scrum methodology

- Work in the interests of customers and stakeholders to turn the vision into a
  working product

## Metaphor for the roles in terms of a race car

- ProductOwner = driver

- DevTeam = engine

- ScrumMaster = lubricants and sensors

## ScrumMaster

- Identify when the team is not performing to its ability

- Assist in correcting the issues

- Notice non-verbal cues

- Is comfortable with conflict

- Can build trust and earn respect

## ProductOwner

- Represent the customers

- Point the car in the correct direction

- Adjust the car direction to stay on course

- Make decisions about official release

- Ultimately he is responsible for success or failure of the projects

- Decide:
  - What is developed
  - When it is developed
  - Whether the product meets expectations

## DevTeam

- Aka Team, Development team, Core team

- Developers, testers, architects, designers
  - Cross-functionality is a good thing

- The ideal team size is 6 plus / minus 2

# Artifacts

## Product backlog

- = master list of all features and functionalities needed to implement the
  vision into the product

- The ProductOwner keeps the backlog:
  - Prioritized
  - Up to date
  - Clear

- The backlog is never complete:
  - Items are added and removed
  - Reordered based on priority, value, or risk

## Product backlog items

- Aka PBI

- E.g., bugs, features, enhancements, non-functional requirements

## Complexity of PBI

- ProductOwner and the DevTeam estimate the size of each task

- The complexity of each task can be expressed in different ways:
  - Points
  - T-shirt size (S, M, L, XL)

## High-priority vs lower-priority tasks

- High-priority stories should be small and clear
  - So they can be brought into the sprint

- Lower-priority items can be large and fuzzy
  - Bigger stories are decomposed into smaller chunks

## Sprint backlog

- = output of the planning meeting

- List of tasks that need to complete during the sprint

- Sprint backlog tasks have an estimate in hours

- The DevTeam keeps the sprint backlog up to date

- During a sprint
  - New tasks are discovered
  - Tasks are adjusted (in terms of description or estimated hours)
  - Tasks are marked as done

## The burndown

- Communicate how much work is remaining and what is the team velocity

- It is updated at the end of each day

- Plot the number of hours remaining (y-axis) against the number of days
  remaining (x-axis)

# The meetings

## Planning meeting

- Each sprint begins with a sprint planning attended by the team, ScrumMaster,
  ProductOwner
  - Typically one needs two hours per number of weeks to plan the sprint
  - For a 1-month sprint, 8 hours of meeting
  - For 2-week sprint, 4 hours of meeting

## Part one of sprint planning meeting

- Review of potential product backlog items for the sprint

- ProductOwner describes what the goal of the meeting is

- DevTeam asks questions to drive away ambiguity

- Outcome is one-sentence description of the desired outcome of the sprint

## Part two of sprint planning meeting

- Many DevTeams discuss how to implement the tasks

- The ProductOwner doesn't need to be present

- The ScrumMaster can be present facilitating the process

- The DevTeam discusses and decides the implementation of the tasks

- Decompose backlog items into work tasks

- Estimate tasks in terms of hours

## Daily scrum

- Aka daily stand-up

- Give the DevTeam the opportunity to sync daily, at the same time, and at the
  same place

## Daily scrum: questions

- The 3 most frequent questions are:
  - What have you accomplished since the last meeting?
  - What will you accomplish today?
  - What obstacles are in your way?

## What the daily scrum is not

- The daily scrum is not a deep-dive problem-solving meeting
  - Any other issues need to be taken offline

- It is not a status report meeting to the ScrumMaster
  - The purpose is for the DevTeam members to talk to each other

- The ProductOwner is in "listen-only" mode

## Sprint review

- On the last day of the sprint, the DevTeam holds a sprint review

- Everybody should join
  - ScrumMaster
  - ProductOwner
  - DevTeam
  - Customers, key stakeholders
  - Executives

- DevTeam
  - Recaps the goal of the sprint
  - Presents the work done

- Customers
  - Review the progress made on the project
  - Accept changes
  - Ask for changes

## Sprint retrospective

- After the sprint review, the retrospective is a way to identify how to improve
  process and execution

## Sprint retrospective: questions

- What went well during the sprint?

- What could be improved in the next sprint?

# Lightweight weekly sprint

## Purpose

- Small teams can use a lightweight workflow informed by Scrum
  - It keeps the short feedback cycles to show observable progress
  - It does not require every formal Scrum event
  - It does not create additional mandatory meetings
- For the framework itself, see the
  [official Scrum Guide](https://scrumguides.org/scrum-guide.html)

## Cadence

- Each sprint is one week long
  - The project picks the first day of the sprint, see
    [Project-specific cadence](/docs/work_organization/all.github_projects_process.reference.md#project-specific-cadence)
  - The last day of the sprint closes the sprint
- The team meets once a week to check blockers, review the previous sprint, and
  coordinate the new one
- The project docs state the time, the timezone, the URL, and the facilitator of
  the meeting

## Goals and backlog

- **Product goal**: The outcome the team is working toward
- **Backlog**: Scoped work on the board that is not yet complete
  - Keep near-term work specific
  - Split large tasks into reviewable deliverables
- **Sprint goal**: One clear outcome for the week
  - E.g., "Run the nightly backtest end to end"
- **Sprint work**: Issues selected to support the sprint goal
  - Each issue has an owner, acceptance criteria, and an effort estimate in
    hours when useful
- Plan against the actual availability of the team
- Revisit the scope when urgent work or new findings affect the capacity
  - Record what was added and what was displaced

## Weekly blocker meeting

- Before the meeting
  - Update the assigned issues with progress, evidence, remaining work,
    blockers, and PRs awaiting review
  - Review the completed work against the sprint goal
  - Prepare the weekly summary, see
    [Lean weekly summary](/docs/work_organization/all.github_projects_process.reference.md#lean-weekly-summary)

- Agenda
  1. Inspect the delivered results and the unfinished work of the previous
     sprint
     - Discuss the evidence or show a short demo when it helps
  2. Review each blocked issue: cause, impact, and help or decision needed
  3. Give each unblock action an owner and a follow-up date
  4. Agree on the new sprint goal, the issues, the owners, and the realistic
     capacity
     - Decide the carryover explicitly
  5. Record the decisions, links, and next actions in the weekly summary
     - Record one process improvement if needed

- Rules
  - Raise a blocker immediately in the issue, do not wait for the meeting
  - Move lengthy technical problem solving to a separate discussion with the
    people needed
  - The meeting coordinates work, it is not a report of percentages complete

## Between meetings

- Leave a short asynchronous issue update on the days you work
  - What changed
  - What comes next
  - What blocks progress
- A daily stand-up and an hour-based burndown chart are not required
  - The team can add them if they solve a real coordination problem

## Definition of Done

- An issue is Done when:
  - Its acceptance criteria are met
  - The evidence is available
  - The required checks and the review are complete
  - Any required PR is merged
- Research-only work has an accessible result and an agreed review
- Insufficient evidence or an outstanding review means the work is unfinished
  - Record the incomplete work honestly at the end of the sprint
  - Decide at the weekly meeting whether to carry it forward

## Responsibilities

- The project maintainer coordinates priorities and acceptance
- The issue owners deliver and update the work
- The reviewers evaluate the work
- The facilitator runs the weekly discussion
- See
  [all.organize_your_work.how_to_guide.md](/docs/work_organization/all.organize_your_work.how_to_guide.md#roles)
- Confirm the named owners with the team, do not import roles from another
  organization
