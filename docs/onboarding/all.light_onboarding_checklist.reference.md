<!-- toc -->

- [Light onboarding checklist](#light-onboarding-checklist)
  * [Light onboarding vs. full onboarding](#light-onboarding-vs-full-onboarding)
  * [Checklist](#checklist)
    + [Org](#org)
    + [IT setup](#it-setup)
    + [Must-read](#must-read)
    + [Final checks](#final-checks)

<!-- tocstop -->

# Light onboarding checklist

## Light onboarding vs. full onboarding

- The "light" onboarding process is intended for people who have not become
  permanent members of the team yet, e.g., interns or those on a probationary
  period
- Upon completing the light onboarding, the new recruit will be able to develop
  in our common environment, open GitHub issues and PRs, use our extensive
  coding toolchain
- However, some of the steps of the full onboarding process (like creating a
  company email) are postponed until the team member is welcomed to a permanent
  position

## Checklist

### Org

- [ ] **Team leader**: File an issue with this checklist
  - The title is "Light-onboarding {{Name}}"
  - Copy paste the following checklist
  - The issue should be assigned to the team leader and the new recruit

- [ ] **Team leader**: Establish contact by Slack or email with the new recruit
      with a few words about the next steps

- [ ] **New recruit**: Send the following information to your team leader
  - Full name:
  - Aka:
  - Personal email:
  - Github user:
  - Laptop OS: Windows, Linux, or Mac
  - Physical location and timezone
  - User's SSH public key

- [ ] **New recruit**: Confirm access to the public GH repos
  - [ ] [Kaizen-ai](https://github.com/causify-ai/kaizenflow)
  - [ ] [helpers](https://github.com/causify-ai/helpers)
  - [ ] [tutorials](https://github.com/causify-ai/tutorials)

- [ ] **Team leader**: Add the new recruit to the Slack workspace

- [ ] **New recruit**: Confirm access to the Slack workspace

### IT setup

- [ ] **New recruit**: Set up the development environment following instructions
      in
      [`all.set_up_development_on_laptop.how_to_guide.md`](/docs/onboarding/all.set_up_development_on_laptop.how_to_guide.md)

### Must-read

- [ ] **Team member**: Carefully study all the documents in
      [the must-read list](/docs/onboarding/all.dev_must_read_checklist.reference.md)
  - They will help you get up to speed with our practices and development style
  - Read them carefully one by one
  - Ask questions
  - Memorize / internalize all the information
  - Take notes
  - Mark the reading as done
  - Open a GH issue/PR to propose improvements to the documentation

### Final checks

- [ ] **Team member**: Exercise all the important parts of the systems
  - [ ] Create a GitHub issue
  - [ ] Check out and pull the latest version of the repo code
  - [ ] Create a branch
  - [ ] Run regressions (`i run_fast_tests`)
  - [ ] Run Linter (`i lint --files="..."`)
  - [ ] Start a Docker container (`i docker_bash`)
  - [ ] Start a Jupyter server (`i docker_jupyter`)
  - [ ] Do a PR
