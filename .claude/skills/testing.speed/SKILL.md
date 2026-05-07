---
description: Reference rules for test speed classification and environment-conditional skipping. Load when adding speed markers, classifying tests by duration, or gating tests to specific environments.
---

- This file contains rules for test speed classification and
  environment-conditional skipping

# Test Speed Tiers

## Speed Markers
- Every test is classified by expected execution time using pytest markers
- Unmarked tests are **fast** by default (5 s timeout)
- Add `@pytest.mark.slow` for tests that take up to 30 s
- Add `@pytest.mark.superslow` for tests that take up to 3600 s
- Never let a fast test grow past its timeout: `pytest-timeout` enforces it
  loudly
  ```python
  import pytest
  import helpers.hunit_test as hunitest

  class TestFoo1(hunitest.TestCase):
      def test_fast1(self) -> None:
          # No marker — must complete in under 5 s.
          ...

      @pytest.mark.slow
      def test_slow1(self) -> None:
          # Runs only in slow suite; up to 30 s.
          ...

      @pytest.mark.superslow
      def test_superslow1(self) -> None:
          # Runs only in superslow suite; up to 3600 s.
          ...
  ```

# Environment-Conditional Skipping

## Skip Helpers
- Use helpers from `helpers/hunit_test_utils.py` to gate tests to specific
  environments instead of hand-rolling `pytest.mark.skipif` predicates
- Call the function at the top of the test method: it raises `pytest.skip()`
  internally

  | Function | Skips unless |
  | :------- | :----------- |
  | `hunteuti.execute_only_on_ci()` | Running inside CI (GitHub Actions) |
  | `hunteuti.execute_only_on_mac()` | Running on macOS |
  | `hunteuti.execute_only_on_dev_csfy()` | Running on the CSFY dev machine |
  | `hunteuti.execute_only_in_target_repo(name)` | Running in a repo whose short name matches `name` |
  ```python
  import helpers.hunit_test_utils as hunteuti

  class TestFoo1(hunitest.TestCase):
      def test_ci_only1(self) -> None:
          hunteuti.execute_only_on_ci()
          # Only runs in CI.
          ...

      def test_helpers_repo1(self) -> None:
          hunteuti.execute_only_in_target_repo("helpers")
          # Only runs in the helpers repo.
          ...
  ```

# Infrastructure Markers

## Pytest Markers for Infrastructure Requirements
- Use these decorators when a test needs specific infrastructure that is not
  always available; the test is skipped automatically when the requirement is
  not met

  | Marker | Skips unless |
  | :----- | :----------- |
  | `@pytest.mark.requires_ck_infra` | Running inside CK infrastructure |
  | `@pytest.mark.requires_ck_aws` | CK AWS connection is available |
  | `@pytest.mark.requires_docker_in_docker` | Docker-in-Docker is available (sibling/child containers) |
  | `@pytest.mark.no_container` | Running outside a container (invoke target tests on the host) |

  ```python
  import pytest
  import helpers.hunit_test as hunitest

  @pytest.mark.requires_ck_infra
  class TestNeedsInfra1(hunitest.TestCase):
      def test_fetch1(self) -> None:
          # Skipped unless running inside CK infrastructure.
          ...

  class TestMixed1(hunitest.TestCase):
      @pytest.mark.requires_ck_aws
      def test_s3_upload1(self) -> None:
          # Skipped unless CK AWS connection is available.
          ...
  ```

- Markers can be applied at class level (all methods inherit) or method level
