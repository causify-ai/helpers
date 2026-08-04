# Phase 4: Checkpointing and Resume

## Journal Every Chunk Outcome

- Problem:
  - The observed run died partway through the sequence
  - Completed work was neither attributed nor resumable
  - `dev_scripts_helpers/ai/cc_lib.py` already defines `save_session_log()`, but
    `linters2/lint_cc.py` never calls it
- Change:
  - Write a JSON journal keyed by (`file_path`, `chunk_title`) holding:
    - `status`: one of `done`, `no_op`, `failed`, `skipped`
    - `cost_usd` and `num_turns`
  - Add `--resume` to skip entries already marked `done` or `no_op`
  - Reuse or extend `save_session_log()` rather than adding a parallel writer
- Done when: killing a run and rerunning with `--resume` continues where it
  stopped

## Bound Each Chunk

- Problem:
  - No per-prompt turn limit, so one rule can loop indefinitely
- Change:
  - Set `ClaudeAgentOptions.max_turns` to a small value per chunk

# Phase 5: Observability

## Report Real Cost and Usage

- Problem:
  - `PromptSequencer.execute()` concatenates `str(message)` for every message,
    including full tool inputs, and retains the result only to log its length
- Change:
  - Drop the concatenation
  - Capture the fields already carried by `ResultMessage`:
    - `total_cost_usd`
    - `usage`
    - `num_turns`
    - `is_error`
    - `terminal_reason`
  - Surface them from `get_execution_stats()` and in the journal
- Done when: the run prints total cost and per-chunk cost

## Show Inner Progress

- Problem:
  - The `tqdm` bar wraps only the outer file loop, so a long chunk sequence gives
    no progress or estimate
- Change:
  - Add a nested `tqdm` bar over the chunks of the current file
- Done when: a multi-file run reports progress at both levels
