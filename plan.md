# Phase 3: Rule Chunking and Filtering

## Split Rules at H2 with a Token Budget

- Problem:
  - H1 sections are wildly unequal in size
  - In `.claude/skills/testing.rules.md` the section `# Verification` is a short
    checklist while `# Writing Test Code` spans most of the file
  - A single oversized chunk reproduces the monolithic prompt it was meant to
    replace
- Change:
  - Split at the level given by `--rule_level`, defaulting to H2
  - Carry the parent H1 title into each chunk as context

## Merge tokens with a Token Budget
- Add a switch to enable this transform --merge_small_rules

- Change:
  - Greedily pack consecutive small sections up to `--max_chunk_tokens`
  - Introduce a `RuleChunk` dataclass:
    ```python
    @dataclass
    class RuleChunk:
        title: str
        content: str
        order: int
    ```
- Done when: chunk sizes fall within a single order of magnitude

## Filter Rules by Relevance
- Add a switch to enable this transform --filter_rules_by_relevance

- Problem:
  - A test file with no mocks still spends turns on the AWS mocking rules and the
    syscall mocking rules
- Change:
  - Add one cheap pre-pass that sends the chunk titles and the file, and asks for
    a JSON list of applicable titles
  - Run only the selected chunks, and log the discarded ones

- Re-use the master flow, in the sense that rules are filtered and written
  in a temporary file and then reused for the split
  - This transform is done at the beginning and then the normal flow is reused

## Order Chunks by Dependency
- Add a switch to enalbe this transform --order_rules_by_dependency

- Problem:
  - Chunks are applied in file order, so interacting rules can fight each other
    - E.g., factoring code into helper methods versus ordering helper methods
      first versus consolidating inputs and outputs
  - The `# Verification` checklist is applied as one section among many rather
    than as a final gate
- Change:
  - Add one pre-pass to assign each chunk a category: semantic, structural, or
    formatting with an explanation of what they are
  - Sort by category (semantic > structural > formatting)
  - Then apply them in order
  - Always run the `# Verification` checklist last, as a terminal pass

- Re-use the master flow, in the sense that rules are filtered and written
  in a temporary file and then reused for the split
  - This transform is done at the beginning and then the normal flow is reused

# Phase 4: Checkpointing and Resume

## Snapshot and Verify Each Chunk

- Problem:
  - Nothing checks that a rule left the file valid
  - The instruction not to change behavior is unverifiable when the target is
    itself a test file
- Change:
  - Before each chunk, read the file into memory as a snapshot
  - After each chunk, run an escalating gate:
    - `ast.parse()` on the file content, which is cheap and catches syntax breaks
    - `hlint.lint_file()` for the topics that request it
    - `pytest <file> -x -q` for the `testing` topic
  - On failure, restore the snapshot, mark the chunk failed, and continue with
    the next chunk instead of aborting the run
- Done when: a rule that breaks the file is rolled back and named in the log

## Journal Every Chunk Outcome

- Problem:
  - The observed run died partway through the sequence
  - Completed work was neither attributed nor resumable
  - `dev_scripts_helpers/ai/cc_lib.py` already defines `save_session_log()`, but
    `linters2/lint_cc.py` never calls it
- Change:
  - Write a JSON journal keyed by (`file_path`, `chunk_title`) holding:
    - `status`: one of `done`, `no_op`, `failed`, `skipped`
    - `diff`: the unified diff produced by the chunk
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
  - Treat a `max_turns` terminal reason as a chunk failure and roll back
- Done when: a pathological rule stops instead of hanging the run

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

## Make Dry Run Inspectable

- Problem:
  - The dry run truncates each message to a short preview, so the plan cannot be
    reviewed
- Change:
  - Dump the full ordered message list to `tmp.lint_cc.messages.txt`
  - Keep the truncated preview on the console
- Done when: the dry run writes a file that reproduces the exact prompts

## Show Inner Progress

- Problem:
  - The `tqdm` bar wraps only the outer file loop, so a long chunk sequence gives
    no progress or estimate
- Change:
  - Add a nested `tqdm` bar over the chunks of the current file
- Done when: a multi-file run reports progress at both levels

# Refactoring

- Problem:
  - `_build_prompt()` and `_build_incremental_messages()` each assemble the role,
    the templates, and the "do not change behavior" instruction, so the two modes
    can drift
- Change:
  - Factor the shared assembly into one builder used by both modes
  - Introduce the helpers:
    ```python
    def _build_rule_chunks(topic_info, *, level=2, max_tokens=1500) -> List[RuleChunk]
    def _filter_relevant_chunks(file_path, chunks) -> List[RuleChunk]
    def _apply_chunk(file_path, chunk, opts) -> ChunkResult
    ```
- Done when: the role and template text exists in exactly one place

# Verification

- Unit tests to add in `linters2/test/test_lint_cc.py`:
  - `_build_rule_chunks()` splits at the requested level and respects the token
    budget
  - `_build_rule_chunks()` carries the parent H1 title into each chunk
  - Chunk ordering puts the verification checklist last
  - The journal round-trips and `--resume` skips completed chunks
  - A fenced `# comment` line does not create a spurious chunk
- End-to-end checks:
  - `--dry_run` on a Python file, a test file, and a markdown file
  - A full run on a file known to be compliant, expecting `NO-OP` throughout and
    an unchanged file
  - A full run interrupted partway, then rerun with `--resume`

# Risks and Trade-Offs

- **Stateless mode loses cross-rule memory**:
  - Mitigated by keeping `--incremental_mode session` available
- **The relevance filter can discard a rule that did apply**:
  - Mitigated by logging discarded chunks and biasing the pre-pass toward
    inclusion
- **Per-chunk test runs are slow on large test files**:
  - Mitigated by `--verify_each_rule`, which can drop back to the `ast.parse()`
    gate only
- **Restricting the tool surface can block a legitimate rule**:
  - E.g., a rule that requires reading a sibling file for context
  - Mitigated by allowing reads anywhere while restricting writes to the target
- **Pinning the settings sources changes behavior for existing users**:
  - Mitigated by landing the change with a note in `linters2/lint_cc.README.md`
