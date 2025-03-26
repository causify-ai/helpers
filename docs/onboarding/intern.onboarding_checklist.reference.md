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
  [_full_ onboarding process](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/all.onboarding_checklist.reference.md)
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

- [ ] **Intern**: Update this GitHub issue if you face any problems. If
      applicable, do a PR proposing improvements to the checklist (or any other
      docs), since this will allow us to improve the process as we move forward

- [ ] **Intern**: Join the Telegram channel - https://t.me/+DXZXsWoEHR1mNWIx

- [ ] **HiringMeister**: Establish contact by email or Telegram with the intern
      with a few words about the next steps

- [ ] **Intern**: Post your laptop's OS (Windows, Linux, Mac) in the comments of
      this issue

- [ ] **Intern**: Confirm access to the public GH repos
  - [ ] [helpers](https://github.com/causify-ai/helpers)
  - [ ] [tutorials](https://github.com/causify-ai/tutorials)

- [ ] **IT**: @Shayawnn Add the intern to the mailing group
      `contributors@causify.ai` so that they can send
      [morning TODO emails](https://github.com/causify-ai/helpers/blob/master/docs/work_organization/all.team_collaboration.how_to_guide.md#morning-todo-email)
  - The intern's personal e-mail address can be found in the corresponding Asana
    task in the
    [Hiring](https://app.asana.com/0/1208280136292379/1208280159230261) project

### IT setup

- [ ] **Intern**: Set up the development environment following instructions in
      [`intern.set_up_development_on_laptop.how_to_guide.md`](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/intern.set_up_development_on_laptop.how_to_guide.md)

### Must-read

- [ ] **Intern**: Carefully study all the documents in
      [the must-read list](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/all.dev_must_read_checklist.reference.md)
  - [ ] [General rules of collaboration](https://github.com/causify-ai/helpers/blob/master/docs/work_organization/all.team_collaboration.how_to_guide.md)
  - [ ] [Coding style guide](https://github.com/causify-ai/helpers/blob/master/docs/coding/all.coding_style.how_to_guide.md)
  - [ ] [How to write unit tests](https://github.com/causify-ai/helpers/blob/master/docs/coding/all.write_unit_tests.how_to_guide.md)
  - [ ] [How to run unit tests](https://github.com/causify-ai/helpers/blob/master/docs/coding/all.run_unit_tests.how_to_guide.md)
  - [ ] [Creating a Jupyter Notebook](https://github.com/causify-ai/helpers/blob/master/docs/coding/all.jupyter_notebook.how_to_guide.md)
  - [ ] [What to do before opening a PR](https://github.com/causify-ai/helpers/blob/master/docs/coding/all.submit_code_for_review.how_to_guide.md)
  - [ ] [Code review process](https://github.com/causify-ai/helpers/blob/master/docs/coding/all.code_review.how_to_guide.md)
  - [ ] [Git workflows and best practices](https://github.com/causify-ai/helpers/blob/master/docs/work_tools/git/all.git.how_to_guide.md)
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
