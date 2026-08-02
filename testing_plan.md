# Testing `lint_cc.py` / `cc_lib.py` Without Spending Tokens

## Context

`linters2/lint_cc.py --apply_incrementally` drives real Claude Code sessions
via `dev_scripts_helpers/ai/cc_lib.py`'s `PromptSequencer`, which wraps
`claude_agent_sdk.ClaudeSDKClient`. Any run that reaches
`PromptSequencer.execute()` costs real API tokens. In the just-completed
Phase 1 work I added new logic to `cc_lib.py` — the `_make_file_scope_guard()`
callback and five new `PromptSequencer.__init__()` kwargs (`model`,
`disallowed_tools`, `setting_sources`, `target_file`, `can_use_tool`) — none
of which has test coverage yet. The user wants to know how to exercise this
script and its new logic without incurring API cost. This plan is test-only:
no production code in `lint_cc.py` or `cc_lib.py` changes.

## What's Already Free Today (no new code)

- `./linters2/lint_cc.py --files <path> --dry_run` never reaches the network
  on either code path: `_run_claude_code()` returns before
  `hsystem.system(cmd)` (`linters2/lint_cc.py:332-336`), and
  `_process_file_incrementally()` returns before constructing a
  `PromptSequencer` (`linters2/lint_cc.py:422-432`). Use this to inspect the
  exact prompts/messages that would be sent.
- `pytest dev_scripts_helpers/ai/test/test_cc_lib.py linters2/test/test_lint_cc.py -q`
  — the existing 32 tests are pure-function/attribute checks, ~1-2s, zero
  network calls, already verified passing after the Phase 1 changes.

## New Tests to Add (still zero tokens)

Reuse the existing `hunitest.TestCase` + prepare/run/check style already in
both files. No `pytest-asyncio` is installed, so drive async code with
`asyncio.run(...)`, matching the pattern already used in
`linters2/lint_cc.py:472` and `dev_scripts_helpers/ai/cc_script.py:247`.

### 1. `dev_scripts_helpers/ai/test/test_cc_lib.py`

Add imports: `asyncio`, `from unittest import mock`, and `import
claude_agent_sdk` (placed after the existing `pytest.importorskip(...)` at
line 17, alongside the existing `dshaccli` import).

**New class `Test_make_file_scope_guard`** (insert before
`class TestPromptSequencer`, mirroring source order — the guard function
precedes the class in `cc_lib.py`). Shared helper:
```python
def helper(self, target_file, tool_name, tool_input):
    guard = dshaccli._make_file_scope_guard(target_file)
    return asyncio.run(guard(tool_name, tool_input, None))
```
Test methods:
- Same file, modifying tool (`"Edit"`) → `PermissionResultAllow`.
- Different file, modifying tool → `PermissionResultDeny`; assert the target
  filename appears in `result.message`.
- Loop over the file-modifying tools (`"Edit"`, `"Write"`, `"NotebookEdit"`,
  `"MultiEdit"`) with a mismatched path → deny for each.
- Non-modifying tool (`"Read"` or `"Bash"`) on a different/absent file →
  always allow.
- `tool_input` missing `"file_path"` entirely, and `tool_input["file_path"]
  == ""` → allow in both cases (covers the falsy short-circuit at
  `cc_lib.py:92-93`).
- Relative `target_file` vs. absolute-equivalent `file_path` → allow (covers
  the `os.path.abspath()` normalization).

**New methods appended to `class TestPromptSequencer`** (after existing
`test4`, continuing the numeric suffix convention):
- Explicit `model`, `disallowed_tools`, `setting_sources` → stored verbatim
  on the instance.
