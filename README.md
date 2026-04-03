# helpers — Causify’s Python Toolkit for High-Leverage Engineering

`helpers` is a public collection of Python utilities, configuration patterns, and developer tooling extracted from real production work at Causify.

It exists for one reason:

> **Make engineering repeatable.**  
> Turn "tribal knowledge" into composable primitives: less glue code, fewer one-off scripts, and more reliable systems.

This repo is useful in three common contexts:

- **Platform/product engineering**: predictable building blocks for I/O, debugging, system operations, Git/Docker, dates/time, dataframes, and more.
- **Repo hygiene at scale**: linting, import validation, CI utilities, pre-commit workflows; things large repos need to stay healthy.
- **LLM/agentic workflows**: lightweight wrappers for completions, structured outputs, caching modes, and cost tracking.

## One-minute map (how the repo fits together)

```mermaid
flowchart LR
 subgraph Lib["`**Python Library** (helpers/)`"]
    direction TB
        Core["Core Helpers<br>(hdbg, hio, hsystem, hgit, hdocker, hdatetime, …)"]
        Data["Data Helpers<br>(hpandas and related modules)"]
        LLM["LLM & Agentic Helpers<br>(hllm, hllm_cost, hllm_cli, hchatgpt, …)"]
  end
 subgraph Config["`**Configuration Patterns** (config_root/)`"]
        Conf["Env-aware configuration objects<br>and builders"]
  end
 subgraph Tooling["`**Tooling & Automation**`"]
        Scripts@{ label: "Dev Scripts<br/>(dev_scripts_helpers/)" }
        Import@{ label: "Import Hygiene<br/>(import_check/)" }
        Linters@{ label: "Linting Framework<br/>(linters/, linters2/)" }
        Tasks@{ label: "Repo Tasks & Automation<br/>(tasks.py, invoke.yaml)" }
  end
 subgraph Docs["`**Documentation & Examples**`"]
        Human@{ label: "Human Docs<br/>(docs/)" }
        Mk@{ label: "MkDocs Site<br/>(docs_mkdocs/)" }
        NB@{ label: "Tutorial Notebooks<br/>(helpers/notebooks/)" }
  end
 subgraph CI["`**Continuous Integration & Hygiene**`"]
        GH@{ label: "GitHub Workflows<br/>(.github/)" }
        PC@{ label: "Pre-commit & Scanning<br/>(.pre-commit-config.yaml, semgrep, …)" }
  end
    Core -- provides base utilities to --> Conf
    Data -- feeds data into --> Conf
    LLM -- adds AI logic to --> Conf
    Scripts -- triggers tasks in --> GH
    Import -- enforces rules in --> GH
    Linters -- runs in --> GH
    Tasks -- executes workflows in --> GH
    Human -- documented in --> GH
    Mk -- deployed via --> GH
    NB -- tested in --> GH
    PC -- validates via --> GH

    Core@{ shape: rounded}
    Data@{ shape: rounded}
    LLM@{ shape: rounded}
    Conf@{ shape: rect}
    Scripts@{ shape: rect}
    Import@{ shape: rect}
    Linters@{ shape: rect}
    Tasks@{ shape: rect}
    Human@{ shape: doc}
    Mk@{ shape: doc}
    NB@{ shape: doc}
    GH@{ shape: rect}
    PC@{ shape: rect}
     Core:::lib
     Data:::lib
     LLM:::lib
     Conf:::config
     Scripts:::tooling
     Import:::tooling
     Linters:::tooling
     Tasks:::tooling
     Human:::docs
     Mk:::docs
     NB:::docs
     GH:::ci
     PC:::ci
    classDef lib fill:#e0f7fa,stroke:#0097a7,stroke-width:2px,color:#004d40
    classDef config fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#795548
    classDef tooling fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px,color:#4a148c
    classDef docs fill:#c5cae9,stroke:#3949ab,stroke-width:2px,color:#1a237e
    classDef ci fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20
````

## Why this exists (the philosophy)

Most engineering orgs accumulate dozens of tiny scripts and helper snippets. Over time that becomes:

- duplicated logic across repos,
- inconsistent behavior,
- hard-to-test workflows,
- brittle operations.

`helpers` is the opposite: small, well-scoped primitives that are easy to discover and safe to reuse. The code is intentionally "boring"; because boring tools are what make fast teams.

## Micro-examples

These examples are deliberately small. The repo is optimized for everyday leverage.

### 1) Defensive checks & clear failures

```python
import helpers.hdbg as hdbg

hdbg.dassert_eq(2 + 2, 4)
hdbg.dassert(10 > 3, "Math still works")
```

### 2) Safe system command execution (without subprocess boilerplate)

```python
import helpers.hsystem as hsystem

out = hsystem.system_to_string("python --version")
print(out)
```

### 3) Simple JSON I/O helpers

```python
import helpers.hio as hio

payload = {"hello": "world"}
hio.to_json("tmp.json", payload)

