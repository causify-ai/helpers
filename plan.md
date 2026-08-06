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
