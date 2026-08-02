# Test Skip Conditions Guide

This document organizes all pytest skip conditions used across the helpers
repository.

Tests are skipped based on platform, environment, dependencies, and repository
configuration to ensure they run only when appropriate.

## Custom Test Markers

- The test suite uses custom pytest markers to categorize and filter tests.
- These markers are defined in `pytest.ini` and help organize test execution
  based on requirements:

  - `need_dev_container`: Tests requiring dependencies not available in the base environment
  - `no_container`: Tests that run without a container (invoke target tests)
  - `requires_ck_aws`: Tests that require CK AWS connection
  - `requires_ck_infra`: Tests that require CK infrastructure
  - `requires_docker_in_docker`: Tests requiring docker children or sibling containers
  - `slow`: Tests considered slow (~30s timeout)
  - `superslow`: Tests considered very slow (~3600s timeout)

## Skip Conditions by Category

### Platform and Operating System

Tests that depend on specific operating systems or host configurations:

// TODO(ai_gp): Condition, Effect, Example

| Condition | Reason | Impact |
| :------- | :------- | :------- |
| `sys.platform == "darwin"` | Platform-specific behavior | Skipped on macOS |
| `hserver.is_host_mac()` | Docker compose mismatch | Skipped when Mac is host |
| `not hserver.is_host_mac()` | Requires non-Mac host | Skipped when Mac is host |
| `hserver.is_host_gp_mac()` | GP's Mac specific test | Skipped on other machines |
| `not hserver.is_host_gp_mac()` | Not GP's Mac | Skipped on GP's Mac |

### Container and Docker Environment

Tests that require specific Docker or container configurations:

| Condition | Reason | Impact |
| :------- | :------- | :------- |
| `hserver.is_inside_docker()` | Test needs to run outside Docker | Skipped inside Docker |
| `not hserver.is_inside_docker()` | Requires running outside Docker | Skipped outside Docker |
| `hserver.can_run_docker_from_docker()` | Docker-in-docker capability needed | Skipped when unavailable |
| `hdocker.get_docker_engine() == "apple"` | Apple Docker engine check | Skipped with other engines |
| `hserver.is_inside_docker() and hserver.is_host_gp_mac()` | Inside Docker on GP's Mac | Skipped when condition false |
| `not hserver.is_inside_docker() and hserver.is_host_gp_mac()` | Outside Docker on GP's Mac | Skipped when condition false |

### Continuous Integration

Tests affected by CI execution context:

| Condition | Reason |
| :------- | :------- |
| `hserver.is_inside_ci()` | In CI output differs from local |
| `not hserver.is_inside_ci()` | Requires local execution environment |
| `hserver.is_inside_ci() or not hgit.is_in_amp_as_supermodule()` | Complex CI/repo check |

### Infrastructure and Deployment Context

Tests requiring specific Causify infrastructure:

| Condition | Reason |
| :------- | :------- |
| `hserver.is_inside_docker_container_on_csfy_server()` | Running on Csfy server |
| `hserver.is_outside_docker_container_on_csfy_server()` | Running outside Docker on Csfy |
| `hserver.is_inside_docker_container_on_csfy_server()` | Config matching check |

### Repository Structure and Configuration

Tests tied to specific repository configurations:

| Condition | Reason |
| :------- | :------- |
| `hgit.is_amp()` | Only run in AMP repository |
| `not hgit.is_amp()` | Only run outside AMP |
| `hgit.is_in_amp_as_supermodule()` | Requires AMP as supermodule |
| `not hgit.is_in_amp_as_supermodule()` | Requires different structure |
| `hgit.is_in_amp_as_submodule()` | Requires AMP as submodule |
| `not hgit.is_in_amp_as_submodule()` | Requires AMP as supermodule |
| `hgit.is_in_helpers_as_supermodule()` | Requires Helpers as supermodule |
| `hgit.is_git_worktree()` | Requires Git worktree setup |
| `not hgit.is_git_worktree()` | Not in a Git worktree |

### Dependencies and Tools

Tests requiring specific external tools or libraries:

| Condition | Reason |
| :------- | :------- |
| `hllmcli._check_llm_executable()` | LLM executable found |
| `not hllmcli._check_llm_executable()` | LLM executable not found |
| `shutil.which("pandoc") is None` | Pandoc not installed |
| `shutil.which("typst") is None` | Typst not installed |
| `hmarform.is_flowmark_available("global")` | Flowmark tool available |
| `hmarform.is_mdformat_available("library")` | mdformat tool available |
| `hmarform.is_prettier_available("global")` | Prettier tool available |
| `version.parse(jupytext.__version__) < version.parse("1.17.1")` | Jupytext version requirement |
| `_TABULATE_AVAILABLE` | Tabulate module available |

### Cloud and AWS Services

Tests requiring cloud service availability:

| Condition | Reason |
| :------- | :------- |
| `hserver.is_CK_S3_available()` | CK AWS S3 available |
| `not hserver.is_CK_S3_available()` | CK AWS S3 not available |

## Known Issues and References

Tests reference specific issues and tasks related to skip conditions:

- **CsfyTask8868**: macOS-specific Docker issues affecting tool rendering
  (pandoc, typst, prettier, markdown tools)
- **CsfyIssue8889**: macOS lint test failures requiring conditional skipping
- **Version incompatibilities**: Jupytext versions and markdown tool versions
  affect test availability

## Execution Contexts

Understanding when tests execute helps with debugging and maintenance.

### Tests Requiring Docker

These tests need Docker and container capabilities:

- Tests marked `requires_docker_in_docker`: Need docker children or sibling containers
- Tests checking `can_run_docker_from_docker()`: Require docker-in-docker capability
- Tests marked `requires_docker_in_docker`: Require docker socket access

### Tests Requiring Infrastructure

These tests depend on specific infrastructure being available:

- Tests marked `requires_ck_infra`: Need CK infrastructure access
- Tests marked `requires_ck_aws`: Need CK AWS connection
- Tests checking Csfy server: Require Csfy infrastructure

### Tests Requiring Development Environment

These tests need special setup or dependencies:

- Tests marked `need_dev_container`: Depend on dev container with extra dependencies
- Tests checking for tool availability: Skip if required tools are missing

### Tests Running Outside Containers

These tests specifically run outside Docker:

- Tests marked `no_container`: Invoke target tests running on host
- Tests checking `is_inside_docker()`: Require host execution
- Tests checking `is_git_worktree()`: Require local Git setup

## Test Organization Strategy

The skip conditions serve multiple purposes:

- **Isolation**: Keep platform/environment-specific tests from running in
  incompatible contexts
- **Reliability**: Prevent flaky tests by ensuring dependencies are available
- **Efficiency**: Skip expensive tests (slow, superslow) in quick feedback loops
- **Coverage**: Run different test suites on appropriate infrastructure
