# Pyright Error Remediation Plan

**Source:** `pyright.txt` (1562 errors, 36 warnings)
**Date:** 2026-06-08

---

## Phase 1 — Mechanical Annotation Fixes 🟢 (2-3 hours)

### Cluster A: `str` ↔ `List[str]` (~30 errors)
Variable typed as `List[str]` assigned `str`, or vice versa. Pure copy-paste / naming collision.

**Fix:** One annotation swap per file. One minute each.

| Hotspot Files | Line Count |
|---|---|
| `config_root/config/config_.py` | 323, 341, 380 |
| `dev_scripts_helpers/preprocess_notes.py` | 557, 560 |
| `dev_scripts_helpers/lib_tasks_docker.py` | 1272-1317 (8 errors) |
| `helpers/hpandas_display.py` | 47-57 |
| `helpers/hpandas_analysis.py` | 442, 467 |

### Cluster B: `str | None` vs `str` (~110 errors)
Function declared `-> str` returns `str | None`, or `str | None` argument passed where `str` expected. Three sub-patterns:
- Missing return path → add `Optional[str]` to return type
- Caller passes None → add `assert x is not None` or fix call
- Hardcoded `None` passed to `str` param → fix call site

**Hotspots:** `hparquet.py`, `hprint.py`, `hs3.py`, `hpandas_utils.py`, `hpytest.py`, `hunit_test.py`, `repo_config_utils.py`, `hversion.py`, many `test_*.py` files.

### Cluster C: `Literal['echo']` vs `int` (2 errors)
`dev_scripts_helpers/git/gup.py:53,65` — string log level passed where `int` expected.

**Fix:** Change `'echo'` to the numeric log level constant.

---

## Phase 2 — Possibly-Unbound Variables 🟡 (2-3 hours)

### Cluster D (~120 errors across 40 files)

**Pattern:** Variable assigned inside conditional branches, one branch skips it, then used after the block.

**Fix:** Initialize before the conditional, then assert not None.

**Hotspots (10+ errors each):**
- `helpers/hgoogle_drive_api.py` — `goasea`, `godisc`, `gspread` lazy imports
- `helpers/hunit_test.py` — `pd`, `np`, `plt` lazy imports
- `helpers/hdatetime.py` — `pytz` lazy import
- `helpers/henv.py` — `psutil` lazy import

**Quick sub-fix for lazy imports (~40 errors):** `# type: ignore[possibly-unbound]` on the import line.

---

## Phase 3 — Pandas Type Narrowing 🟡 (3-5 hours, ~310 errors)

### Cluster E: `Timestamp | NaTType` vs `Timestamp` (~120 errors)
Pandas returns `Timestamp | NaTType`, code expects `Timestamp`.

**Hotspot files (30+ errors each):** `test_hdatetime.py`, `test_hparquet.py`, `test_hpandas_transform.py`.

### Cluster F: `Series | DataFrame` vs `DataFrame` (~60 errors)
Pandas groupby/apply/window ops return unions.

### Cluster G: `list[str]` vs pandas `Axes | None` (~80 errors)
Passing lists to `.loc[..., columns=]` / `.drop(labels=)`.

### Cluster H: Cannot access `freq`/`levels`/`year`/`month` on `Index` (~50 errors)
Pandas stubs don't expose these on the abstract `Index` base class — they exist at runtime on `DatetimeIndex`/`MultiIndex`.

**Recommended approach:** Add project-wide pyright exclusions for pandas stubs rather than 310 individual `# type: ignore` comments.

---

## Phase 4 — Logger / Logging Attributes 🟠 (1 hour, ~80 errors)

### Cluster I: `logger.trace` / `logging.TRACE` not known (~65 errors)
Custom `trace()` log level added at runtime, not in typeshed. Concentrated in `hcache_simple.py` (50+ errors).

### Cluster J: `hlogging.X` not known (~15 errors)
Functions (`shutup_chatty_modules`, `test_logger`, `set_v2_formatter`, etc.) moved/renamed.

**Fix:** Bulk `# type: ignore[attr-defined]` or add a project-wide exclusion.

---

## Phase 5 — S3FileSystem Stub Mismatch 🟠 (1-2 hours, ~35 errors)

### Cluster K
s3fs type stubs don't match actual runtime API. Methods like `open()`, `ls()`, `glob()`, `exists()`, `put()`, `get()`, `rm()` are all reported as unknown.

**Best fix:** Project-wide `reportAttributeAccessIssue = false` for `s3fs` module — more efficient than 35 individual `# type: ignore`.

---

## Phase 6 — Import / Module Resolution 🔴 (2-4 hours, ~45 errors)

### Cluster L: Unresolvable imports (~20 errors)
`omegaconf`, `ml_collections`, `pyannotate_runtime`, `junitparser`, `dill`, `pypdf`, `pygame`, `pysftp`, `psycopg2`, `asana`, `git_filter_repo`, `helpers.user_credentials`.

**Fix:** Most are optional/script-specific deps. One `# type: ignore[import]` per file.

### Cluster M: Module attribute not known (~25 errors)
`github.Repository`, `boto3.session`, `hydra.core`, `IPython.display`, `pyarrow.lib`.

**Fix:** Different import path or `# type: ignore`.

---

## Phase 7 — Structural Type Fixes 🔴 (3-5 hours, ~50 errors)

### Cluster N: Override / method signature mismatches (~20 errors)
`hjoblib.py` (4 overrides of `StoreBackendBase`), `test_hobject.py` (parameterized test base class), `htqdm.py`, `hsql_test.py`, `docs_mkdocs/check_mkdocs_links.py`.

**Fix:** Adjust signatures to match parent class. Requires understanding the override contract.

### Cluster O: `invoke` import restructuring (~15 errors)
`from invoke import task` → `from invoke.tasks import task`
`MockContext` / `Result` → new homes per invoke version.

### Cluster P: OpenAI/Anthropic/LLM API typing (~20 errors)
`hchatgpt.py`, `hllm.py`, `hllm_cost.py`. SDK stubs don't match usage.

**Fix:** Per-method investigation + stub updates or type: ignore.

---

## Effort Summary

| Priority | Errors | Time | Risk |
|----------|--------|------|------|
| Phases 1-2 (A-D) | ~260 | 4-6 hr | Mechanical, low risk |
| Phase 3 (E-H) | ~310 | 3-5 hr | Better solved with project-wide pandas exclusion |
| Phase 4 (I-J) | ~80 | 1 hr | Mechanical, low risk |
| Phase 5 (K) | ~35 | 1 hr | Better solved with project-wide s3fs exclusion |
| Phase 6 (L-M) | ~45 | 2-4 hr | Mixed, some investigation needed |
| Phase 7 (N-P) | ~50 | 3-5 hr | Needs code understanding |
| **Total** | **~780 non-warning errors** | **~15-25 hr** | |

**Quick win:** Phases 1-4 cover ~650 errors (80% of total) with mechanical one-line fixes in ~10 hours.

**Alternative strategy:** Add project-wide pyright exclusions for `pandas` and `s3fs`, which eliminates ~350 errors (Clusters E/F/G/H/K) with zero code changes. Then fix the remaining ~430 errors mechanically.