<!-- toc -->

- [General Rules of Collaboration](#general-rules-of-collaboration)
  * [Ask somebody if you have any doubts](#ask-somebody-if-you-have-any-doubts)
  * [Ping Team Leaders when you are out of tasks](#ping-team-leaders-when-you-are-out-of-tasks)
  * [Collaboration for problem solving](#collaboration-for-problem-solving)
  * [Collaboration](#collaboration)
    + [Why do we need to follow this handbook?](#why-do-we-need-to-follow-this-handbook)
      - [Learning from each other](#learning-from-each-other)
      - [Consistency and process](#consistency-and-process)
    + [Sync-ups](#sync-ups)
      - [Company town-hall meetings](#company-town-hall-meetings)
      - [Technical sync-ups](#technical-sync-ups)
      - [Ad-hoc meetings](#ad-hoc-meetings)
      - [Org emails](#org-emails)
      - [Synchronization point](#synchronization-point)
      - [Morning TODO email](#morning-todo-email)
    + [Communication](#communication)
      - [Use the right form of communication](#use-the-right-form-of-communication)
      - [DRY also applies to documentation](#dry-also-applies-to-documentation)
      - [Avoid write-once code and research](#avoid-write-once-code-and-research)
      - [Consistency](#consistency)
      - [Training period](#training-period)
      - [Go slowly to go faster](#go-slowly-to-go-faster)
    + [Vacations/OOTO time](#vacationsooto-time)
    + [Improve your English!](#improve-your-english)
      - [Study an English grammar book](#study-an-english-grammar-book)

<!-- tocstop -->

# General Rules of Collaboration

- We are not going to discuss and debate the rationale behind the following
  suggestions, but we assume that all is self-evident truth

## Ask somebody if you have any doubts

- If you have doubts on how to do something you want to do:
  - Look in the [documentation](/docs) and our Google drive folders
    [Process](https://drive.google.com/drive/u/1/folders/1aLNVB_Oiljf2ajkmpZuoX_TArpQdb6pG)
    and [Tech](https://drive.google.com/drive/u/1/folders/0AG6WMNtf7MVkUk9PVA)
  - Try Google search/ChatGPT
- If you still can't find the answer, ask your team members
  - Learn
    [how to ask questions](http://www.catb.org/~esr/faqs/smart-questions.html)
    first
  - Note that often people tell you his / her interpretation or their workaround
    for a problem, which might not be the best approach, so be careful and
    always think for yourself
  - Don't hesitate to ask anyone, including GP & Paul

## Ping Team Leaders when you are out of tasks

- When you're close to being out of tasks or all your ongoing PRs are waiting
  for review and are close to being merged, feel free to ping us in the IM and
  ask for more issues
  - IM = Telegram for interns / Slack for permanent team members
- In this way, Team Leaders can quickly assign you another issue, before you run
  out of work
- Everyone should have 2 issues to work on at the same time to avoid getting
  blocked on others

## Collaboration for problem solving

- Identify a problem and describe it in the issue
- Try your best to find a solution independently and outline the design in the
  issue
- If in doubt, seek guidance from a more experienced team member
- Communicate with the team and reach consensus on the solution
- NB:
  - Not every step requires explicit approval. In our team members, we value
    autonomy and ability to get things done
  - Keep our usual conventions and workflows in mind. For example, usually there
    is no need to ask "Do we need to add unit tests for this?" or "Do we also
    want this documented?" - the answer is almost always "YES", so just doing it
    saves time, shows proactivity and ability to follow processes

## Collaboration

### Why do we need to follow this handbook?

#### Learning from each other

- Proper research and software engineering practices allow us to:
  - Learn from each other
  - Accumulate and distill the wisdom of experts
  - Share lessons learned from our mistakes along the way

#### Consistency and process

- Consistency is a crucial enabler to make teams faster
- Productivity increases when team members "work in the same way", i.e., there
  is a single official way of performing a task, so that it's possible and easy
  to:
  - Re-use research and software components
  - Help each other in debugging issues
  - Add/transfer new people to teams
  - Work on multiple projects simultaneously
  - Learn from each other's experience and mistakes
  - Review each other's work looking for errors and improvements
  - ...

### Sync-ups

- We meet regularly every week and with different audiences to check on the
  progress of the projects we work on

#### Company town-hall meetings

- They usually happen on the first Monday of each month and have the following
  goals:
  - Summarize ongoing projects and their status
    - Share the achieved milestones
    - Discuss blocking tasks across projects
  - Discuss topics of general interest
    - E.g., organization, process
  - Talk about the team, hiring, customers

#### Technical sync-ups

- We meet one or two times per week for each of the projects (e.g., IM, WEB3)
- Please check your calendar to make sure the times work and the invited
  participants are correct
- The people running the day-to-day project should update the meeting agenda in
  the Gdoc
  - Try to do it one day before so that everybody knows ahead of time what we
    need to talk about and can come prepared
- Typically 2-3 issues are more than enough to fill one hour of discussion
  - Give priority to tasks that are controversial, blocking, or finished
  - No reason to linger on the successes or the easy stuff
- Send an email or tag a comment to Gdocs to broadcast the agenda
- It's ok to skip a meeting when the agenda is empty, or keep it short when
  there is not much to discuss
  - We don't have to fill one hour every time

#### Ad-hoc meetings

- Don't hesitate to ask for a quick meeting if you are unsure about:
  - What exactly needs to be done in a GitHub Issue
  - How to set-up something (e.g., environment, docker)
- Better safe than sorry

#### Org emails

- GP & Paul may send emails with the subject starting with "ORG:" pointing to
  interesting docs that are of general interest and relevance
- Please make sure to read the docs carefully and internalize what we suggest to
  do and, especially, the rationale of the proposed solutions
- It's ok to acknowledge the email replying to `eng@causify.ai`

#### Synchronization point

- We understand that most of the time everybody is head-down making progress on
  their tasks
  - This is great!
- However, sometimes we need synchronization:
  - We need to stop the progress for a bit when requested
  - Do an urgent task
  - Acknowledge that the task is done
  - Go back to pushing
- The procedure is:
  - One of us (e.g., GP or Paul) creates a GitHub task, with:
    - Detailed instructions
    - The list of all of the persons in charge of executing the task
  - Send a ping with the link on Slack if the task is urgent
  - Everybody does what's asked
  - Mark on the GitHub task your name

#### Morning TODO email

The idea is to send a morning TODO email to broadcast:

- Issues you will be working on
- Working hours
- Blocking issues/PRs

- E-mail template:
  ```
  To: eng@causify.ai

  Subject: TODO

  Hi all,

  Today I am going to work

  Hours:
  - ...

  Issues:
  - GitHub issue title and number with a hyperlink
     - ETA: YYYY-MM-DD
  - GitHub issue title and number with a hyperlink
     - Original ETA: YYYY-MM-DD
     - ETA: YYYY-MM-DD
     - Reason for ETA update: ...
     - Blocked on: ... (ok to omit if not blocked)
  ```

- Good example:
  ```
  To: eng@causify.ai

  Subject: TODO

  Hi all,

  Today I am going to work

  Hours:
  - 8

  Issues:
  - Create matching service #261
      - ETA: today (2023-05-25)
      - Original ETA: yesterday (2023-05-24)
      - Reason for ETA update: it was more complex than what we thought
      - Blocked on: PR review from Grisha
  - Create linear supply/demand curves #177
      - ETA: tomorrow (2023-05-26)
  - Unit test `compute_share_prices_and_slippage()` #8482
      - ETA: 2024-06-19
  ```

- Bad example:
  ```
  To: eng@causify.ai

  Subject: to-do

  Hi all,

  Today I am going to work 2-6 hours.
  - Calls
  - PR reviews
  - Finish the trading report analysis
  ```

- The goal is:
  - Think about what you are going to work on for the day, so you have a clear
    plan
  - Let Team Leaders know that you're going to work today and what is your
    workload
  - Make sure people blocked on your tasks know that / whether you are working
    on those tasks
  - Broadcast if you are blocked or if you don't have tasks
  - A TODO email replaces stand-up meetings
- When to send an email:
  - Within the first hour of beginning the day
    - There is no hard deadline, given that we have people working from
      different time zones. Doing it first thing in the morning ensures one
      doesn't forget
  - It is recommended to check the inbox (email, GitHub) first to reflect all
    the update in the plan for the day
- Send an email to:
  - For permanent team members/people on a 3-month trial: `eng@causify.ai`
  - For interns or collaborators: `contributors@causify.ai`
- Email subject:
  - `TODO` (all caps)
  - It makes it easier to filter emails by subject
- Reply to your previous TODO email so that at least last week of TODOs is
  included
- Specify how many hours are you going to work today
  - On Monday we also specify an estimation for a week
  - No need to be too specific, give just an approximation
- List all the tasks you're going to work during the day in priority order
  - Add a hyperlink to the corresponding GitHub issue to each task in order to
    ease the navigation <img width="381" src="https://github.com/sorrentum/sorrentum/assets/31514660/0d2fbba4-1e6c-4c39-9c04-7ffc4acdde81">
  - For each task provide an ETA
    - You always estimate the ETA yourself, based on the task's difficulty,
      priority and your workload
    - No reason to be optimistic: complex things take time to be done correctly
    - Use a date in the YYYY-MM-DD format, e.g. 2023-05-20
    - When possible, add "today", "yesterday", "tomorrow", "end of week" so that
      it's easier to parse
      - "End of week" generally means Friday, although it can be extended if you
        are planning to work on the weekend (provide the date to clarify)
      - If nothing is applicable, it's okay to just provide the date
    - If the originally set ETA has not been changed yet, omit "Original ETA"
      and "Reason for ETA update"
    - If your original ETA needs to be updated (e.g., you thought that you would
      have finished a task by yesterday, but it's taking longer), keep the older
      ETA (as "Original ETA") and add the new one (as "ETA")
- Report the PR/issue blocked

### Communication

#### Use the right form of communication

- GitHub
  - This is a major form of communication about technical details, so if you
    have any questions about any particular issue or PR, discuss it there first,
    e.g.:
    - Clarify issue specs
    - Ask for help with debugging
    - PR reviews
- Asana
  - Is concerned with all the non-technical issues in general, e.g.:
    - Work organization tasks
    - Marketing and funding
    - On-boarding process
- Slack
  - This is our messenger for tight interaction (like a debug session) or
    immediacy (e.g., "are you ready for the sync up?")
  - Please, avoid discussing anything that can be discussed at GitHub or Asana
    - You often need to reference some comments and ideas in other places like
      issues or messages and it is impossible to reference a Slack message
      outside of it
    - It is much easier for all reviewers to catch up with all the thinking
      process if it is logged at one place - Slack is never a place for this
- Jupyter notebooks
  - Generally used to implement and describe research in detail
    - `Master` notebooks are intended to be used as tools for demonstrative
      analysis with visible stats and plots
- Markdown files
  - Document instructions, process, design closely related to code
  - Notes that need to be close to the code itself
  - Documents that need to be authoritative and long-term (e.g., reviewed,
    tracked carefully)
- Google docs
  - Document research in a descriptive way
  - Explain what are the results independently on how they were reached
- Emails
  - `TODO`s primarily
  - Rarely used for any other purpose
  - Exceptions are to send non-urgent information to everybody
- There should be little replication among these forms of documentation
  - It's not ok to file a bug and then ping on Slack unless it's urgent

#### DRY also applies to documentation

- [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)! Do not Repeat
  Yourself
- E.g., it's not a good idea to cut & paste pieces of Gdocs in a GitHub bug,
  rather just point to the relevant session on Gdocs from the GitHub bug

#### Avoid write-once code and research

- Code and research is:
  - Written once by a few people
  - Read many times by many people
- Therefore it is essential to invest in the process of writing it heavily

#### Consistency

- Coding/research across our group is done with consistent procedures, code
  layout, and naming conventions

#### Training period

- When you start working with us, you need to go through a period of training in
  following the procedures and conventions described in this handbook
- We understand that this is a painful process for you:
  - You need to change your old habits for new habits that you might disagree
    with, or not comprehend
  - You need to rework your code/notebooks that are already correctly working
    until it adheres to the new conventions
- Understand that this is also a painful process for the reviewers:
  - On top of their usual workload, they need to:
    - Invest time to explain to you how we do things
    - Answer your questions
    - Try to convey the sense of why these procedures are important
- In a few words, nobody _enjoys_ this process, and yet it is necessary,
  mandatory, and even beneficial
- The process acquaintance can take several days if you are open and patient,
  but months if you resist or treat it as an afterthought
  - Our suggestion is to accept these rules as the existence of gravity

#### Go slowly to go faster

- Once you reach proficiency, you will be moving much faster and make up for the
  invested time
  - In fact, everyone will be much quicker, because everyone will be able to
    look at any part of the codebase or any notebook and get oriented quickly

### Vacations/OOTO time

- We use
  [vacation calendar](https://calendar.google.com/calendar/u/0?cid=Y19kYWRlOGU0NTUwMzhiMDllMmUzNDk1OWM2YzFkYWNhYTVmMTAzYjdjZmNiODQ1MDkzOWZhMTBkZDY2NWI3ZjJhQGdyb3VwLmNhbGVuZGFyLmdvb2dsZS5jb20)
  to announce time off
- If you are a part of _@all_ mailing group you should be able to access this
  calendar with your company email
- Create an event in it, whenever you have planned time off in order to let your
  colleagues know in advance

### Improve your English!

- Make sure you have English checker in all your tools:
  - Pycharm: you can use
    [this](https://plugins.jetbrains.com/plugin/12175-grazie) plugin
  - Vim: `set spell`
  - Google docs: Grammarly
  - GitHub and web: Grammarly
  - Email client: TBD
- These tools are going to help you improve since you can see the mistake as you
  go
- Feel free to use [Google Translate](https://translate.google.com/) when you
  are not sure about a word or a phrase
- What's the point of doing an excellent job if you can't communicate it?

#### Study an English grammar book

- I used
  [this](https://www.amazon.com/English-Grammar-Use-Self-study-Intermediate/dp/0521189063/ref=sr_1_3?ie=UTF8&qid=1536765989&sr=8-3&keywords=English+Grammar+in+Use)
  when I learned English (late in life at 25 starting from
  no-English-whatsoever, so you can do it too)
