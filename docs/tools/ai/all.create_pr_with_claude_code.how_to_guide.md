# How to Create a PR With Claude Code

- A PR (pull request) asks to add your changes to the shared code
  - A reviewer checks it before it is merged
- Claude Code is an AI assistant that reads and writes code with you
- These are the steps, in order, from picking a task to a PR of the expected
  quality
  - Each step links to the doc with the details
- The steps are the same for any repo
  - Rules specific to one repo (e.g., who reviews, branch prefix, fork flow) live
    in the docs of that repo
- To delegate a whole task list to agents, see
  [`all.auto_task.how_to_guide.md`](all.auto_task.how_to_guide.md)

## 1. Get Ready

- Do the onboarding checklist that the project lead posts in the main issue of
  your project:
  - Read the paper or the design doc
  - Read the code in the project dir
  - Run the project's Docker container and learn how the project is built and run
  - Read the Claude Code rules for code and notebooks: `.claude/skills/coding*`
    and `.claude/skills/notebook.*`
  - Read all the markdown files in the project dir
- Read the
  [must-read docs](../../onboarding/all.dev_must_read_checklist.reference.md)
- Read the AI policy of the repo, if there is one
  - Why: you must be able to explain every line you submit, and no AI slop

## 2. Pick a Task

- Take a task from the master plan of the project (the file with the goals and
  the tasks) that has a GitHub issue (a task page on GitHub)
  - Why: we only work on tasks that are on the plan and in GitHub
  - See
    [Create an End-to-End Plan](../../planning/all.plan_work.how_to_guide.md#create-an-end-to-end-plan)
- Post in the issue when you expect to finish (ETA), and update it if it changes
  - See
    [Sync-ups](../../work_organization/all.team_collaboration.how_to_guide.md#sync-ups)
- Post a short update in the issue every 2-3 days: done, next, blockers

## 3. Investigate Before Changing Anything

- Read the issue, its comments, and the code the task touches; change nothing yet
- Write down which files and functions the task affects, and any problem you find
- Ask in the issue if anything is unclear
  - Why: a wrong guess costs more time than a question

## 4. Create a Branch in a Worktree

- A branch is your own line of changes, separate from `master` (the shared
  version)
- Name it after the issue, see
  [Workflow](../git/all.git.how_to_guide.md#workflow)
  - E.g., `HelpersTask123_Short_title`
- Create it in a worktree: a second dir of the repo, on your branch
  - See
    [Work in a Worktree](../git/all.git.how_to_guide.md#work-in-a-worktree)
  - Why: your main dir stays as it is, e.g., for running Jupyter
- If you are not a collaborator on the repo, use the fork steps in the docs of
  that repo

## 5. Work in Small Steps

- Split the task into small steps; finish and test each one before the next
  - Why: small steps are easy to test, to explain, and to review
  - See
    [Stick to Smaller PRs](../../coding/all.submit_code_for_review.how_to_guide.md#stick-to-smaller-prs)
- Make one commit per step: a commit saves a step with a short message
  - Add only the files of that step (`git add <file>`), never `git add .`
  - Say what changed and give the issue, see
    [Write Helpful Commit Messages](../git/all.git.how_to_guide.md#write-helpful-commit-messages)

## 6. Follow the Rules for Each File Type

- `.claude/rules.md` maps each type of file to its rules and templates
  - Claude Code follows them, and so do you
  - See [Rules](all.ai_workflows.how_to_guide.md#rules)
- Skills are saved instructions for common jobs, run in Claude Code as
  `/<name>`, e.g.:
  - `/notebook.refactor_to_utils`: move notebook code into the `_utils.py` file
  - `/testing.write_unit_tests`: plan and write the unit tests for a file
  - See [Coding Workflows](all.ai_workflows.how_to_guide.md#coding-workflows) and
    [Notebook Workflows](all.ai_workflows.how_to_guide.md#notebook-workflows)

## 7. Understand Every Line

- Keep notes in plain words as you go: what each function does, and why you made
  each choice
  - Keep them in a personal file that you do not commit
- Treat what Claude Code writes as a first draft: read it, question it, and
  rewrite it
  - See
    [Edit Code/Text Written by AI](../../coding/all.submit_code_for_review.how_to_guide.md#edit-codetext-written-by-ai)
  - Why: a reviewer may ask about any line, and you must answer

## 8. Test in Layers

- Go from the fastest check to the most thorough one, inside the project's Docker
  container
  - See
    [Test in Layers](../../coding/all.submit_code_for_review.how_to_guide.md#test-in-layers)
- Write down the pass and fail counts before and after your change, for the PR

## 9. Open the PR

- Push your branch (upload your commits) with a normal push; never force push,
  and never push to `master`
  ```bash
  > git push -u origin <BRANCH>
  ```
- Title: the branch name
- First line of the description: `Closes #<issue>` if the PR completes the issue,
  otherwise `Related to #<issue>`
  - See
    [Filing Process](../../work_organization/all.use_github.how_to_guide.md#filing-process)
- Fill in the PR description template
  `.claude/templates/github_PR_description.template.md`
  - `/github.find_name_for_pr` writes a draft in `pr_description.md`
  - See
    [PR Description Template](../../planning/all.plan_work.how_to_guide.md#pr-description-template)
- Put yourself in the "Assignees" field, add the reviewers, and add the label
  - See
    [Filing a New PR](../../work_organization/all.use_github.how_to_guide.md#filing-a-new-pr)
- Get the PR ready to merge with `/github.get_pr_ready_to_merge`
  - It runs the linters, the local tests, and the GitHub checks, and fixes what fails
  - Run `/github.get_pr_to_pass_local_tests` or `/github.get_pr_to_pass_ci_tests`
    to fix only the local tests or only the CI checks
- GitHub runs automatic checks on each PR
  - If one fails, find out whether your change caused it and say so in the PR
  - See
    [Make Sure Checks Are Green](../../coding/all.submit_code_for_review.how_to_guide.md#make-sure-checks-are-green)

## 10. After the PR

- In the issue checklists, tick each finished item with a short link to the
  result, e.g., `- [x] Update the master plan: PR #123`
- Update the project's log (the list of what was done), the task list in the
  master plan, and the paper when the work changes them
  - See
    [Keep Docs in Sync](../../planning/all.plan_work.how_to_guide.md#keep-docs-in-sync)
- Answer review comments with new commits on the same branch
  - See
    [Addressing a Comment](../../work_organization/all.use_github.how_to_guide.md#addressing-a-comment)
- When the PR is merged, remove the worktree
  - The branch is not deleted
  - See
    [Work in a Worktree](../git/all.git.how_to_guide.md#work-in-a-worktree)

## Resources

- Plan, loop, log, and PR description:
  [`all.plan_work.how_to_guide.md`](../../planning/all.plan_work.how_to_guide.md)
- Skills, rules, and templates:
  [`all.ai_workflows.how_to_guide.md`](all.ai_workflows.how_to_guide.md)
- Before opening a PR:
  [`all.submit_code_for_review.how_to_guide.md`](../../coding/all.submit_code_for_review.how_to_guide.md)
- Issues, PRs, labels, and review:
  [`all.use_github.how_to_guide.md`](../../work_organization/all.use_github.how_to_guide.md)
- Git branches, worktrees, and commit messages:
  [`all.git.how_to_guide.md`](../git/all.git.how_to_guide.md)
- Delegate a task list to agents:
  [`all.auto_task.how_to_guide.md`](all.auto_task.how_to_guide.md)
