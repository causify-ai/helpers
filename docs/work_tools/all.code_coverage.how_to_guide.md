<!-- toc -->

- [Codecov Integration and Coverage Setup Documentation](#codecov-integration-and-coverage-setup-documentation)
  * [Setting Up Codecov](#setting-up-codecov)
  * [Coverage Configuration](#coverage-configuration)
  * [GitHub Actions Workflow](#github-actions-workflow)
    + [Workflow Schedule:](#workflow-schedule)
    + [Workflow Jobs:](#workflow-jobs)
  * [Codecov Configuration (codecov.yml)](#codecov-configuration-codecovyml)
  * [Viewing Coverage Reports](#viewing-coverage-reports)
  * [Running Coverage Locally](#running-coverage-locally)
  * [Additional Functionalities and Extensions](#additional-functionalities-and-extensions)
  * [Coverage Behavior and Best Practices](#coverage-behavior-and-best-practices)
  * [Troubleshooting](#troubleshooting)

<!-- tocstop -->

# Codecov Integration and Coverage Setup Documentation

This documentation describes the setup and usage of Codecov integration for our
repos. The purpose is to explain how Codecov coverage tracking is configured,
the functionalities implemented, and how developers can interpret, interact
with, and extend the coverage results.

## Setting Up Codecov

Codecov was integrated by adding necessary files and configuration steps:

Files and Directories Added:

- `.coveragerc`: Configures coverage collection rules
- `.github/gh_requirements.txt`: Lists dependencies necessary for the coverage
  workflow
- `.github/workflows/coverage_tests.yml`: Defines GitHub Actions workflow for
  automated coverage runs
- `.github/codecov.yml`: Specifies Codecov-specific behaviors such as flags,
  comments, and coverage thresholds

## Coverage Configuration

The `.coveragerc` file located at the repository's root defines coverage
measurement settings:

- `Source Directory`: Specifies the directory for coverage collection.
  ```
  [run]
  source = helpers
  ```

- `Excluded Files`: These files are omitted from coverage reporting.
  ```
  [report]
  omit =
      */devops/compose/*
      */helpers/test/outcomes/*/tmp.scratch/*
  ```

## GitHub Actions Workflow

Coverage tests are automated via GitHub Actions -
`.github/workflows/coverage_tests.yml`.

### Workflow Schedule:

- Runs daily at midnight (UTC)
- Can be manually triggered (`workflow_dispatch`)
- Action fails if coverage drops by `1%` (including `fast`, `slow` and
  `superslow` tests)

### Workflow Jobs:

1. Fast Tests Coverage:

- Runs daily or on manual trigger
- Uploads report flagged as `fast`

2. Slow Tests Coverage:

- Runs daily or on manual trigger
- Uploads report flagged as `slow`

3. Superslow Tests Coverage:

- Runs weekly on Monday or on manual trigger.
- Uploads report flagged as `superslow`.

4. Each job:

- Generates an `XML` coverage report (`coverage.xml`)
- Uploads reports to `Codecov` with respective flags (`fast`, `slow`,
  `superslow`)
- Marks CI as failed if upload errors occur (`fail_ci_if_error: true`)

## Codecov Configuration (codecov.yml)

Coverage flags and project-level checks are configured at -
`.github/codecov.yml`.

1. Flag Management: The `carryforward` option allows Codecov to reuse the
   previous coverage data if no new coverage report is submitted for a specific
   flag during a `CI` run. Setting it to true ensures continuous visibility for
   flags that might not run on every CI cycle.
   ```
   flag_management:
   default_rules:
       carryforward: false
   individual_flags:
       - name: fast
       carryforward: true
       - name: slow
       carryforward: true
       - name: superslow
       carryforward: true
   ```

2. Comment Behavior: `comment = false` disables per-line comments in GitHub PRs.
   ```
   comment: false
   ```

3. Coverage Status Check:

- Enabled for `master` branch.
- Compares coverage changes relatively.
- Fails CI if total coverage decreases by 1% or more. This threshold ensures
  that significant coverage drops do not go unnoticed, enforcing code quality
  standards.
  ```
  coverage:
  status:
      project:
      enabled: true
      target_branch: master
      comparator: relative
      threshold: 1
      flags:
          - fast
          - slow
          - superslow
      patch:
      enabled: false
  ```

## Viewing Coverage Reports

Coverage results for the helpers repository are accessible via Codecov.

- Codecov UI link for helpers -
  [helpers repo coverage](https://app.codecov.io/gh/causify-ai/helpers)
- `Master Build Dashboard Notebook`:
  [`/dev_scripts_helpers/update_devops_packages/notebooks/Master_buildmeister_dashboard.ipynb`](/dev_scripts_helpers/update_devops_packages/notebooks/Master_buildmeister_dashboard.ipynb)

## Running Coverage Locally

Developers can manually run coverage tasks locally via Invoke commands:

- Fast Tests:
```
invoke run_fast_coverage .
```

- Slow Tests:
```
invoke run_slow_coverage .
```

- Superslow Tests:
```
invoke run_superslow_coverage .
```

Coverage results (text/XML/HTML) are generated locally for immediate inspection.

## Additional Functionalities and Extensions

Additional functionalities provided by Codecov that can be utilized or extended
include:

- `Pull Request Comments`: Automatically generate detailed coverage summaries or
  line-by-line coverage comments directly in GitHub pull requests
- `Coverage Badges`: Integrate coverage badges in the repository `README` to
  visibly show current coverage status
- `Report Customization`: Configure detailed reporting settings to specify what
  information to display or omit in coverage summaries

## Coverage Behavior and Best Practices

- Coverage reports are uploaded regardless of test success to ensure coverage
  tracking consistency
- Coverage flags (`fast`, `slow`, `superslow`) allow separate visibility and
  tracking
- Regular review of coverage differences (visible in PR checks and Codecov UI)
  is encouraged to maintain code quality

## Troubleshooting

- Check GitHub Actions logs for errors in coverage upload steps
- Ensure `CODECOV_TOKEN` is correctly set as a GitHub secret
- Validate workflow and coverage configuration files for correctness if issues
  arise