loaded = hio.from_json("tmp.json")
print(loaded)
```

### 4) DataFrame utilities (example: convert DF to JSON string)

```python
import pandas as pd
import helpers.hpandas as hpandas

df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
print(hpandas.convert_df_to_json_string(df))
```

### 5) LLM structured output + cost tracking (agentic building blocks)

`helpers.hllm` supports providers like OpenAI and OpenRouter (via `openrouter/<model>`). It also supports caching modes and structured output.

```python
from pydantic import BaseModel

import helpers.hllm as hllm
import helpers.hllm_cost as hllmcost

class Summary(BaseModel):
    summary: str
    risks: list[str]

# Track cost for a specific provider/model.
tracker = hllmcost.LLMCostTracker(provider_name="openai", model="gpt-4o-mini")

result = hllm.get_structured_completion(
    "Summarize key risks of shipping without observability.",
    response_format=Summary,
    system_prompt="Be concise and practical.",
    model="gpt-4o-mini",
    cache_mode="DISABLE_CACHE",
    print_cost=True,
    cost_tracker=tracker,
)

print(result.summary)
print("Cost so far ($):", tracker.get_current_cost())
```

## What’s in here (a guided tour)

### Core Python helpers (`helpers/`)

The main Python library lives in `helpers/`. Many modules follow the `h<name>.py` naming pattern (e.g., `hdbg.py`, `hio.py`, `hsystem.py`) to make discovery fast and avoid collisions.

A few high-signal examples:

- `helpers/hdbg.py`: defensive checks and assertions
- `helpers/hsystem.py`: safe system command execution
- `helpers/hio.py`: practical file I/O helpers
- `helpers/hgit.py`: git utilities
- `helpers/hdocker.py`: docker helpers
- `helpers/henv.py`: environment utilities
- `helpers/hdatetime.py`: date/time utilities

### Data utilities (`hpandas` and friends)

`helpers/hpandas.py` re-exports a suite of pandas helpers implemented across `hpandas_*` modules (conversion, compare, display, cleaning, assertions, IO, etc.). This makes the most common "pandas hygiene" tasks consistent across projects.

### LLM & agentic utilities

This repo includes lightweight building blocks for LLM workflows:

- `helpers/hllm.py`: completions + structured outputs + caching modes
- `helpers/hllm_cost.py`: cost tracking and provider cost utilities (incl. `LLMCostTracker`)
- `helpers/hllm_cli.py`: CLI-oriented LLM workflows
- `helpers/hchatgpt.py` / `helpers/hchatgpt_instructions.py`: utilities around assistants/instructions workflows

Tutorial notebooks live under `helpers/notebooks/` (see `hllm.tutorial.py`).

### Config patterns (`config_root/`)

Reusable configuration patterns: config objects/builders and environment-aware configuration.

### Tooling and repo hygiene

This repo also ships "how we keep repos healthy" primitives:

- `dev_scripts_helpers/`: automation scripts for common workflows
- `import_check/`: import hygiene validation
- `linters/`, `linters2/`: lint framework and configs
- `.github/`: CI workflows and checks
- `.claude/`: Claude Code configuration and hooks
- `CLAUDE.md`: Architecture overview and development patterns for Claude Code
- `conftest.py`: Pytest configuration and shared test fixtures
- `instr.md`: Development instructions and task specifications
- `main_pytest.py`: Main pytest runner and test execution controller
- `tasks.py`: Entry point for pyinvoke task automation system
- pre-commit and scanning configs (`.pre-commit-config.yaml`, `.semgrepignore`, etc.)

## Design principles (what makes this repo useful)

- **Small modules > big frameworks**
  Helpers should be composable and easy to understand.
- **Safety by default**
  Defensive checks, predictable failures, sensible defaults.
- **Fast discovery**
  Naming conventions encourage "find the right tool quickly."
- **Reproducibility**
  If it matters, it should be runnable in CI and documented.
- **Low dependency footprint**
  Dependencies are added only when they buy real leverage.

## Getting started

### Use as a git submodule (common in larger repos)

```bash
git submodule add https://github.com/causify-ai/helpers.git helpers_root
git submodule update --init --recursive
```

### Use locally (development / experimentation)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

If contributing, enable pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Tests & quality checks

Run tests:

```bash
pytest -q
# or
python main_pytest.py
```

Run pre-commit:

```bash
pre-commit run -a
```

List repo automation tasks (if using invoke):

```bash
pip install invoke
invoke -l
```

## Documentation

Human docs live under `docs/`. A browsable site is maintained under `docs_mkdocs/`.

Serve MkDocs locally:

```bash
pip install mkdocs mkdocs-material
cd docs_mkdocs
mkdocs serve
```

## Contributing

- Keep changes small and reviewable.
- Add tests when behavior changes.
- Prefer reusable utilities over one-off scripts.
- Keep backwards compatibility in mind for downstream consumers.

## Security

This repo includes secret-scanning and standard hygiene.
**Do not commit secrets.** If you suspect a leak: rotate credentials and open an incident.

## License

See [`LICENSE`](LICENSE).
