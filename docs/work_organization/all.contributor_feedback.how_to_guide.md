# Contributor Feedback

<!-- toc -->

- [Feedback principles](#feedback-principles)
- [Scoring metrics](#scoring-metrics)
  * [General](#general)
  * [Metrics for interns](#metrics-for-interns)
  * [Metrics for permanent team members](#metrics-for-permanent-team-members)
    + [Roles](#roles)
- [Scoring process](#scoring-process)

<!-- tocstop -->

## Feedback principles

- We want to evaluate and provide feedback to our contributors on different
  aspects of their work

- As a way to formalize giving feedback, we assign numerical scores on a variety
  of [metrics](#scoring-metrics)

- Each metric is scored between 1 (poor), 3 (average) and 5 (excellent)
  - We consider 4 as acceptable, anything less than 4 as problematic and needs
    to improve

- We don't take non-perfect scores personally but just as a way to understand
  what to improve

- Scoring is anonymous

- Everyone should be scored by at least 2 people

- Frequency:
  - Every 2 weeks for interns
  - Every month for permanent team members

## Scoring metrics

### General

- Metrics should be independent

- We should provide
  - Concrete questions to assess how people do on each metric
  - Ways to improve the score (e.g., "read this book!", "do more of this and
    less of that")

- Along with the numerical scores, there should be a possibility to add a
  textual note that can be used to provide rationale of the feedback and to
  suggest improvements

### Metrics for interns

- Sends good TODO emails
  - Doesn't forget to send one
  - Follows our
    [formatting requirements](/docs/work_organization/all.team_collaboration.how_to_guide.md#morning-todo-email)
  - Sets realistic ETAs
- Reads docs with attention
  - Internalizes our conventions described in the docs
- Able to follow procedures
  - Issue and PR-related workflows
  - Org processes
- Independence
  - Provides solutions rather than questions
  - Doesn't need a lot of guidance
  - Asks only "good" questions (not something that they should be able to solve
    on their own)
- Attention to detail
  - Doesn't forget to do small things, including but not limited to:
    - Follow style conventions
    - Apply fixes everywhere appropriate
    - Keep the branch up to date
    - Make sure there are no tmp files checked in
  - Thinks about corner cases while writing code and tests
- Git / GitHub knowledge
  - Doesn't run into problems with branches/PRs
- Python knowledge / coding ability
  - Writes effective and beautiful code
- Commitment to the project
  - Puts in the hours
    - This is a minor point: the number of hours doesn't really matter as long
      as stuff is done
    - On the other hand, if somebody consistently doesn't put enough time to get
      stuff done, it can become a problem
  - Willing to learn and contribute
  - Willing to solve problems
- Productivity
  - Quick to successfully complete tasks
- Learns from reviews
  - Doesn't repeat the same mistake twice

### Metrics for permanent team members

- Quality of code
  - Writes elegant code
  - Follows our standards and conventions
- Quality of design
  - Designs beautiful but simple abstractions
  - Adds abstractions only when needed
  - Orchestrates software components properly
  - Uses design patterns when needed
- Attention to details
  - Thinks in terms of corner cases
  - Debugs things carefully
  - Takes pride in a well-done product (e.g., code, documentation)
- Productivity
  - Closes issues effectively without unnecessary iterations
- Makes and achieves ETAs
  - Accurately estimates complexity of issues
  - Thinks of risks and unknown unknowns, best / average / worst ETAs
  - Resolves issues in set ETAs
  - Puts in a sufficient amount of hours to make progress
- Autonomy
  - Understands specs
  - Needs an acceptable level of supervision to execute the tasks
  - Does what's right according to our shared way of doing things without
    reminders
- Follows our PR process
  - Learns from reviews and doesn't make the same mistakes
  - Runs Linter consistently before each iteration
  - Does a PR / day (even a draft)
- Follows our organizational process
  - Sends a daily TODO email
  - Updates their issues regularly
  - Curates GitHub
- Team work
  - Helps others on the team when others need help / supervision
  - Takes the initiative and goes the extra mile when needed
  - Sacrifices for the greater good (e.g., doing stuff that is not fun to do)
- Communication
  - Files issues with clear specs
  - Explains technical issues and gives updates properly and with clarity
  - Reports problems and solutions with proper context
  - Speaks and writes English well
- Ability to run a team
  - Can juggle multiple topics at once
  - Can split the work in issues
  - Can provide clear and extensive specs
  - Is ok with being interrupted to help team members
- Positive energy
  - Has an upbeat approach to working even if sh\*t doesn't work (since things
    never work)
  - Isn't a
    [<span class="underline">Negative Nelly</span>](https://www.urbandictionary.com/define.php?term=negative%20nelly)
- Dev %, Data scientist %, Devops %
  - This measures how much of each [role](#roles) the team member can cover

#### Roles

- We want to determine how comfortable the team member is engaging in different
  types of activities
  - This is helpful to understand which roles a new hire can play

- Current roles:
  - Data science
    - Example of activities:
      - Write notebooks
      - Do research
      - Debug data
  - Dev
    - Example of activities:
      - Write code
      - Refactor code
      - Architecture code
      - Debug code
      - Unit test code
  - DevOps
    - Example of activities:
      - Manage / supervise infra
      - Airflow
      - Docker
      - AWS
      - Administer Linux

- E.g., X is a data scientist and has Data science=5, Dev=3, DevOps=1
- Roles are not mutually exclusive
  - A jack-of-all-trades can get a high score for all the roles

## Scoring process

- The process is organized and guided by
  - HiringMeister for interns
  - FeedbackMeister for permanent team members

- Scoring is done via a Google Form, which is distributed to the scorers in
  Asana

- Scores for each metric are averaged in a spreadsheet, which is then made
  available to people as feedback
  - If there are textual notes accompanying numerical scores, their summary is
    also provided

- Contributors receive an email which includes the feedback and a link to this
  doc to help interpret the metrics
