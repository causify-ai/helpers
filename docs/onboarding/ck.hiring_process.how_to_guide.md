# Hiring process

<!-- toc -->

- [Hiring stages](#hiring-stages)
- [HiringMeister](#hiringmeister)
- [Step by step](#step-by-step)
- [Warm-up tasks](#warm-up-tasks)
- [Intern scoring](#intern-scoring)

<!-- tocstop -->

## Hiring stages

- We separate the hiring process into the following stages:
- **Intern**
  - Not a part of the company
  - Paid, but not through the company payroll
  - Interns only have access to public repos (e.g., `helpers`, `tutorials`)
  - Can be full-time or part-time
    - Since most are students, during summer they can work full-time
    - In any case we expect at least 20 hrs/week
  - Interns go through
    ["light" on-boarding](/docs/onboarding/intern.onboarding_checklist.reference.md)
    - Read the "must-read" docs about how we do things
    - Set up for development on their laptops
  - Interns get [simple tasks](#warm-up-tasks) to work on, so that we can assess
    how well they can follow directions and work independently
    - The tasks would be most likely related to Linter, documentation, AI, DS
    - How to test potential hires to the Infra team? We decide case by case
  - Ideal goal: minimal effort for us to give a chance to somebody, high
    probability of failing
  - Interns are managed only by the hiring team without any input from team
    leaders
  - Interns receive feedback on various skills every 2 weeks (see more
    [below](#intern-scoring))
  - After 1-2 months (or whenever we feel we have enough information to make an
    informed decision), we decide whether the intern can move on to the
    following stage of the hiring pipeline
- **3-month trial**
  - Before an intern can turn into a permanent team member, they go through a
    3-month trial period
  - At this stage, they work full-time and have all the markings of a Causify
    team member
  - They go through
    [full on-boarding](/docs/onboarding/all.onboarding_checklist.reference.md),
    receiving company e-mail, server access, access to private repos, etc.
  - They receive feedback on various skills every month to make sure they are
    adapting and improving in the way we expect
  - After 3 months, we make a decision whether to make an offer or not
    - The probability of failing at this stage should be low
  - This stage is run by the hiring team with some input from team leaders
  - During this stage, we decide which team they go on: Infra, Dev, DS, AI
- **Permanent team member**
  - Successful candidates receive an offer for a permanent full-time position
    after the 3-month trial
  - At this point they should already be fully on-boarded and ready to hit the
    ground running
  - They get assigned to a particular team/project and start being managed by
    the corresponding team leader
  - For now, we don't consider hiring new people to part-time positions since
    it's too difficult to plan their involvement in projects

## HiringMeister

- Members of the hiring team alternate being the HiringMeister for 2 weeks
- To see who is the HiringMeister now, refer to
  [Rotation Meisters](https://docs.google.com/spreadsheets/d/1Ab6a3BVeLX1l1B3_A6rNY9pHRsofeoCw2ip2dkQ6SdA)
- HiringMeister's duties include:
  - Organizing the hiring and onboarding process (see [below](#step-by-step) for
    more details)
  - Communicating with applicants by email
  - Supervising interns and people on a 3-month trial period
  - Keeping all the relevant documentation up-to-date
  - Improving the process when needed
  - Managing the hiring project on Asana
- In other words, HiringMeister is the first point of contact for triaging,
  making sure nothing falls through the cracks

## Step by step

- We look for candidates based on the specific hiring needs in our
  teams/projects. There are several avenues:
  - Emails to CS and related depts
    - Especially for PhD students
  - Using our LinkedIn pipeline
    - We are going to start targeting graduates from top schools
  - Job postings on LinkedIn
  - Job postings on Upwork

- HiringMeister: upon receipt of a new application, create a task on Asana in
  the
  [Hiring](https://app.asana.com/1/1208196877870190/project/1208280136292379/list/1208280159230261)
  project
  - The task goes in the "Candidates" group
  - The name of the task is the name of the applicant
  - In the task description, use the following template:

    ```verbatim
    Pronoun:
    Personal email:
    Work status (e.g., when graduates):

    Hiring info:
      Google Form:
      CV:
      LinkedIn:
      GitHub user:
      TG:
      Working hours / week:
      Best piece of code:
      How good (1-5):
    ```
  - We use this Asana task to communicate about the applicant

- HiringMeister: send an email to the applicant with a link to the
  [questionnaire](https://docs.google.com/forms/d/e/1FAIpQLScWAavYiYj1IfWGP1QEv2jqjKvQKnFjseryhzmIIHZKnZ4HkA/viewform)
  to gather information about them
  - Responses are available
    [here](https://docs.google.com/forms/d/1NUsjbTyXBoITQZ6z8nqmTydFPcWl0kWEQZJZzzYXUeM/edit#responses)
  - Use their responses to update the corresponding Asana task description

- Hiring team: decide whether we take on the applicant as an **intern**
  - Decided at a review meeting that takes place every 2 weeks
  - We want to increase the quality of the collaborators, so if there is a red
    flag (e.g., no GitHub, low GPA, undergrad) we can decide not to offer the
    internship
  - The goal is to avoid onboarding people that will likely disappoint us
  - If we receive a single candidate application and find no red flags in the
    profile, we should proceed further in the process
  - It's ok to ask more team members to take a look
  - If the candidate is a no-go, GP sends an email of rejection

- HiringMeister: create a GitHub issue for onboarding the intern
  - Follow the instructions in
    [`intern.onboarding_checklist.reference.md`](/docs/onboarding/intern.onboarding_checklist.reference.md)

- HiringMeister: regularly check the updates made by the intern in the
  onboarding issue and help resolve any errors they face
  - This "light" onboarding process should take 2-3 days max
  - The goal is to make sure that all the mechanisms for developing are tested
    and working, so that we can focus on the next stages ("can the intern fix a
    simple bug?", "can the intern write more complex code?", etc.)

- HiringMeister: once the onboarding is complete, assign a
  [warm-up issue](#warm-up-tasks) to the intern
  - If an intern shows lack of progress on their assigned warm-up task, ping
    them twice for updates. If no progress is made, reassign the task to a more
    promising intern
  - Once the intern submits a pull request, review it to ensure adherence to our
    processes. Provide constructive feedback on areas for improvement and
    ascertain if the task's objectives have been fully met
  - If the task is completed, assign a new one

- Hiring team: after 1 month, decide whether we should continue to collaborate
  with the intern or not

- HiringMeister: when the intern moves on to the **3-month trial period**,
  create a GitHub issue for further onboarding
  - Follow the instructions in
    [`all.onboarding_checklist.reference.md`](/docs/onboarding/all.onboarding_checklist.reference.md)

- HiringMeister: once the full onboarding is complete, organize more complex
  tasks to test their development and problem-solving skills
  - This is done together with team leaders

- Hiring team: after 3 months, decide whether we want to offer a permanent
  position on the team
  - If the offer is made, decide which team/project the new team member is
    joining, based on their background, skills, performance during internship
    and 3-month trial, and, last but not least, company needs

## Warm-up tasks

- The HiringMeister should collaborate with the team to identify potential
  warm-up tasks to give to the interns upon completion of their onboarding
  process
- The goal of a warm-up issue is to write a bit of code and show they can follow
  the process, the goal is not to check if they can solve a complex coding
  problem
- It should take 1-2 days to get it done
- This helps us understand if they can
  - Follow the process (or at least show that they have read the docs and
    somehow internalized them)
  - Solve some trivial problems
  - Write Python code
  - Interact on GitHub
  - Communicate with the team
- The warm-up tasks should be straightforward to integrate, immediately
  beneficial, unrelated to new features, and should not rely on the code in
  private repos
- It is important that specs are provided in a manner that is easy to be
  understood by interns, and any queries they may have regarding the task are
  addressed quickly by the HiringMeister or another permanent team member
- Warm-up tasks are collected in advance:
  - Issues marked with the "good first issue" label on GH
    - Extremely simple (e.g., changing a few lines of code, converting Gdoc to
      Markdown...)
    - The goal is to practice following our procedure
  - Issues marked with the "good second issue" label on GH
    - Still simple but require a little bit more coding than the first issue
    - The goal is to start testing the skills as well as confirm the
      understanding of our process
  - [Outsourceable issues gdoc](https://docs.google.com/document/d/1uuezdmcsV9TG2YwXGvEd0PBgWScCpR-QPOcySI5LPIA/edit#heading=h.vcvkivfud7be)

## Intern scoring

- The interns are scored every 2 weeks
- Scoring criteria and template are defined in detail in
  [`all.contributor_scoring.how_to_guide.md`](/docs/work_organization/all.contributor_scoring.how_to_guide.md)
  - Not all the criteria are used for scoring the interns
  - See, e.g.,
    [Scoring sheet](https://docs.google.com/spreadsheets/d/1eIzQnUZFiCAei4_vYnNWc_wDRfpSHgCdDmIeqnDm78Y),
    [Internships - Feedback 2024](https://docs.google.com/spreadsheets/d/1FCuM3dPP3QZCT7iOHSKXls-maSZ0Mwj7BjsbaUq-T0Y/edit?gid=1816709202#gid=1816709202)
  - See also the guidelines for the
    [performance feedback for full-time team members](https://docs.google.com/document/d/1wkG7c8LYhCnBINDRTpWcCLEQ5E9cW_A_bt4jr-Vxy64/edit#heading=h.16akje28vcjx),
    for what is generally expected of our employees
- The scoring should be done by all members of the hiring team
- The final score of the intern is the average score of all the team members
- The final scores are delivered to the interns every 2 weeks
- Interns with a low score should be let go
