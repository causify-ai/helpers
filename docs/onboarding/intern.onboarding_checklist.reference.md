<!-- toc -->

- [Intern onboarding checklist](#intern-onboarding-checklist)
  * [Intern onboarding vs. full onboarding](#intern-onboarding-vs-full-onboarding)
  * [Checklist](#checklist)
    + [Org](#org)
    + [IT setup](#it-setup)
    + [Must-read](#must-read)
    + [Final checks](#final-checks)

<!-- tocstop -->

# Intern onboarding checklist

## Intern onboarding vs. full onboarding

- The onboarding process documented here is intended for people who have not
  become permanent members of the team yet, i.e., interns
- Upon completing this onboarding, the intern will be able to develop in our
  common environment, open GitHub issues and PRs, use our extensive coding
  toolchain
- However, some of the steps of the
  [_full_ onboarding process](/docs/onboarding/all.onboarding_checklist.reference.md)
  (like creating a company email) are postponed until the intern "graduates" to
  a permanent position

## Checklist

- Source:
  [`intern.onboarding_checklist.reference.md`](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/intern.onboarding_checklist.reference.md)

### Org

- [ ] **HiringMeister**: File an issue with this checklist
  - The title is "Onboarding {{Name}}"
  - Copy-and-paste the whole checklist starting from [here](#checklist)
  - The issue should be assigned to the intern

- [ ] **Intern**: Join the Telegram channel -
      [https://t.me/+DXZXsWoEHR1mNWIx](https://t.me/+DXZXsWoEHR1mNWIx)

- [ ] **HiringMeister**: Establish contact by email or Telegram with the intern
      with a few words about the next steps

- [ ] **Intern**: Post your laptop's OS (Windows, Linux, Mac) in the comments of
      this issue
  - Our dev environment is only adapted for Linux and Mac. Windows users have to
    install dual boot or a VM with Linux (Ubuntu)

- [ ] **Intern**: Confirm access to the public GH repos
  - [ ] [helpers](https://github.com/causify-ai/helpers)
  - [ ] [tutorials](https://github.com/causify-ai/tutorials)

- [ ] **HiringMeister**: Give the intern write access to the current
      Intern-focused project on GH

- [ ] **IT**: @Shayawnn Add the intern to the mailing group
      `contributors@causify.ai` so that they can send
      [morning TODO emails](https://github.com/causify-ai/helpers/blob/master/docs/work_organization/all.team_collaboration.how_to_guide.md#morning-todo-email)
  - The intern's personal e-mail address can be found in the corresponding Asana
    task in the
    [Hiring](https://app.asana.com/0/1208280136292379/1208280159230261) project

- [ ] **HiringMeister**: Update the
      [Access Tracker](https://docs.google.com/spreadsheets/d/130tDQBLAeq89uOTj9pyE8r1-o2-OKztCZYZtyiOKnLk/edit?resourcekey=&gid=1024055821#gid=1024055821)
      spreadsheet
  - Put "Yes" in the columns that the intern now has access to

### IT setup

- [ ] **Intern**: Set up the development environment following instructions in
      [`intern.set_up_development_on_laptop.how_to_guide.md`](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/intern.set_up_development_on_laptop.how_to_guide.md)
  - We expect the intern to independently solve all the problems they encounter
    through trial and error, googling and ChatGPT-ing
  - If you cannot solve some problem no matter how hard you try:
    - Check if the problem has already been reported and discussed in one of the
      existing issues
    - If not, create a new issue and provide a full report
      - Describe your problem in detail, including the full context to reproduce
        (e.g., copy-and-paste the command you ran and the output you got; do not
        use screenshots)
      - Describe what you have already tried to fix it and what was the result
      - Tag the hiring team
  - After the problem is resolved, then, if applicable, do a PR to fix the bug /
    add a description of the problem and the solution to the docs
  - See also
    [`Collaboration for problem solving`](https://github.com/causify-ai/helpers/blob/master/docs/work_organization/all.team_collaboration.how_to_guide.md#collaboration-for-problem-solving)

### Must-read

- [ ] **Intern**: Carefully study all the documents in
      [the must-read list](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/all.dev_must_read_checklist.reference.md)
  - [ ] [General rules of collaboration](https://github.com/causify-ai/helpers/blob/master/docs/work_organization/all.team_collaboration.how_to_guide.md)
  - [ ] [Coding style guide](https://github.com/causify-ai/helpers/blob/master/docs/code_guidelines/all.coding_style.how_to_guide.md)
  - [ ] [How to write unit tests](https://github.com/causify-ai/helpers/blob/master/docs/tools/unit_test/all.write_unit_tests.how_to_guide.md)
  - [ ] [How to run unit tests](https://github.com/causify-ai/helpers/blob/master/docs/tools/unit_test/all.run_unit_tests.how_to_guide.md)
  - [ ] [Creating a Jupyter Notebook](https://github.com/causify-ai/helpers/blob/master/docs/tools/notebooks/all.jupyter_notebook.how_to_guide.md)
  - [ ] [What to do before opening a PR](https://github.com/causify-ai/helpers/blob/master/docs/code_guidelines/all.submit_code_for_review.how_to_guide.md)
  - [ ] [Code review process](https://github.com/causify-ai/helpers/blob/master/docs/code_guidelines/all.code_review.how_to_guide.md)
  - [ ] [Git workflows and best practices](https://github.com/causify-ai/helpers/blob/master/docs/tools/git/all.git.how_to_guide.md)
  - [ ] [GitHub organization](https://github.com/causify-ai/helpers/blob/master/docs/work_organization/all.use_github.how_to_guide.md)
  - [ ] [Tips for writing documentation](https://github.com/causify-ai/helpers/blob/master/docs/documentation_meta/all.writing_docs.how_to_guide.md)
  - They will help you get up to speed with our practices and development style
  - Read them carefully one by one
  - Ask questions
  - Memorize / internalize all the information
  - Take notes
  - Mark the reading as done
  - Open a GH issue/PR to propose improvements to the documentation

### Final checks

- [ ] **Intern**: Exercise all the important parts of the systems
  - [ ] Create a GitHub issue
  - [ ] Check out and pull the latest version of the repo code
  - [ ] Create a branch
  - [ ] Run regressions (`i run_fast_tests`)
  - [ ] Run Linter (`i lint --files="..."`)
  - [ ] Start a Docker container (`i docker_bash`)
  - [ ] Start a Jupyter server (`i docker_jupyter`)
  - [ ] Do a PR
- Tip: a good approach to the "final checks" is to perform all the steps
  (opening an issue, creating a branch, filing a PR) for something very small
  but useful -- like fixing a typo in the docs.
- To get used to our process, for the first couple of PRs post the
  [PR checklist](https://github.com/causify-ai/helpers/blob/master/docs/code_guidelines/all.submit_code_for_review.how_to_guide.md#checklist)
  in a comment and check the boxes when the requirements are met