- Omitted `setting_sources`/`disallowed_tools` → default to `[]` (distinct
  from `test1`, which doesn't check these fields).
- `target_file` set, no `can_use_tool` → `sequencer.can_use_tool` is
  non-`None`, callable, and behaves like the guard from
  `_make_file_scope_guard` (one sanity call denying a mismatched file).
- Explicit `can_use_tool` + `target_file` both set → the explicit callback
  wins (identity check `sequencer.can_use_tool is my_callback`).
- Neither `target_file` nor `can_use_tool` → `sequencer.can_use_tool is
  None`.

### 2. Mocked `execute()` test — `dev_scripts_helpers/ai/test/test_cc_lib.py`

New class `Test_PromptSequencer_execute`, placed after `TestPromptSequencer`.

Define a small test-local fake (not `AsyncMock`, which can't cleanly emulate
an async-generator method) directly above the class:
```python
class _FakeClaudeSDKClient:
    def __init__(self, responses_by_call):
        self._responses_by_call = responses_by_call
        self.queried_prompts = []
        self.aenter_called = False
        self.aexit_called = False

    async def __aenter__(self):
        self.aenter_called = True
        return self

    async def __aexit__(self, *exc_info):
        self.aexit_called = True
        return False

    async def query(self, prompt):
        self.queried_prompts.append(prompt)

    async def receive_response(self):
        idx = len(self.queried_prompts) - 1
        for message in self._responses_by_call[idx]:
            yield message
```

Patch only `claude_agent_sdk.ClaudeSDKClient` via
`mock.patch("claude_agent_sdk.ClaudeSDKClient")` — this is the correct call
site since `cc_lib.py` does `import claude_agent_sdk` and references
`claude_agent_sdk.ClaudeSDKClient` dynamically (never a `from...import`).
Do **not** mock `ClaudeAgentOptions` — it's a plain dataclass with no I/O;
let it construct for real and assert on its actual fields.

Test body (one test is enough):
1. Build two real `claude_agent_sdk.AssistantMessage(content=[TextBlock(...)],
   model="claude-test")` fixtures.
2. `fake_client = _FakeClaudeSDKClient(responses_by_call=[[msg1], [msg2]])`.
3. Construct `PromptSequencer(allowed_tools=..., disallowed_tools=...,
   permission_mode="acceptEdits", cwd=..., model="claude-test-model",
   setting_sources=["project"], target_file="/tmp/target.py",
   print_output=False)` — `print_output=False` avoids stdout noise from
   `print_message()`.
4. `with mock.patch("claude_agent_sdk.ClaudeSDKClient") as mock_client_cls:
   mock_client_cls.return_value = fake_client;
   asyncio.run(sequencer.execute(["prompt A", "prompt B"]))`.
5. Assert: `mock_client_cls.assert_called_once()` (single session reused
   across prompts); the `options` kwarg passed to it has the expected
   `allowed_tools`/`disallowed_tools`/`permission_mode`/`model`/
   `setting_sources`, and `can_use_tool is sequencer.can_use_tool`;
   `fake_client.aenter_called`/`aexit_called` are both `True`;
   `fake_client.queried_prompts == ["prompt A", "prompt B"]`;
   `sequencer._prompts_executed == 2`; `sequencer.get_last_response() != ""`
   (do not pin the exact string — it's an SDK repr, not part of `cc_lib.py`'s
   contract).

### 3. `linters2/test/test_lint_cc.py` — one regression guard

Add imports `argparse` and `helpers.hio as hio`. New class
`Test_process_file_apply_incrementally`, placed after
`Test_extract_h1_sections`:
```python
class Test_process_file_apply_incrementally(hunitest.TestCase):
    def test1(self) -> None:
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        args = argparse.Namespace(
            apply_incrementally=True,
            skill="",
            rule="",
            topic="",
            dry_run=True,
            model="",
        )
        rc, topic_info = llincc._process_file(file_path, args)
        self.assertEqual(rc, 0)
        self.assertIn("role", topic_info)
        self.assertIn("rules", topic_info)
        self.assertIn("templates", topic_info)
        self.assertGreater(len(topic_info["rules"]), 0)
```
This guards the Phase 1 fix that `topic_info` stays populated on the
`--apply_incrementally` branch (needed for post-processing). It stays
network-free because `dry_run=True` makes `_process_file_incrementally()`
return before touching `PromptSequencer`.

## Verification

```bash
pytest dev_scripts_helpers/ai/test/test_cc_lib.py linters2/test/test_lint_cc.py -q
```
Run from repo root (both files resolve `.claude/skills/...` relative to
cwd). Expect ~47 tests total (32 existing + ~15 new), completing in a couple
of seconds, with zero network calls and no `ANTHROPIC_API_KEY` required.
