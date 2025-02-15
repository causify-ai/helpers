# Untitled

<!-- toc -->

- [General](#general)
  * [On-boarding issue](#on-boarding-issue)
  * [Create and Assign warm-up issue](#create-and-assign-warm-up-issue)
    + [Warm-up tasks](#warm-up-tasks)
  * [Score candidates](#score-candidates)
  * [Suggestions](#suggestions)
- [HiringMeister](#hiringmeister)
  * [Find candidates](#find-candidates)
  * [Initial screening](#initial-screening)
  * [Hiring committee](#hiring-committee)
  * [Mentors](#mentors)
  * [Onboarding pipeline](#onboarding-pipeline)
  * [Onboarding GH Issues](#onboarding-gh-issues)
  * [Feedback for interns](#feedback-for-interns)
  * [Feedback for full-timers](#feedback-for-full-timers)

<!-- tocstop -->

## General

- The HiringMeister is responsible for testing prospective candidates for
  full-time and part-time positions within our organization
- To see who is the HiringMeister now refer to
  [Rotation Meisters](https://docs.google.com/spreadsheets/d/1Ab6a3BVeLX1l1B3_A6rNY9pHRsofeoCw2ip2dkQ6SdA)
- The HiringMeister:
  - Ensures candidate evaluation through PR and pointing them to documentation
  - Maintains hiring standards
  - Fosters skill assessment through task assignments
  - Continuously improves the recruitment process

### On-boarding issue

- As the invitation to the repo are accepted by the selected candidates, create
  an `On-boarding` GitHub issue for each candidate
- The name of the issue must be `On-board <Candidate Name>` and assignee is the
  GitHub username of the candidate
- The contents of the issue are

  ```verbatim

  Please follow this checklist. Mark each item as done once completed.

  Post any errors you face in this issue.
  - [ ] Acknowledge the pledge to put time in the project [here](https://github.com/kaizen-ai/kaizenflow/blob/master/README.md#Important)
  - [ ] Read [How to organize your work](https://github.com/kaizen-ai/kaizenflow/blob/master/docs/work_organization/kaizenflow.organize_your_work.how_to_guide.md)
  - [ ] Read [Quick start for developing](https://github.com/kaizen-ai/kaizenflow/blob/master/docs/onboarding/kaizenflow.set_up_development_environment.how_to_guide.md)
  - [ ] Make sure the [Docker dev container](https://github.com/kaizen-ai/kaizenflow/blob/master/docs/work_tools/all.docker.how_to_guide.md) works
  - [ ] Make sure the [unit tests](https://github.com/kaizen-ai/kaizenflow/blob/master/docs/coding/all.write_unit_tests.how_to_guide.md) run successfully
  - [ ] Read [KaizenFlow Python coding style guide](https://github.com/kaizen-ai/kaizenflow/blob/master/docs/coding/all.coding_style.how_to_guide.md)
  - [ ] Fork, star, watch the KaizenFlow repo so that GitHub promotes our repo (we gotta work the system)
  - [ ] Learn about the [Morning Email](https://github.com/kaizen-ai/kaizenflow/blob/master/docs/work_organization/all.team_collaboration.how_to_guide.md#morning-email)
  - [ ] How to do a [review](https://github.com/kaizen-ai/kaizenflow/blob/master/docs/coding/all.submit_code_for_review.how_to_guide.md)
  - [ ] If you are graduating soon and you would like to get a full-time job in one of the companies in the KaizenFlow ecosystem reach out to GP at [gp@kaizen-tech.io](mailto:gp@kaizen-tech.io)
  - [ ] Get assigned a warm-up issue
  ```

- A reference issue is
  [On-boarding](https://github.com/kaizen-ai/kaizenflow/issues/437)
- Regularly check the updates made by the candidate and help resolving any
  errors faced by them

### Create and Assign warm-up issue

#### Warm-up tasks

- Collaborate with the team to identify potential warm-up tasks for candidates
  upon completion of their on-boarding process
- The goal of a warm-up issue is for someone to write a bit of code and show
  they can follow the process, the goal is not to check if they can solve a
  complex coding problem
- It should take 1-2 days to get it done
- This helps us understand if they can
  - Follow the process (or at least show that they read it and somehow
    internalized it)
  - Solve a trivial some problems
  - Write Python code
  - Interact on GitHub
  - Interact with the team
- Ensure that these warm-up tasks are straightforward to integrate, immediately
  beneficial, unrelated to new features, and do not rely on the `ck`
  infrastructure
- As candidates complete their on-boarding checklist, promptly assign them
  warm-up tasks from the predetermined list
- Write specs in a manner that is easily understandable by candidates, address
  any queries they may have regarding the task, and regularly follow up for
  updates
- If a candidate shows lack of progress on their assigned warm-up task, ping
  them twice for updates. If no progress is made, reassign the task to a more
  promising candidate
- Upon submission of a pull request by the candidate for the task, review it to
  ensure adherence to our processes. Provide constructive feedback on areas for
  improvement and ascertain if the task's objectives have been fully met
- Before merging the PR on `kaizenflow`, create a similar PR on `cmamp` and
  merge both of them together
- Assign more task to the candidate if required to make a final decision

### Score candidates

- Score the candidates every two weeks and notify all the team members for
  scoring
- Scoring criteria and template are defined in details in
  [this](/docs/work_organization/all.contributor_scoring.how_to_guide.md) doc
  - Not all the criteria are used for scoring the new candidates
  - E.g.
    [Scoring sheet](https://docs.google.com/spreadsheets/d/1eIzQnUZFiCAei4_vYnNWc_wDRfpSHgCdDmIeqnDm78Y)
- The scoring should be done by all of the members of the hiring team
- The final score of the candidate includes the average score of all the team
  members
- The final scored are delivered to the candidates every two weeks
- The candidate with low score should be dropped

### Suggestions

- In the first couple of weeks we should try to ingrain the following flow into
  a new team member’s mind
- Instead of spending hours coding on their own, apply the following steps:
  1. Identify a problem and describe it in the issue
  2. Design solution or seek guidance from a mentor
  3. Let mentor approve/comment and reach consensus on the solution
  4. Write code
- Stick to smaller PRs
  - It's very important to push frequently and ask for feedback early to avoid
    large refactoring

## HiringMeister

### Find candidates

We get candidates in several ways

- Send emails to CS and related depts
  - Especially for PhD students

- Use our LinkedIn pipeline to find candidates
  - We are going to start targeting graduates from top schools

- Post job on LinkedIn

- Post job on Upwork

### Initial screening

- HiringMeister: upon receipt of applications for new positions, track
  applicants add task to Asana "Candidates"
  - For each task description use the template
    https://app.asana.com/0/1204526145297526/1207748235019119/f

- HiringMeister: send email to gather additional information from candidates
  - Ask candidates to fill out the questionnaire form
    [here](https://docs.google.com/forms/d/1-iegytm5t1w-LPs7gm8IuUHTxi3cKI2iqzlPKdanWqY/edit#response=ACYDBNiZxM_bkXREaYEijJzedNrMRFiuzfuGgMQLE2W8qnzXnC1UcYAd8SbnXWHKAA)
  - Results are
    [here](https://docs.google.com/spreadsheets/d/13Mxj5ZIydMQHSmJUDCpURB5w-50RPXC0AjgKWYcMZnw/edit?resourcekey#gid=2038824432)

### Hiring committee

- Every 2 weeks the screening committee conducts a meeting to review the
  applicants
  - Everyone on the committee collects all the information needed to make a
    decision
  - TODO(gp): This needs to be formalized better

- We want to increase the quality of the collaborators, so if there is a red
  flag (e.g., no GitHub, low GPA, undergrad) we can decide to not on-board
  - The goal is to avoid on-boarding people that will likely disappoint us

- If we receive a single candidate application and find no red flags in the
  profile, we should proceed further in the process
  - It's ok to ask more team members to take a look

- If the candidate is a no-go, GP sends an email of rejection

### Mentors

- Hiring Meisters (e.g., Sonaal and Samarth) supervise the hiring process
  - [docs/onboarding/kaizenflow.hiring_meister.how_to_guide.md](https://github.com/kaizen-ai/kaizenflow/blob/master/docs/onboarding/kaizenflow.hiring_meister.how_to_guide.md)

- Coding mentors are:
  - Hiring Meisters
  - Anybody who is not in some critical path (e.g., Dan, Danya, Toma)

### Onboarding pipeline

- Once a candidate is accepted we assign a mentor on Asana
  - The mentor is in charge to intervene when the candidate is blocked
  - We track the mentor in Asana

- We use Asana tasks to communicate about the candidates

- There are multiple pipeline stages on Asana that candidates go through
  - **Candidates**
    - Anybody who wants to join our project/company
  - **On-boarding on KaizenAI**
    - _Goal_: set up candidates to work on their laptop on KaizenAI
    - _Duration_: few days
    - The checklist for onboarding on KaizenAI is
      [here](/docs/onboarding/kaizenflow.hiring_meister.how_to_guide.md#on-boarding-bug-creation)
    - Once the checklist is complete, candidates move to the next step
  - **Working on KaizenAI**
    - _Goal_: understand who can/should join the team
    - _Duration_: 1 month
    - _Type of tasks_: unit tests
    - Each candidate should work on 2-3 issues to make sure we can judge how
      good is a candidate
    - We score candidates every 2 weeks for a few iterations until we can make a
      decision
    - Candidates who are good enough can be onboarded on cmamp, otherwise are
      dropped
  - **On-boarding on cmamp**
    - _Goal_: set up candidates to develop on cmamp (only on the server)
    - _Duration_: few days
    - The checklist for onboarding on cmamp is
      [here](http://docs/onboarding/all.onboarding_checklist.md)
    - On-boarding GH issue on cmamp
  - **Working on cmamp**
    - _Goal_: learn our development process
    - _Duration_: 1 month
    - _Type of tasks_: unit tests (stuff that doesn’t require design)
    - After that we can assign the best hires to teams
  - **Full-time or interns on probation**
    - _Goal_: contribute to KaizenAI or cmamp
    - _Duration_: 3 months
    - _Type of tasks_: unit test, refactoring, simple non-design tasks
    - Assign them to teams
    - Give them more complex task
  - **Full-time team members**
    - Normal workflow
  - **Team leaders**
    - Type of tasks: in charge of architecture, big picture, real-time systems
    - For the ones that are able to master the process

### Onboarding GH Issues

We want to have a pipeline of GH Issues to assign people as soon as they are
ready

- [On-boarding issues](https://docs.google.com/document/d/1uuezdmcsV9TG2YwXGvEd0PBgWScCpR-QPOcySI5LPIA/edit#heading=h.vcvkivfud7be)

### Feedback for interns

The scoring process is described here

`docs/work_organization/all.contributor_scoring.how_to_guide.md`

[Internships - Feedback 2024](https://docs.google.com/spreadsheets/d/1FCuM3dPP3QZCT7iOHSKXls-maSZ0Mwj7BjsbaUq-T0Y/edit?gid=1816709202#gid=1816709202)

### Feedback for full-timers

[Performance feedback](https://docs.google.com/document/d/1wkG7c8LYhCnBINDRTpWcCLEQ5E9cW_A_bt4jr-Vxy64/edit#heading=h.16akje28vcjx)
