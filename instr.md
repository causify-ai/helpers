Fix the code in git_branch_create so that when running
i git_branch_create -b gp_scratch_32

before 
gh pr create --repo github.com/causify-ai/helpers --draft --title "gp_scratch_32" --body ""

do a fake commit 
git commit --allow-empty -m "Draft PR"

to avoid


Creating draft pull request for gp_scratch_32 into master in causify-ai/helpers

pull request create failed: GraphQL: No commits between master and gp_scratch_32 (createPullRequest)

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Create a `plan.md` in the same directory with 5 bullet points explaining what
    the plan is
  - Wait for the user to confirm

