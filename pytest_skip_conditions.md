# Test Skip Conditions Guide
This document organizes all pytest skip conditions used across the helpers
repository

Tests are skipped based on platform, environment, dependencies, and repository
configuration to ensure they run only when appropriate

## Custom Test Markers
- The test suite uses custom pytest markers to categorize and filter tests
- These markers are defined in `pytest.ini` and help organize test execution
  based on requirements:
  - `need_dev_container`: Tests requiring dependencies not available in the base
    environment
  - `no_container`: Tests that run without a container (invoke target tests)
  - `requires_ck_aws`: Tests that require CK AWS connection
  - `requires_ck_infra`: Tests that require CK infrastructure
  - `requires_docker_in_docker`: Tests requiring docker children or sibling
    containers
  - `slow`: Tests considered slow (~30s timeout)
  - `superslow`: Tests considered very slow (~3600s timeout)

## Skip Conditions by Category

### Platform and Operating System
Tests that depend on specific operating systems or host configurations:

| Condition                      | Effect                                                         |
| :----------------------------- | :------------------------------------------------------------- |
| `sys.platform == "darwin"`     | Skipped on macOS                                               |
| `hserver.is_host_mac()`        | Skipped when the host is a Mac, due to Docker compose mismatch |
| `not hserver.is_host_mac()`    | Skipped on non-Mac hosts; the test requires a Mac              |
| `hserver.is_host_gp_mac()`     | Skipped when running on GP's Mac specifically                  |
| `not hserver.is_host_gp_mac()` | Skipped on every machine except GP's Mac                       |

### Container and Docker Environment
Tests that require specific Docker or container configurations:

| Condition                                                           | Effect                                                      |
| :------------------------------------------------------------------ | :---------------------------------------------------------- |
| `hserver.is_inside_docker()`                                        | Skipped inside Docker; the test needs to run on the host    |
| `not hserver.is_inside_docker()`                                    | Skipped outside Docker; the test needs a container          |
| `not hserver.can_run_docker_from_docker()`                          | Skipped when the docker-in-docker capability is unavailable |
| `hserver.is_host_mac() and hdocker.get_docker_engine() == "apple"`  | Skipped on Mac hosts using the Apple container engine       |
| `not (hserver.is_inside_docker() and hserver.is_host_gp_mac())`     | Skipped unless running inside Docker on GP's Mac            |
| `not (not hserver.is_inside_docker() and hserver.is_host_gp_mac())` | Skipped unless running outside Docker on GP's Mac           |

### Continuous Integration
Tests affected by CI execution context:

| Condition                                                       | Effect                                                                  |
| :-------------------------------------------------------------- | :---------------------------------------------------------------------- |
| `hserver.is_inside_ci()`                                        | Skipped in CI; local output differs from CI output                      |
| `not hserver.is_inside_ci()`                                    | Skipped outside CI; the test requires the CI environment                |
| `hserver.is_inside_ci() or not hgit.is_in_amp_as_supermodule()` | Skipped in CI, or whenever the repo isn't set up as the AMP supermodule |

### Infrastructure and Deployment Context
Tests requiring specific Causify infrastructure:

| Condition                                                  | Effect                                                              |
| :--------------------------------------------------------- | :------------------------------------------------------------------ |
| `not hserver.is_inside_docker_container_on_csfy_server()`  | Skipped unless running inside a Docker container on the Csfy server |
| `not hserver.is_outside_docker_container_on_csfy_server()` | Skipped unless running outside Docker on the Csfy server            |

### Repository Structure and Configuration
Tests tied to specific repository configurations:

