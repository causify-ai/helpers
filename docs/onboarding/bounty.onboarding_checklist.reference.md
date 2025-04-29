# Bounty hunters onboarding

<!-- toc -->

- [Checklist](#checklist)
- [Instructions](#instructions)
  * [Org](#org)
  * [Working on a bounty](#working-on-a-bounty)

<!-- tocstop -->

## Checklist

- Source:
  [`bounty.onboarding_checklist.reference.md`](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/bounty.onboarding_checklist.reference.md)

- [ ] **Contributor**: Fork the repos
  - [ ] [helpers](https://github.com/causify-ai/helpers)
  - [ ] [tutorials](https://github.com/causify-ai/tutorials)
- [ ] **Contributor**: Set up the development environment following instructions
      in
      [`intern.set_up_development_on_laptop.how_to_guide.md`](https://github.com/causify-ai/helpers/blob/master/docs/onboarding/intern.set_up_development_on_laptop.how_to_guide.md)
- [ ] **Contributor**: Carefully study all the documents in the must-read list:
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

## Instructions

### General organization

- All the collaboration happens on GitHub as a typical open-source project
- The bounties are published in a
  [Gdoc with specs](https://docs.google.com/document/d/1xPgQ2tWXQuVWKkGVONjOGd5j14mXSmGeY_4d1_sGzAE/edit?tab=t.0#heading=h.1ja24i564v3o)
  - We are going to be adding more and more bounties depending on the demand
- There is a
  [sign-up sheet](https://docs.google.com/spreadsheets/d/1QiTCyydNQwftMWj3nTL5jWBqOq3UCziFChF08aRNBcE/edit?gid=0#gid=0)
  for the bounties
  - There can be at most 2 people working on each bounty
  - If 2 people are working on the same bounty, they are competing with each
    other
    - You get paid only if you do the task better than the other person
  - At some point (e.g., the task is close to being done) we reserve the right
    to make the bounty "locked", meaning that other people can no longer take it
    on
- There will be minimal interaction from us
  - In general we don't answer questions, contributors need to figure things out
    themselves
  - If they believe there is a genuine bug somewhere in the codebase, they
    should
    - Check the existing issues in case this bug has already been reported
    - If not, file an issue with a proper report and ideally propose a fix too
- If a contributor succeeds, we pay the bounty $XYZ as a bank transfer or in
  Tether
  - If both sides agree, the contributor gets a paid internship / RA / TA
  - We then on-board the contributors as part of our team and dedicate our time
    to train them

### Working on a bounty

- Take time to peruse the description of the bounty
  - No need to rush, there is always time and work to do
- Before any implementation, the contributor should create an issue for the task
  and post a detailed plan of action there
  - By default the contributor is then free to proceed according to their plan
    (implement, file a PR)
  - We reserve the right to review and propose changes at any point
- For each bounty, the contributor should spend ~1 hour looking for a package or
  already existing solutions on GitHub
  - One should report the findings even if nothing has been found (e.g.,
    explaining how the search was done)
  - It's totally ok (and actually recommended) to re-use packages and other
    people's work to get stuff done
  - If you find an implementation of the bounty in the wild, congrats, you made
    money with very little work
- All code needs to be written using our coding style
  - See [`template_code.py`](/template_code.py),
    [coding style doc](/docs/coding/all.coding_style.how_to_guide.md),
    [examples of good code](/docs/coding/all.submit_code_for_review.how_to_guide.md#compare-your-code-to-example-code)
  - We provide our Linter and our AI code-styler / reviewer (once available) to
    help with formatting and style fixes
- All code needs to be unit tested according to our
  [standards and infrastructure](/docs/coding/all.write_unit_tests.how_to_guide.md)
- The project needs to be documented in the way we
  [document software](/docs/documentation_meta/all.writing_docs.how_to_guide.md)
