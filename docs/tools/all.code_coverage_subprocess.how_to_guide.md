<!-- toc -->

- [Enhanced Pytest Coverage for Subprocesses and Docker](#enhanced-pytest-coverage-for-subprocesses-and-docker)
  * [Overview](#overview)
  * [Problem & Solution](#problem--solution)
    + [The Challenge:](#the-challenge)
    + [The Solution:](#the-solution)
  * [Setup Guide](#setup-guide)
    + [Prerequisites](#prerequisites)
    + [Step 1: Configure Coverage for Parallel Execution](#step-1-configure-coverage-for-parallel-execution)
    + [Step 2: Install Coverage Hooks](#step-2-install-coverage-hooks)
    + [Step 3: Prepare Coverage Data Directory](#step-3-prepare-coverage-data-directory)
    + [Step 4: Update Docker Containers (if applicable)](#step-4-update-docker-containers-if-applicable)
    + [Step 5: Run Tests with Coverage](#step-5-run-tests-with-coverage)
    + [Step 6: Collect and Merge Coverage Data](#step-6-collect-and-merge-coverage-data)
    + [Step 7: View Coverage Report on web browser](#step-7-view-coverage-report-on-web-browser)
  * [Common Usage Patterns in test files](#common-usage-patterns-in-test-files)
    + [Simple Subprocess Test](#simple-subprocess-test)
    + [Docker Container Test](#docker-container-test)

<!-- tocstop -->

# Enhanced Pytest Coverage for Subprocesses and Docker

## Overview

This guide extends `coverage run` to capture comprehensive test data from
**Python subprocesses** and **Dockerized applications**. By implementing
**coverage hooks** and **parallel data collection**, you can achieve complete
test coverage reporting across distributed processes that are typically excluded
from standard coverage metrics.

## Problem & Solution

### The Challenge:

Traditional pytest coverage collection fails when tests spawn Python
subprocesses or execute code within Docker containers. This results in
significant coverage gaps, as child processes and containerized code execution
don't contribute to your coverage reports, leading to artificially low and
misleading coverage metrics.

### The Solution:

- **Automatic Process Instrumentation**: Deploy coverage hooks that
  automatically instrument all Python processes, including subprocesses and
  container-based execution
- **Parallel Data Collection**: Enable concurrent coverage data collection from
  multiple processes without conflicts
- **Unified Report Generation**: Aggregate coverage data from all sources into
  comprehensive, actionable reports

## Setup Guide

### Prerequisites

- **Python project** with **pytest tests**.
- **Docker** installed.
- **`coverage`, `pytest`, `pytest-cov`** packages.
- Access to modify **Docker containers**.

### Step 1: Configure Coverage for Parallel Execution

- Update `.coveragerc` in **project root**:

  ```ini
  [run]
  branch = True
  parallel = True
  concurrency = multiprocessing
  sigterm = True

  [paths]
  source =
      .
      /app
  ```

### Step 2: Install Coverage Hooks

- Run:
  ```bash
  python -c "import helpers.hcoverage as hcovera; hcovera.inject()"
  ```
- Example Log:
  ```INFO:helpers.hcoverage:Installed coverage hook to /home/maddev/src/venv/client_venv.helpers/lib/python3.10/site-packages/coverage.pth via sudo tee
  ```

### Step 3: Prepare Coverage Data Directory

- Run:
  ```bash
  python3 -c "import helpers.hcoverage as hcovera; hcovera.coverage_subprocess_commands()"
  ```
- Or manually:
  ```bash
  mkdir -p coverage_data
  cp .coveragerc coverage_data/.coveragerc
  chmod 644 coverage_data/.coveragerc
  ```

### Step 4: Update Docker Containers (if applicable)

- Add to **Dockerfile**:

```dockerfile
FROM python:3.8
WORKDIR /app

# Install coverage and testing dependencies
RUN pip install --no-cache-dir coverage pytest pytest-cov

# Create coverage data directory with proper permissions
RUN mkdir -p /app/coverage_data && chmod 777 /app/coverage_data

# Copy coverage configuration
COPY .coveragerc /app/coverage_data/.coveragerc
ENV COVERAGE_PROCESS_START=/app/coverage_data/.coveragerc

# Install coverage hook for automatic startup
RUN python -c "\
import site, os; \
site_dir = site.getsitepackages()[0]; \
pth_file = os.path.join(site_dir, 'coverage.pth'); \
with open(pth_file, 'w') as f: \
    f.write('import coverage; coverage.process_startup()')"
```

- Not required if base image is built through `hdocker.build_container_image()`

### Step 5: Run Tests with Coverage

- Run:
  ```bash
  coverage run --parallel-mode -m pytest your_test_file.py
  ```
- Example Output:

  ```bash
  ================================================================================ 1 failed, 2 passed, 1 skipped in 21.87s ================================================================================
  (client_venv.helpers) maddev@pop-os:~/src/helpers1$
  ```

### Step 6: Collect and Merge Coverage Data

- Run:
  ```bash
  python3 -c "import helpers.hcoverage as hcovera; hcovera.coverage_combine()"
  ```
- Or manually:
  ```bash
  cp coverage_data/.coverage.* . 2>/dev/null || true
  coverage combine
  coverage report
  ```
- Example Output for `llm_transform.py`
  ```bash
  (client_venv.helpers) maddev@pop-os:~/src/helpers1$ python3 -c "import helpers.hcoverage as hcovera; hcovera.coverage_combine()"
  ... Combined data file .coverage.5a2d2b4fdfe3.1.XrhVQNTx
  ... Skipping duplicate data .coverage.cdf5b8f26c75.1.XFGOFeyx
  ... Combined data file .coverage.e03acce33422.1.XtfLXHQx
  ... Combined data file .coverage.pop-os.46350.XygSLfNx
  ... Combined data file .coverage.pop-os.47307.XkYJoatx
  ... Combined data file .coverage.pop-os.47484.XaosHvKx
  ... Combined data file .coverage.pop-os.47752.XCCWcfOx
  ... Combined data file .coverage.pop-os.47936.XvEsXxjx
  ... Name                                                   Stmts   Miss Branch BrPart  Cover
  ... ----------------------------------------------------------------------------------------
  ... /etc/python3.10/sitecustomize.py                           5      1      0      0    80%
  ... __init__.py                                                0      0      0      0   100%
  ... conftest.py                                               74     33     16      6    52%
  ... dev_scripts_helpers/__init__.py                            0      0      0      0   100%
  ... dev_scripts_helpers/documentation/__init__.py              0      0      0      0   100%
  ... dev_scripts_helpers/documentation/lint_notes.py          214    188     76      1     9%
  ... dev_scripts_helpers/llms/__init__.py                       0      0      0      0   100%
  ... dev_scripts_helpers/llms/dockerized_llm_transform.py      32      4      8      4    80%
  ... dev_scripts_helpers/llms/llm_prompts.py                  463     47     48     12    86%
  ... dev_scripts_helpers/llms/llm_transform.py                139     51     36     15    60%
  ... dev_scripts_helpers/llms/test/__init__.py                  0      0      0      0   100%
  ... dev_scripts_helpers/llms/test/test_llm_transform.py       67     15      6      1    75%
  ... helpers/__init__.py                                        0      0      0      0   100%
  ... helpers/hcoverage.py                                      67     50     16      1    22%
  ... helpers/hdbg.py                                          394    258    136     22    31%
  ... helpers/hdocker.py                                       525    387     90      7    25%
  ... helpers/henv.py                                          216     91     46      4    50%
  ... helpers/hgit.py                                          573    458    130      3    17%
  ... helpers/hintrospection.py                                125    102     48      0    13%
  ... helpers/hio.py                                           333    228    118     12    27%
  ... helpers/hlatex.py                                         36     28      4      0    20%
  ... helpers/hlogging.py                                      292    155     90     21    42%
  ... helpers/hmarkdown.py                                     501    434    194      0    10%
  ... helpers/hopenai.py                                       233    152     62      5    31%
  ... helpers/hparser.py                                       206    119     64      5    39%
  ... helpers/hprint.py                                        421    230    134     14    42%
  ... helpers/hserver.py                                       424    227    134     11    39%
  ... helpers/hsystem.py                                       459    309    140      7    28%
  ... helpers/htimer.py                                        116     69     14      2    38%
  ... helpers/hunit_test.py                                    782    566    190     20    25%
  ... helpers/hversion.py                                       85     24     14      3    65%
  ... helpers/hwall_clock_time.py                               40     19     10      1    44%
  ... helpers/hwarnings.py                                      26      4      4      1    83%
  ... helpers/repo_config_utils.py                             153     83     28      6    43%
  ... ----------------------------------------------------------------------------------------
  ... TOTAL                                                   7001   4332   1856    184    33%
  ```

### Step 7: View Coverage Report on web browser

- Generate the HTML report:

  ```bash
  coverage html
  ```

- Serve it on a local web server:

  ```bash
  python3 -m http.server --directory htmlcov 8000
  ```

- In your browser, navigate to: [http://localhost:8000](http://localhost:8000)

## Common Usage Patterns in test files

### Simple Subprocess Test

```python
def test_subprocess_script():
    result = subprocess.run([sys.executable, "my_script.py"], capture_output=True)
    assert result.returncode == 0
```

- Works with `hsystem.system`

### Docker Container Test

```python
def test_docker_script():
    base_cmd = hdocker.get_docker_base_cmd(use_sudo=False)
    docker_cmd = base_cmd + ["my-image", "python", "script.py"]
    result = subprocess.run(docker_cmd, capture_output=True)
    assert result.returncode == 0
```

- Considers "my-image" to be built with `hdocker.build_container_image()`