| Condition                                 | Effect                                                                    |
| :---------------------------------------- | :------------------------------------------------------------------------ |
| `not hgit.is_amp()`                       | Skipped outside the AMP repository                                        |
| `hgit.is_amp()`                           | Skipped inside the AMP repository                                         |
| `not hgit.is_in_amp_as_supermodule()`     | Skipped unless AMP is set up as the supermodule                           |
| `hgit.is_in_amp_as_submodule()`           | Skipped when AMP is set up as a submodule; the test needs to run directly |
| `not hgit.is_in_amp_as_submodule()`       | Skipped unless AMP is set up as a submodule                               |
| `not hgit.is_in_helpers_as_supermodule()` | Skipped unless Helpers is set up as the supermodule                       |
| `hgit.is_git_worktree()`                  | Skipped when running from inside a Git worktree                           |
| `not hgit.is_git_worktree()`              | Skipped unless running from inside a Git worktree                         |

### Dependencies and Tools
Tests requiring specific external tools or libraries:

| Condition                                                       | Effect                                                                          |
| :-------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| `hllmcli._check_llm_executable()`                               | Skipped when the `llm` executable is found; the test targets the not-found path |
| `not hllmcli._check_llm_executable()`                           | Skipped when the `llm` executable isn't found                                   |
| `shutil.which("pandoc") is None`                                | Skipped when pandoc isn't installed                                             |
| `shutil.which("typst") is None`                                 | Skipped when typst isn't installed                                              |
| `not hmarform.is_flowmark_available("global")`                  | Skipped when the flowmark tool isn't available                                  |
| `not hmarform.is_mdformat_available("library")`                 | Skipped when the mdformat tool isn't available                                  |
| `not hmarform.is_prettier_available("global")`                  | Skipped when prettier isn't available                                           |
| `version.parse(jupytext.__version__) < version.parse("1.17.1")` | Skipped when the installed jupytext version is too old                          |
| `not _TABULATE_AVAILABLE`                                       | Skipped when the tabulate module isn't available                                |

### Cloud and AWS Services
Tests requiring cloud service availability:

| Condition                          | Effect                                                                     |
| :--------------------------------- | :------------------------------------------------------------------------- |
| `not hserver.is_CK_S3_available()` | Skipped when CK AWS S3 isn't available                                     |
| `hserver.is_CK_S3_available()`     | Skipped when CK AWS S3 is available; the test targets the unavailable path |

## Known Issues and References
Tests reference specific issues and tasks related to skip conditions:

- **CsfyTask8868**: macOS-specific Docker issues affecting tool rendering
  (pandoc, typst, prettier, markdown tools)
- **CsfyIssue8889**: macOS lint test failures requiring conditional skipping
- **Version incompatibilities**: Jupytext versions and markdown tool versions
  affect test availability

## Execution Contexts
Understanding when tests execute helps with debugging and maintenance

### Tests Requiring Docker
- Docker and container capabilities:
  - `requires_docker_in_docker`: Needs docker children or sibling containers,
    including socket access
  - `can_run_docker_from_docker()`: Requires docker-in-docker capability

### Tests Requiring Infrastructure
- Infrastructure and cloud access:
  - `requires_ck_infra`: Needs CK infrastructure access
  - `requires_ck_aws`: Needs CK AWS connection
  - Csfy server checks (e.g.,
    `hserver.is_inside_docker_container_on_csfy_server()`): Require Csfy
    infrastructure

### Tests Requiring Development Environment
- Development environment dependencies:
  - `need_dev_container`: Depends on a dev container with extra dependencies
  - Tool-availability checks (e.g., `hmarform.is_flowmark_available()`): Skip if
    the required tool is missing

### Tests Running Outside Containers
- Host-only execution:
  - `no_container`: Invoke target tests running on host
  - `hserver.is_inside_docker()`: Requires host execution
  - `hgit.is_git_worktree()`: Requires local Git worktree setup

## Test Organization Strategy
The skip conditions serve multiple purposes:

- **Isolation**: Keep platform/environment-specific tests from running in
  incompatible contexts
- **Reliability**: Prevent flaky tests by ensuring dependencies are available
- **Efficiency**: Skip expensive tests (slow, superslow) in quick feedback loops
- **Coverage**: Run different test suites on appropriate infrastructure
