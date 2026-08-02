# Plan: make `--topic`/`--skill`/`--rule` orthogonal to `--mode` in `cc_lint.py`

- **Drop the cross-exclusivity in `_main()`**: keep `--topic`/`--skill`/`--rule`
  mutually exclusive with *each other* (existing argparse group, unchanged),
  but remove `--mode`'s membership in the extra `num_exclusive` assert, so any
  of {`--topic`, `--skill`, `--rule`, default-inferred} can be combined with
  any of {`one_shot`, `session`, `stateless`}.

- **Generalize the incremental branch** (`_process_file_incrementally` /
  `_build_incremental_messages`), used when `--mode` is `session`/`stateless`,
  to build message chunks from whichever "what" was actually specified,
  instead of only the filename-inferred topic:
  - `--topic` (or default): unchanged — one chunk per H1 section across all of
    `topic_info["rules"]`'s files.
  - `--rule`: `hmarsele.extract_rule_from_file()`'s text, split into H1
    sections when it contains more than one (whole-file rule spec), else a
    single chunk (line-anchored spec already extracts one section).
  - `--skill`: a single, non-decomposed chunk equal to the existing
    `/{skill} {file_path}` slash-command string — kept as-is because a skill
    invocation is a command for Claude Code's own skill loader, not
    declarative rule prose to split.

- **Leave the `one_shot` path's prompts/execution untouched**: the existing
  `topic`/`skill`/`rule`/default branches in `_process_file()` that call
  `_build_prompt()` + `_run_claude_code()` (subprocess `cc` wrapper) keep their
  current prompt construction and behavior exactly as today; only their
  reachability changes (no longer blocked from coexisting with a non-default
  `--mode` elsewhere).

- **Factor the H1-splitting core out of file I/O**: split
  `_extract_h1_sections(rule_file)` into a pure `list[str]`-based helper plus
  a thin file-reading wrapper, so the same splitting logic can run over
  `extract_rule_from_file()`'s in-memory string (for `--rule`) without writing
  a temp file.

- **Tests** in `linters2/test/test_cc_lint.py`, covering `--mode` ×
  `{topic, skill, rule, default}` (the 3×4 = 12 combinations from task 2),
  each in two flavors against the same input file:
  - *fake*: mock `claude_agent_sdk.ClaudeSDKClient` (mirrors
    `Test_PromptSequencer_execute` in `dev_scripts_helpers/ai/test/test_cc_lib.py`)
    for `session`/`stateless`, and mock the subprocess call for `one_shot`;
    assert the right chunks/messages get built and dispatched.
  - *live*: `pytest.importorskip("claude_agent_sdk")` + class-level
    `@pytest.mark.skip(reason="Run manually: makes a real Claude Agent SDK
    call and costs tokens")`, cheapest model, `assertIn`-style loose checks —
    mirrors `Test_PromptSequencer_execute_end_to_end` in the same file.
  Also update `cc_lint.README.md`'s "Invariants"/architecture section, which
  currently documents "exactly one action mode is active" — that invariant is
  being intentionally removed.
