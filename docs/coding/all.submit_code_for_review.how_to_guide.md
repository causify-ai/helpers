# First Review Process

<!-- toc -->

- [Read Python Style Guide](#read-python-style-guide)
- [Run Linter](#run-linter)
- [Compare your code to example code](#compare-your-code-to-example-code)
- [Edit code/text written by AI](#edit-codetext-written-by-ai)
- [Save Reviewer time](#save-reviewer-time)
  * [Make sure checks are green](#make-sure-checks-are-green)
  * [Review your own PR](#review-your-own-pr)
  * [Assign Reviewers](#assign-reviewers)
  * [Mention the issue](#mention-the-issue)
  * [Resolve conversations](#resolve-conversations)
  * [Merge master into your branch](#merge-master-into-your-branch)
  * [Ask for reviews](#ask-for-reviews)
  * [Do not use screenshots](#do-not-use-screenshots)
  * [Report bugs correctly](#report-bugs-correctly)
  * [Stick to smaller PRs](#stick-to-smaller-prs)
- [Talk through code and not GitHub](#talk-through-code-and-not-github)
- [Look at examples of first reviews](#look-at-examples-of-first-reviews)

<!-- tocstop -->

We understand that receiving feedback on your code can be a difficult process,
but it is an important part of our development workflow. Here we have gathered
some helpful tips and resources to guide you through your first review.

## Read Python Style Guide

- Before submitting your code for review, we highly recommend that you read our
  [Python Style Guide](/docs/coding/all.coding_style.how_to_guide.md), which
  outlines the major conventions and best practices for writing Python code.
- Adhering to these standards will help ensure that your code is easy to read,
  maintain, and understand for other members of the team.

## Run Linter

- Linter is a tool that checks (and tries to fix automatically) your code for
  syntax errors, style violations, and other issues.
- Run it on all the changed files to automatically catch any code issues before
  filing any PR or before requesting a review!
- Run Linter with `invoke` command (which is abbreviated as `i`) and pass all
  the files you need to lint in quotation marks after the `--files` option,
  separated by a space
- The command should be run from the root of the repo you are developing in
- The file paths should be relative to the repo root
  - Command example:
  ```
  > i lint --files="docs/coding/all.str_to_df.how_to_guide.md linters/utils.py"
  ```
  - Output example:
    ```
    docs/coding/all.str_to_df.how_to_guide.md: 'docs/coding/all.str_to_df.how_to_guide.md' is not referenced in README.md [check_md_reference]
    docs/coding/all.str_to_df.how_to_guide.md:79: 'figs/str_to_df/image1.png' does not follow the format 'figs/all.str_to_df.how_to_guide.md/XYZ' [fix_md_links]
    linters/utils.py:294: [R0916(too-many-boolean-expressions), get_dirs_with_missing_init] Too many boolean expressions in if statement (6/5) [pylint]
    ```
  - `i lint` has options for many workflows. E.g., you can automatically lint
    all the files that you touched in your PR with `--branch`, the files in the
    last commit with `--last-commit`. You can look at all the options with:
    ```
    > i lint --help
    ```
- Fix the lints
  - No need to obsessively fix all of them - just crucial and obvious ones
- Running Linter on a file also applies some formatting fixes to it
  automatically and stages the updated file for commit
- If Linter introduces extensive changes in a PR, causing difficulty in reading
  the diff, a new pull request should be created exclusively for the Linter
  changes, based on the branch of the original PR.

## Compare your code to example code

- To get an idea of what well-formatted and well-organized code looks like, we
  suggest taking a look at some examples of code that adheres to our standards.
- We try to maintain universal approaches to all the parts of the code, so when
  looking at a code example, check for:
  - Code style
  - Docstrings and comments
  - Type hints
  - Dir structure
- Here are some links to example code:
  - Classes, functions and scripts:
    - [`/import_check/show_imports.py`](/import_check/show_imports.py)
    - [`/linters/amp_fix_md_links.py`](/linters/amp_fix_md_links.py)
    - [`/helpers/lib_tasks_lint.py`](/helpers/lib_tasks_lint.py)
  - Unit tests:
    - [`/import_check/test/test_show_imports.py`](/import_check/test/test_show_imports.py)
    - [`/linters/test/test_amp_fix_md_links.py`](/linters/test/test_amp_fix_md_links.py)
    - [`/helpers/test/test_lib_tasks_lint.py`](/helpers/test/test_lib_tasks_lint.py)

## Edit code/text written by AI

- We do not mind if the AI writes the first version of the code or text for you
- We do mind if you simply copy-and-paste its output and submit if for our
  review as-is
- Take whatever is produced by AI as the first draft: go over it, revise it,
  make sure it's readable and relevant, adjust it to fit our specific
  conventions

## Save Reviewer time

- Follow the instructions given in
  [`PR workflows`](/docs/work_organization/all.use_github.how_to_guide.md#pr-workflows)

### Make sure checks are green

- Before requesting review, make sure that all the checks performed by GitHub
  Actions pass
  - The checks and their status can be seen at the bottom of the PR page or in
    the "Checks" tab
- Clicking on a failed check will take you to the extended report with the full
  failure stacktrace
- If the Linter check fails with "The Git client is not clean", then run Linter
  on the files reported by the check (it will automatically update them with
  formatting fixes), commit and push them
- In rare cases it's okay to submit a PR for review with some of the checks
  failing:
  - If the tests are already broken in master
  - If a genuine bug in Linter causes the check to fail or requires reverting
    the automatic fixes
    - Check if this bug is already tracked in an issue, and if not, open a new
      issue to report it

### Review your own PR

- Before requesting review, take a final look at the "Files changed" tab
- Make sure there are
  - No changes you haven't intended
  - No leftovers from debugging
  - No files added by mistake (such as tmp files)

### Assign Reviewers

- Make sure to select a Reviewer in a corresponding GitHub field so he/she gets
  notified
  - <img width="313" alt="" src="https://github.com/kaizen-ai/kaizenflow/assets/31514660/f8534c49-bff6-4d59-9037-d70dc03d5ff9">
  - Junior contributors should assign Team Leaders (e.g., Grisha, DanY, Samarth,
    ...) to review their PR
    - Team Leaders will assign integrators (GP & Paul) themselves after all
      their comments have been addressed
  - Ping the assigned Reviewer in the issue if nothing happens in 24 hours
  - If you want to keep someone notified about changes in the PR but do not want
    to make him/her a Reviewer, type `FYI @github_name` in the comment section

### Mention the issue

- Mention the corresponding issue in the PR description to ease navigation
  - E.g., see an
    [example](https://github.com/kaizen-ai/kaizenflow/pull/288#issue-1729654983)
    - <img width="505" alt="" src="https://github.com/kaizen-ai/kaizenflow/assets/31514660/69fbabec-300c-4f7c-94fc-45c5da5a6817">

### Resolve conversations

- When you've addressed a comment from a Reviewer, press `Resolve conversation`
  button so the Reviewer knows that you actually took care of it
  - <img width="328" alt="" src="https://github.com/kaizen-ai/kaizenflow/assets/31514660/a4c79d73-62bd-419b-b3cf-e8011621ba3c">

### Merge master into your branch

- Before any PR review request do `i git_merge_master` in order to keep the code
  updated
  - Resolve conflicts if there are any
  - Do not forget to push it since this action is a commit itself
- Actually, a useful practice is to merge master to your branch every time you
  get back to work on it
  - This way you make sure that your branch is always using relevant code and
    avoid huge merge conflicts
- You can also easily merge master into your branch by clicking on "Update
  branch" button on the PR page
  <img src="/docs/coding/figs/submit_code_for_review/image1.png">
- **NEVER** press `Squash and merge` button yourself
  - You need to merge master branch into your branch - not vice verca!
  - This is a strictly Team Leaders' and Integrators' responsibility

### Ask for reviews

- When you've addressed all the comments and need another round of review:
  - Press the circling arrows sign next to the Reviewer for the ping
    - <img width="280" alt="" src="https://github.com/kaizen-ai/kaizenflow/assets/31514660/4f924f4f-abab-40be-975d-a4fa81d9af3b">
  - Remove `PR_for_authors` and add the `PR_for_reviewers` label (see
    [here](/docs/work_organization/all.use_github.how_to_guide.md#pr-labels) for
    the description of available labels)
    - <img width="271" alt="" src="https://github.com/kaizen-ai/kaizenflow/assets/31514660/3580bf34-dcba-431b-af5c-5ae65f7597c3">

### Do not use screenshots

- Stack traces and logs are much more convenient to use for debugging
- Screenshots are often too small to capture both input and return logs while
  consuming a lot of basically useless memory
- Reviewers and collaborators cannot copy from the screenshot, which means that
  if they want to reproduce the error, they need to manually type the code shown
  in the screenshot, which is very inconvenient and error-prone
- The exceptions are plots and non-code information
- Examples:
  - _Bad_

    <img width="677" alt="scree" src="https://github.com/kaizen-ai/kaizenflow/assets/31514660/699cd1c5-53d2-403b-a0d7-96c66d4360ce">
  - _Good_

    Input:
    ```
    type_ = "supply"
    supply_curve1 = ddcrsede.get_supply_demand_discrete_curve(
        type_, supply_orders_df1
    )
    supply_curve1
    ```

    Error:
    ```
    ---------------------------------------------------------------------------
    NameError                                 Traceback (most recent call last)
    Cell In [5], line 2
          1 type_ = "supply"
    ----> 2 supply_curve1 = ddcrsede.get_supply_demand_discrete_curve(
          3     type_, supply_orders_df1
          4 )
          5 supply_curve1

    NameError: name 'ddcrsede' is not defined
    ```

### Report bugs correctly

- Whenever you face any errors, put as much information about the problem as
  possible, e.g.,:
  - What you are trying to achieve
  - Command line you ran, e.g.,
    ```
    > i lint -f defi/tulip/test/test_dao_cross_sol.py
    ```
  - **Copy-paste** the error and the stack trace from the cmd line, **no
    screenshots**, e.g.,
    ```
    Traceback (most recent call last):
      File "/venv/bin/invoke", line 8, in <module>
        sys.exit(program.run())
      File "/venv/lib/python3.8/site-packages/invoke/program.py", line 373, in run
        self.parse_collection()
    ValueError: One and only one set-up config should be true:
    ```
  - The log of the run
    - Maybe the same run using `-v DEBUG` to get more info on the problem
  - What the problem is
  - Why the outcome is different from what you expected
  - E.g. on how to report any issues
    - [https://github.com/kaizen-ai/kaizenflow/issues/370#issue-1782574355](https://github.com/kaizen-ai/kaizenflow/issues/370#issue-1782574355)

### Stick to smaller PRs

- It's better to push frequently and ask for feedback early to avoid large
  refactoring

## Talk through code and not GitHub

- PR authors should, as a rule, talk to reviewers not through GitHub but through
  code
  - E.g., if there is something you want to explain to the reviewers, you should
    not comment on your own PR, but instead add comments in the code itself, or
    improve the code so that it doesn't need explanation
  - Everything on GitHub is lost once the PR is closed, so all knowledge needs
    to go inside the code or the documentation
- Of course it's ok to respond to questions on GitHub

## Look at examples of first reviews

- It can be helpful to review some examples of previous first reviews to get an
  idea of what common issues are and how to address them.
- Here are some links to a few "painful" first reviews:
  - Adding unit tests:
    - [https://github.com/kaizen-ai/kaizenflow/pull/166](https://github.com/kaizen-ai/kaizenflow/pull/166)
    - [https://github.com/kaizen-ai/kaizenflow/pull/186](https://github.com/kaizen-ai/kaizenflow/pull/186)
  - Writing scripts:
    - [https://github.com/kaizen-ai/kaizenflow/pull/267](https://github.com/kaizen-ai/kaizenflow/pull/267)
    - [https://github.com/kaizen-ai/kaizenflow/pull/276](https://github.com/kaizen-ai/kaizenflow/pull/276)
