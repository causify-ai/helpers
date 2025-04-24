- Source:
  [`bounty.onboarding_checklist.reference.md`](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/bounty.onboarding_checklist.reference.md)

### Org

- [ ] **Collaborator**: Fork the repos
  - [ ] [helpers](https://github.com/causify-ai/helpers)
  - [ ] [tutorials](https://github.com/causify-ai/tutorials)

- [ ] **Collaborator**: File an issue with this checklist
  - The title is "Onboarding {{Name}}"
  - The issue should be assigned to the collaborator

- [ ] **Collaborator**: Update this GitHub issue if you face any problems. If applicable, do a PR proposing improvements to the checklist (or any other docs), since this will allow us to improve the process as we move forward

- [ ] **Collaborator**: Post your laptop's OS (Windows, Linux, Mac) in the comments of this issue

- [ ] **Collaborator**: Confirm access to the public GH repos
  - [ ] [helpers](https://github.com/causify-ai/helpers)
  - [ ] [tutorials](https://github.com/causify-ai/tutorials)

### IT setup

- [ ] **Collaborator**: Set up the development environment following instructions in [`intern.set_up_development_on_laptop.how_to_guide.md`](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/intern.set_up_development_on_laptop.how_to_guide.md)

### Must-read

- [ ] **Collaborator**: Carefully study all the documents in [the must-read list](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/all.dev_must_read_checklist.reference.md)
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

- [ ] **Collaborator**: Exercise all the important parts of the systems
  - [ ] Create a GitHub issue
  - [ ] Check out and pull the latest version of the repo code
  - [ ] Create a branch
  - [ ] Run regressions (`i run_fast_tests`)
  - [ ] Run Linter (`i lint --files="..."`)
  - [ ] Start a Docker container (`i docker_bash`)
  - [ ] Start a Jupyter server (`i docker_jupyter`)
  - [ ] Do a PR
