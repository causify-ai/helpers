#!/usr/bin/env -S uv run

# /// script
# dependencies = ["tqdm", "anthropic", "claude-agent-sdk", "opentelemetry-api"]
# ///

"""
Format or lint files using Claude Code.

For detailed documentation, usage examples, and command-line options, see:
`linters2/cc_lint.README.md`

This script:
- Detects file types by extension and path pattern
- Builds a prompt
- Invokes Claude Code with that prompt on the selected files

# Usage Example

- Lint specific Python files:
> cc_lint.py --files "file1.py file2.py" ...

- Lint a single file:
> cc_lint.py -i file.py ...

- Lint modified files:
> cc_lint.py --modified ...

- Apply specific topic rules:
> cc_lint.py --files "file.py" --topic coding ...

- Execute a skill:
> cc_lint.py --files "file.py" --skill coding.fix_inline ...

- Save command to `tmp.cc_lint_dry_run.txt` without executing:
> cc_lint.py --files "*.md" --dry_run ...
"""

import argparse
import asyncio
import dataclasses
import json
import logging
import os
import re
from typing import Any, cast, Dict, List, Optional, Tuple

from tqdm import tqdm

import dev_scripts_helpers.ai.cc_lib as dshaccli
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hlint as hlint
import helpers.hmarkdown_headers as hmarhead
import helpers.hmarkdown_select as hmarsele
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem


_LOG = logging.getLogger(__name__)

# File collecting the untrimmed dry-run output instead of printing it to
# screen.
_DRY_RUN_FILE = "tmp.cc_lint_dry_run.txt"

# Default JSON journal recording each chunk's outcome in `--mode
# session`/`stateless`, used by `--resume` to skip completed chunks.
_DEFAULT_JOURNAL_FILE = "tmp.cc_lint_journal.json"


# #############################################################################
# Low-level Utility Functions
# #############################################################################


def _get_rules_for_topic(topic: str) -> Dict[str, Dict]:
    """
    Get rules and templates for a given topic.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :return: Dict with role, rules list, templates list, and other config
        ```
        {
            "role": ".claude/skills/role.coding.md",
            "rules": [".claude/skills/coding.rules.md"],
            "templates": [".claude/templates/coding.template.py"],
            "run_jupytext": False,
            "run_lint": False,
        }
        ```
    """
    _LOG.debug("Looking up rules for topic: '%s'", topic)
    TOPIC_TO_INFO = {
        "bash": {
            "role": "role.coding.md",
            "rules": [],
            "templates": [],
        },
        "blog": {
            "role": "role.ai_researcher.md",
            "rules": [
                "blog.rules.md",
                "markdown.rules.md",
                "text.rules.md",
            ],
            "templates": [],
        },
        "book": {
            "role": "role.ai_researcher.md",
            "rules": ["references.rules.md"],
            "templates": [],
        },
        "coding": {
            "role": "role.coding.md",
            "rules": ["coding.rules.md"],
            "templates": ["coding.template.py"],
        },
        "latex": {
            "role": "role.ai_researcher.md",
            "rules": ["latex.rules.md"],
            "templates": [],
        },
        "markdown": {
            "role": "role.ai_researcher.md",
            "rules": [
                "markdown.rules.md",
                "text.rules.md",
            ],
            "templates": [],
        },
        "notebook": {
            "role": "role.notebook.md",
            "rules": ["notebook.rules.md"],
            "templates": [
                "notebook.template.ipynb",
                "notebook_utils_template.py",
            ],
        },
        "readme": {
            "role": "role.ai_researcher.md",
            "rules": ["readme.rules.md"],
            "templates": [],
        },
        "skill": {
            "role": "role.skill.md",
            "rules": ["skill.rules.md"],
            "templates": [],
        },
        "slides": {
            "role": "role.ai_researcher.md",
            "rules": ["slides.rules.md"],
            "templates": [],
        },
        "testing": {
            "role": "role.coding.md",
            "rules": ["testing.rules.md"],
            "templates": ["testing.template.py"],
        },
        "tool_X_in_30_mins": {
            "role": "role.coding.md",
            "rules": ["tool_X_in_30_mins.rules.md"],
            "templates": [],
        },
        "tool_X_in_60_mins": {
            "role": "role.coding.md",
            "rules": ["tool_X_in_60_mins.rules.md"],
            "templates": [],
        },
    }
    hdbg.dassert_in(
        topic,
        TOPIC_TO_INFO,
        "Topic not found in rules",
    )
    # E.g., for topic="coding":
    # ```
    # {"role": "role.coding.md",
    #  "rules": ["coding.rules.md"],
    #  "templates": ["coding.template.py"]}
    # ```
    topic_info = TOPIC_TO_INFO[topic]
    topic_info["role"] = ".claude/skills/%s" % topic_info["role"]
    topic_info["rules"] = [f".claude/skills/{r}" for r in topic_info["rules"]]
    topic_info["templates"] = [
        f".claude/templates/{t}" for t in topic_info["templates"]
    ]
    topic_info["run_jupytext"] = topic in ("notebook",)
    topic_info["run_lint"] = topic in (
        "readme",
        "markdown",
    )
    _LOG.debug("topic_info=%s", topic_info)
    return topic_info


def _infer_topic_from_filename(file_path: str) -> str:
    """
    Detect the file type and return the corresponding topic.

    E.g.,
    - "test_example.py" -> "testing"
    - "hdebug.py" -> "coding"

    :param file_path: Path to the file
    :return: topic (e.g., 'coding', 'testing', 'markdown')
    """
    _LOG.debug("Inferring topic from file: '%s'", file_path)
    basename = os.path.basename(file_path)
    if basename.endswith(".ipynb"):
        topic = "notebook"
    elif basename.endswith(".md"):
        if basename.startswith("README"):
            topic = "readme"
        elif "_in_30_mins.md" in basename:
            topic = "tool_X_in_30_mins"
        elif "_in_60_mins.md" in basename:
            topic = "tool_X_in_60_mins"
        elif ".claude/skills/" in file_path:
            topic = "skill"
        else:
            topic = "markdown"
    elif basename.endswith(".py"):
        if basename.startswith("test_"):
            topic = "testing"
        else:
            topic = "coding"
    elif basename.endswith(".sh"):
        topic = "bash"
    elif basename.endswith(".tex"):
        topic = "latex"
    elif basename.endswith(".txt"):
        topic = "slides"
    else:
        raise ValueError(f"Invalid topic for filename '{file_path}'")
    _LOG.debug("file_path=%s -> return='%s'", file_path, topic)
    return topic


# #############################################################################
# RuleChunk
# #############################################################################


@dataclasses.dataclass
class RuleChunk:
    """
    One rule section ready to be applied as a single incremental turn.
    """

    title: str
    content: str
    order: int
    # Path of the rule file `content` was extracted from, used to cite the
    # rule (e.g., in a `--add_todos` TODO comment).
    rule_file: str = ""


def _estimate_tokens(text: str) -> int:
    """
    Estimate the token count of `text` using a character-based heuristic
    (~4-characters-per-token ratio)

    :param text: text to estimate
    :return: estimated token count
    """
    num_tokens = len(text) // 4
    return num_tokens


def _chunk_h1_title(chunk: RuleChunk) -> str:
    """
    Get the H1 title `chunk` was carried under.

    Every chunk's content starts with its own or its parent H1's header
    line (see `hmarhead.extract_sections_at_level()`), so this is a cheap
    lookup instead of a separate field on `RuleChunk`.

    :param chunk: chunk to inspect
    :return: title from the leading `# <title>` line
    """
    # The H1 header line is always the first line of the chunk's content.
    first_line = chunk.content.split("\n", 1)[0]
    title = first_line.lstrip("#").strip()
    return title


def _merge_small_chunks(
    chunks: List[RuleChunk], *, max_tokens: int
) -> List[RuleChunk]:
    """
    Greedily pack consecutive small chunks up to a token budget.

    Only merges chunks that share the same parent H1 (see
    `_chunk_h1_title()`), so packing never mixes content from unrelated
    sections (e.g., folding the `# Verification` checklist into an
    unrelated neighbor).

    :param chunks: ordered chunks to pack, e.g., the output of
        `_build_rule_chunks()`
    :param max_tokens: token budget per merged chunk; a chunk already over
        budget by itself is kept as its own chunk unmerged
    :return: chunks with consecutive same-H1 small ones combined, in
        original order, `order` renumbered from `0`
    """
    if not chunks:
        return []
    # Seed the current bucket from the first chunk.
    merged: List[RuleChunk] = []
    bucket_titles = [chunks[0].title]
    bucket_content = [chunks[0].content]
    bucket_tokens = _estimate_tokens(chunks[0].content)
    bucket_h1 = _chunk_h1_title(chunks[0])
    bucket_rule_file = chunks[0].rule_file
    # Greedily fold each subsequent chunk into the current bucket when it
    # shares the parent H1 and rule file and still fits the token budget,
    # otherwise flush the bucket and start a new one.
    for chunk in chunks[1:]:
        chunk_tokens = _estimate_tokens(chunk.content)
        same_h1 = _chunk_h1_title(chunk) == bucket_h1
        same_rule_file = chunk.rule_file == bucket_rule_file
        fits_budget = bucket_tokens + chunk_tokens <= max_tokens
        if same_h1 and same_rule_file and fits_budget:
            # Strip the repeated H1 header line before folding into the
            # bucket, since the bucket's first chunk already carries it.
            content_to_add = chunk.content
            if content_to_add.startswith(f"# {bucket_h1}"):
                content_to_add = content_to_add.split("\n", 1)[-1].strip()
            bucket_titles.append(chunk.title)
            bucket_content.append(content_to_add)
            bucket_tokens += chunk_tokens
        else:
            merged.append(
                RuleChunk(
                    title=" / ".join(bucket_titles),
                    content="\n\n".join(bucket_content),
                    order=len(merged),
                    rule_file=bucket_rule_file,
                )
            )
            bucket_titles = [chunk.title]
            bucket_content = [chunk.content]
            bucket_tokens = chunk_tokens
            bucket_h1 = _chunk_h1_title(chunk)
            bucket_rule_file = chunk.rule_file
    # Flush the last bucket.
    merged.append(
        RuleChunk(
            title=" / ".join(bucket_titles),
            content="\n\n".join(bucket_content),
            order=len(merged),
            rule_file=bucket_rule_file,
        )
    )
    _LOG.debug("return=%d merged chunks", len(merged))
    return merged


def _build_rule_chunks(
    topic_info: Dict,
    *,
    level: int = 2,
    max_tokens: int = 1500,
    merge_small_rules: bool = False,
) -> List[RuleChunk]:
    """
    Build the ordered `RuleChunk` sequence for a topic's rule files.

    :param topic_info: topic configuration dict from `_get_rules_for_topic()`
    :param level: header level to split each rule file at (`1`=H1, `2`=H2,
        ...); an H1 section with no header at `level` is kept whole
    :param max_tokens: token budget for `_merge_small_chunks()`, used only
        when `merge_small_rules` is `True`
    :param merge_small_rules: if `True`, greedily pack consecutive small
        chunks up to `max_tokens` (see `_merge_small_chunks()`)
    :return: one `RuleChunk` per section across every rule file in
        `topic_info["rules"]`, in file order, `order` set to position
    """
    _LOG.debug(hprint.to_str("level max_tokens merge_small_rules"))
    # Split every rule file's H1 sections into chunks at `level`, keeping
    # track of which rule file each section came from.
    rule_files = topic_info["rules"]
    all_sections: List[Tuple[str, str, str]] = []
    for rule_file in rule_files:
        hdbg.dassert_file_exists(rule_file, "Rule file not found")
        lines = hio.from_file(rule_file).split("\n")
        for title, content in hmarhead.extract_sections_at_level(
            lines, level=level
        ):
            all_sections.append((title, content, rule_file))
    chunks = [
        RuleChunk(title=title, content=content, order=idx, rule_file=rule_file)
        for idx, (title, content, rule_file) in enumerate(all_sections)
    ]
    # Optionally pack small chunks together to cut the number of turns.
    if merge_small_rules:
        chunks = _merge_small_chunks(chunks, max_tokens=max_tokens)
    _LOG.debug("return=%d chunks", len(chunks))
    return chunks


def _call_llm_for_json(prompt: str, *, model: str) -> Optional[Any]:
    """
    Call the LLM with `prompt` and parse a JSON value out of the reply.

    Strips any surrounding prose or Markdown code fence around the JSON
    payload, since models often wrap structured replies in
    ` ```json ... ``` `.

    :param prompt: prompt requesting a JSON reply
    :param model: model to use, or `""` for `hllmcli.apply_llm()`'s default
    :return: the parsed JSON value (a list or a dict, depending on the
        prompt), or `None` if no JSON could be parsed out of the reply
    """
    _LOG.debug(hprint.to_str("model"))
    # Query the LLM and locate the JSON payload inside the reply.
    response, _ = hllmcli.apply_llm(prompt, model=model)
    match = re.search(r"\[.*\]|\{.*\}", response, re.DOTALL)
    if not match:
        _LOG.warning("No JSON found in LLM reply: '%s'", response)
        return None
    # Parse the located payload.
    try:
        result = json.loads(match.group(0))
    except json.JSONDecodeError:
        _LOG.warning("Could not parse JSON from LLM reply: '%s'", response)
        return None
    _LOG.debug("return=%s", hprint.to_str("result"))
    return result


def _is_verification_chunk(chunk: RuleChunk) -> bool:
    """
    Check whether `chunk` belongs to the terminal `# Verification` section.

    :param chunk: chunk to check
    :return: whether `chunk`'s own or parent H1 title (see
        `_chunk_h1_title()`) is `"Verification"`
    """
    is_verification = _chunk_h1_title(chunk) == "Verification"
    return is_verification


def _filter_relevant_chunks(
    file_path: str, chunks: List[RuleChunk], *, model: str = ""
) -> List[RuleChunk]:
    """
    Keep only the chunks applicable to `file_path`, via one LLM pre-pass.

    Sends every chunk title plus `file_path`'s content to the LLM and asks
    for the applicable subset, so a file that never touches, e.g., AWS
    mocking does not spend a turn on the AWS mocking rule chunk. Biases
    toward inclusion: chunks are kept unfiltered whenever the reply cannot
    be parsed or would discard every chunk, since dropping an applicable
    rule is worse than one extra no-op turn.

    :param file_path: file the chunks would be applied to
    :param chunks: candidate chunks to filter
    :param model: model to use for the pre-pass, or `""` for the default
    :return: the chunks whose title was selected, `order` renumbered from
        `0`; unchanged from `chunks` when the reply cannot be trusted
    """
    _LOG.debug(hprint.to_str("file_path model"))
    # Ask the LLM which candidate chunk titles apply to `file_path`.
    hdbg.dassert_file_exists(file_path)
    file_content = hio.from_file(file_path)
    titles_list = "\n".join(f"- {chunk.title}" for chunk in chunks)
    prompt = f"""
        You are selecting which rule sections apply to the file below.

        File path: {file_path}
        File content:
        ```
        {file_content}
        ```

        Candidate rule section titles:
        {titles_list}

        Reply with a JSON array of the titles (copied exactly) that apply
        to this file. If in doubt, include the title.
        """
    prompt = hprint.dedent(prompt)
    selected = _call_llm_for_json(prompt, model=model)
    # Fail open (keep every chunk) when the reply is not a JSON list.
    if not isinstance(selected, list):
        _LOG.warning(
            "Relevance filter reply was not a JSON list; keeping all %d "
            "chunk(s)",
            len(chunks),
        )
        return chunks
    # Keep only the chunks whose title was selected.
    selected_set = set(selected)
    kept = [chunk for chunk in chunks if chunk.title in selected_set]
    discarded_titles = [
        chunk.title for chunk in chunks if chunk.title not in selected_set
    ]
    if discarded_titles:
        _LOG.info(
            "Discarded %d chunk(s) as not relevant: %s",
            len(discarded_titles),
            discarded_titles,
        )
    # Fail open (keep every chunk) when the reply would discard all of them.
    if not kept:
        _LOG.warning(
            "Relevance filter selected zero chunks; keeping all %d chunk(s)",
            len(chunks),
        )
        return chunks
    kept = [
        dataclasses.replace(chunk, order=idx) for idx, chunk in enumerate(kept)
    ]
    _LOG.debug("return=%d chunks", len(kept))
    return kept


# Category rank used to sort chunks so semantic changes land before
# structural ones, and structural before pure formatting.
_CATEGORY_RANK = {"semantic": 0, "structural": 1, "formatting": 2}


def _order_chunks_by_dependency(
    chunks: List[RuleChunk], *, model: str = ""
) -> List[RuleChunk]:
    """
    Reorder chunks so interacting rules stop fighting each other.

    Runs one LLM pre-pass to categorize each chunk as `semantic`,
    `structural`, or `formatting`, then sorts semantic-first so intent
    changes land before code-shape changes and before pure formatting,
    keeping file order as the tiebreaker within a category. Regardless of
    category, any chunk under the `# Verification` H1 (see
    `_is_verification_chunk()`) is always moved to the end, since it is a
    terminal gate rather than a rule to apply mid-sequence.

    :param chunks: candidate chunks to reorder
    :param model: model to use for the pre-pass, or `""` for the default
    :return: chunks sorted by category with `# Verification` last, `order`
        renumbered from `0`; falls back to `"structural"` for a chunk
        missing from the reply, and to file order when the reply cannot be
        parsed
    """
    _LOG.debug(hprint.to_str("model"))
    # Ask the LLM to categorize every chunk title.
    titles_list = "\n".join(f"- {chunk.title}" for chunk in chunks)
    prompt = f"""
        Classify each rule section title below into exactly one category:
        - "semantic": changes behavior or intent
        - "structural": reorganizes code without changing behavior
        - "formatting": pure style or formatting

        Rule section titles:
        {titles_list}

        Reply with a JSON object mapping each title (copied exactly) to
        its category.
        """
    prompt = hprint.dedent(prompt)
    categories = _call_llm_for_json(prompt, model=model)
    # Fall back to file order (every chunk `"structural"`) when the reply
    # is not a JSON object.
    if not isinstance(categories, dict):
        _LOG.warning(
            "Dependency ordering reply was not a JSON object; keeping "
            "file order for %d chunk(s)",
            len(chunks),
        )
        categories = {}

    def _rank(chunk: RuleChunk) -> Tuple[bool, int]:
        if _is_verification_chunk(chunk):
            return (True, 0)
        category = categories.get(chunk.title, "structural")
        category_rank = _CATEGORY_RANK.get(
            category, _CATEGORY_RANK["structural"]
        )
        return (False, category_rank)

    # Sort semantic-first, `# Verification` always last, file order as the
    # tiebreaker within a category (`sorted()` is stable).
    ordered = sorted(chunks, key=_rank)
    ordered = [
        dataclasses.replace(chunk, order=idx)
        for idx, chunk in enumerate(ordered)
    ]
    _LOG.debug("return=%d chunks", len(ordered))
    return ordered


# #############################################################################
# Journal handling
# #############################################################################


def _load_journal(journal_file: str) -> List[Dict[str, Any]]:
    """
    Load the chunk journal, or return an empty list if it does not exist yet.

    :param journal_file: path to the JSON journal file
    :return: list of journal entries, in the order they were appended
    """
    if not os.path.exists(journal_file):
        return []
    content = hio.from_file(journal_file)
    entries = cast(List[Dict[str, Any]], json.loads(content))
    _LOG.debug("Loaded %d journal entries from '%s'", len(entries), journal_file)
    return entries


def _append_journal_entries(
    journal_file: str, entries: List[Dict[str, Any]]
) -> None:
    """
    Append `entries` to the journal at `journal_file`.

    Read-modify-write so each chunk's outcome is durable on disk as soon as
    it completes, surviving a run that is killed partway through.

    :param journal_file: path to the JSON journal file
    :param entries: journal entries to append, each with `file_path`,
        `chunk_title`, `status`, `cost_usd`, and `num_turns`
    """
    if not entries:
        return
    journal = _load_journal(journal_file)
    journal.extend(entries)
    hio.to_file(journal_file, json.dumps(journal, indent=2))
    _LOG.debug(
        "Appended %d entries to journal '%s' (%d total)",
        len(entries),
        journal_file,
        len(journal),
    )


def _latest_journal_status(
    journal: List[Dict[str, Any]], file_path: str, chunk_title: str
) -> str:
    """
    Get the most recently appended status for `(file_path, chunk_title)`.

    :param journal: journal entries, in append order (see `_load_journal()`)
    :param file_path: file the chunk applies to
    :param chunk_title: chunk title, as journaled
    :return: the `status` of the last matching entry, or `""` if the pair
        has no entry
    """
    status = ""
    for entry in journal:
        if (
            entry["file_path"] == file_path
            and entry["chunk_title"] == chunk_title
        ):
            status = entry["status"]
    return status


def _status_from_chunk_stats(stats: Dict[str, Any]) -> str:
    """
    Map a `PromptSequencer` chunk stats dict to a journal status.

    :param stats: one entry from `PromptSequencer.get_chunk_stats()` (or the
        `on_chunk_done` callback), with `outcome` and `is_error`
    :return: `"failed"` when `is_error` or the reply did not follow the
        no-op contract (`outcome == "UNKNOWN"`), else `"no_op"` or `"done"`
        derived from `outcome`
    """
    if stats["is_error"]:
        return "failed"
    outcome = stats["outcome"]
    if outcome == "NO-OP":
        return "no_op"
    if outcome.startswith("CHANGED"):
        return "done"
    # "UNKNOWN": the reply did not follow the no-op contract, so the
    # chunk's actual effect on the file is untrusted.
    return "failed"


def _filter_resumable(
    file_path: str,
    titled_messages: List[Tuple[str, str]],
    journal: List[Dict[str, Any]],
    journal_file: str,
) -> List[Tuple[str, str]]:
    """
    Drop chunks already `done`/`no_op` for `file_path` in `journal`.

    Journals a `"skipped"` entry for each dropped chunk, so every run's
    outcome for every chunk is recorded, not just the first run that
    actually executed it.

    :param file_path: file the chunks apply to
    :param titled_messages: `(chunk_title, message)` pairs to filter
    :param journal: journal entries loaded via `_load_journal()`
    :param journal_file: path to append `"skipped"` entries to
    :return: `titled_messages` with already-`done`/`no_op` chunks removed
    """
    kept: List[Tuple[str, str]] = []
    skipped_entries: List[Dict[str, Any]] = []
    for title, message in titled_messages:
        status = _latest_journal_status(journal, file_path, title)
        if status in ("done", "no_op"):
            _LOG.info(
                "Skipping chunk '%s' for '%s': already '%s'",
                title,
                file_path,
                status,
            )
            skipped_entries.append(
                {
                    "file_path": file_path,
                    "chunk_title": title,
                    "status": "skipped",
                    "cost_usd": None,
                    "num_turns": None,
                }
            )
        else:
            kept.append((title, message))
    _append_journal_entries(journal_file, skipped_entries)
    _LOG.debug(
        "return=%d of %d chunk(s) kept after --resume filtering",
        len(kept),
        len(titled_messages),
    )
    return kept


# #############################################################################
# Prompt Building
# #############################################################################


def _build_add_todos_instructions(rule_file: str = "") -> str:
    """
    Build the `--add_todos` instruction block.

    Tells Claude Code to insert `# TODO(...): ...` comments citing the
    violated rule's location instead of editing the file to comply with it.

    :param rule_file: path of the rule file to name explicitly; left
        generic when `""` (e.g., the one-shot topic prompt, which lists
        several candidate rule files for Claude Code to read itself)
    :return: instruction text with the TODO comment format and an example,
        e.g.,
        ```
        # TODO(...): Do this and that (testing.rules.md:1081:## Use
        Context Manager Syntax for Multiple Mocks)
        ```
    """
    rule_file_descr = f"`{rule_file}`" if rule_file else "the rule file"
    instructions = f"""
        - Do NOT edit the file to comply with a rule. Instead, for every
          violation, add a comment immediately above the offending line in the
          form:
          ```
          # TODO(...): <what to do and why> (<rule_file>:<rule header line>)
          ```
          E.g.:
          ```
          # TODO(...): Do this and that (testing.rules.md:## Use Context Manager Syntax for Multiple Mocks)
          ```
          - Look up {rule_file_descr} to find the `<rule header line>` (the
            header line text, including its leading `#`s) that the violated rule
            came from
          - Do not otherwise change the file: do not fix the violation, only add
            the TODO comment
        """
    instructions = hprint.dedent(instructions)
    return instructions


def _build_prompt(topic: str, *, add_todos: bool = False) -> Tuple[str, Dict]:
    """
    Build a Claude Code prompt for the given skill.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :param add_todos: if `True`, instruct Claude Code to add
        ```
        # TODO(...): ...
        ```
        comments citing rule violations, instead of applying the rules
    :return: Tuple of (prompt string, topic_info dict)
    """
    _LOG.debug(hprint.to_str("topic add_todos"))
    topic_info = _get_rules_for_topic(topic)
    role = topic_info["role"]
    rules = topic_info["rules"]
    templates = topic_info["templates"]
    prompt_parts = []
    hdbg.dassert_file_exists(role, "Role file not found")
    role_content = hio.from_file(role)
    prompt_parts.append(role_content)
    if rules:
        if add_todos:
            header = "You MUST look for each rule below that is not followed:"
        else:
            header = (
                "You MUST look for each rule below that is not followed "
                "and apply them:"
            )
        prompt_parts.append(f"- {header}")
        for rule_file in rules:
            prompt_parts.append(f"  - `{rule_file}`")
    if templates:
        prompt_parts.append("- You MUST follow the templates below:")
        for template_file in templates:
            prompt_parts.append(f"  - `{template_file}`")
    if add_todos:
        prompt_parts.append(_build_add_todos_instructions())
    else:
        prompt_parts.append(
            "You MUST make sure not to change the behavior or the intent of the passed file"
        )
    txt = "\n".join(prompt_parts)
    _LOG.debug("return=prompt_length=%d", len(txt))
    return txt, topic_info


# #############################################################################
# Execution
# #############################################################################


def _run_claude_code(
    prompt: str,
    topic: str,
    file_path: str,
    dry_run: bool,
    model: str,
) -> int:
    """
    Run Claude Code with the given prompt via the cc wrapper.

    Delegates to `dev_scripts_helpers/ai/cc` which handles model routing
    (OpenRouter vs direct Anthropic) and environment variable setup.

    :param prompt: Claude Code prompt
    :param topic: Topic for logging purposes
    :param file_path: File to process
    :param dry_run: If True, save the command and prompt to
        `_DRY_RUN_FILE` instead of executing
    :param model: Model to use for Claude invocation
    :return: Return code (0 on success, or subprocess return code)
    """
    _LOG.debug(hprint.to_str("prompt topic file_path dry_run model"))
    hdbg.dassert_file_exists(file_path)
    prompt_file = "tmp.cc_lint.prompt.txt"
    hio.to_file(prompt_file, prompt)
    # Call the cc wrapper which handles model routing and env setup.
    _CC_WRAPPER = hgit.find_file(
        "cc", dir_path=os.path.join(os.path.dirname(__file__), "..")
    )
    # Tee the output through extract_cc_log2.py for formatting.
    _EXTRACT_LOG = hgit.find_file(
        "extract_cc_log2.py",
        dir_path=os.path.join(
            os.path.dirname(__file__), "..", "dev_scripts_helpers", "ai"
        ),
    )
    cmd = [
        _CC_WRAPPER,
        "-p",
        f"Execute the file {prompt_file}",
    ]
    cmd = " ".join(cmd) + f" | {_EXTRACT_LOG}"
    if dry_run:
        # Save the full, untrimmed dry-run output to a file instead of
        # printing it to screen.
        dry_run_output = [
            "Using model: %s" % model,
            hprint.frame("Prompt (%s):" % topic),
            prompt,
            "Claude command: %s" % cmd,
            "Dry run: command not executed",
        ]
        hio.to_file(_DRY_RUN_FILE, "\n".join(dry_run_output))
        _LOG.warning("Saved dry-run output to '%s'", _DRY_RUN_FILE)
        _LOG.debug("return=0")
        return 0
    _LOG.info("Using model: %s", model)
    _LOG.debug("\n%s\n%s", hprint.frame("Prompt (%s):") % topic, prompt)
    _LOG.info("Claude command: %s", cmd)
    hsystem.system(cmd)
    _LOG.debug("return=0")
    return 0


# #############################################################################
# File Processing
# #############################################################################


def _build_incremental_system_prompt(
    topic_info: Dict, *, add_todos: bool = False
) -> str:
    """
    Build the system prompt for incremental rule application.

    The role and the "do not change behavior" instruction are sent once as
    the system prompt instead of being repeated in a message, since they
    apply to every rule turn.

    :param topic_info: topic configuration dict from `_get_rules_for_topic()`
    :param add_todos: if `True`, append `# TODO(...): ...` comments instead of
        applying the rule
    :return: system prompt text combining the role, the templates to
        follow, and the "do not change behavior" instruction
    """
    system_prompt: List[str] = []
    #
    role = topic_info["role"]
    hdbg.dassert_file_exists(role, "Role file not found")
    role_content = hio.from_file(role)
    system_prompt.append(role_content)
    #
    msg = "You MUST make sure not to change the behavior or the intent of the passed file"
    system_prompt.append(msg)
    #
    if add_todos:
        system_prompt.append(_build_add_todos_instructions())
    #
    templates = topic_info["templates"]
    if templates:
        msg = "- You MUST follow the templates below:"
        system_prompt.append(msg)
        for template_file in templates:
            system_prompt.append(f"  - `{template_file}`")
    #
    system_prompt_as_str = "\n".join(system_prompt)
    _LOG.debug(hprint.to_str("system_prompt_as_str"))
    return system_prompt_as_str


def _build_rule_message(
    file_path: str,
    rule_content: str,
    *,
    rule_file: str = "",
    add_todos: bool = False,
) -> str:
    """
    Build one rule message re-anchored on `file_path` with the no-op contract.

    Naming `file_path` in every message keeps its referent from drifting
    once the context holds several rule sections; the no-op contract lets a
    compliant rule produce zero edits instead of forced churn.

    :param file_path: path of the file the rule applies to
    :param rule_content: H1 rule section content to apply
    :param rule_file: path of the rule file `rule_content` was extracted
        from, cited in the check instruction when `add_todos` is `True`
    :param add_todos: if `True`, check the rule for violations and add
        `# TODO(...): ...` comments instead of applying the rule
    :return: prompt text requiring a structured reply like
        - `LLM> NO-OP`
        - `LLM> CHANGED: <summary>`
    """
    rule_message: List[str] = []
    if add_todos:
        rule_file_descr = f"(from `{rule_file}`) " if rule_file else ""
        action = rf"""
        Check ONLY the rule below {rule_file_descr}against `{file_path}` for violations and add a TODO(...) comment for each one, per the system prompt's TODO format
        """
        action = hprint.dedent(action)
    else:
        action = f"Apply ONLY the rule below to `{file_path}`"
    header = f"""
    - {action}
    - Do not revisit rules applied earlier
    """
    rule_message.append(hprint.dedent(header))
    fence_block = f"```\n{rule_content}\n```"
    rule_message.append(hprint.indent(fence_block, num_spaces=2))
    #
    if add_todos:
        footer = """
        - Reply with exactly one line:
          - `LLM> NO-OP` if the file already complies with the rule or already
            has a TODO for every violation
          - `LLM> CHANGED: <one-line summary>` if you added TODO comment(s)
        """
    else:
        footer = """
        - Reply with exactly one line:
          - `LLM> NO-OP` if the file already complies with the rule
          - `LLM> CHANGED: <one-line summary>` if you made an edit
        """
    rule_message.append(hprint.dedent(footer))
    #
    msg = "\n".join(rule_message)
    return msg


def _build_incremental_messages(
    file_path: str,
    topic_info: Dict,
    *,
    level: int = 2,
    max_tokens: int = 1500,
    merge_small_rules: bool = False,
    filter_rules_by_relevance: bool = False,
    order_rules_by_dependency: bool = False,
    model: str = "",
    add_todos: bool = False,
) -> List[Tuple[str, str]]:
    """
    Build a sequence of rule messages for incremental rule application.

    :param file_path: path of the file to process, interpolated into every
        rule message
    :param topic_info: topic configuration dict from `_get_rules_for_topic()`
    :param level: header level to split each rule file at, passed to
        `_build_rule_chunks()`
    :param max_tokens: token budget passed to `_build_rule_chunks()`, used
        only when `merge_small_rules` is `True`
    :param merge_small_rules: if `True`, pack small chunks up to
        `max_tokens` (see `_build_rule_chunks()`)
    :param filter_rules_by_relevance: if `True`, drop chunks the pre-pass in
        `_filter_relevant_chunks()` finds inapplicable to `file_path`
    :param order_rules_by_dependency: if `True`, reorder chunks via
        `_order_chunks_by_dependency()` so semantic rules land first and
        `# Verification` lands last
    :param model: model to use for the `filter_rules_by_relevance` and
        `order_rules_by_dependency` pre-passes
    :param add_todos: if `True`, each message asks Claude Code to add `#
        TODO(...): ...` comments instead of applying the rule (see
        `_build_rule_message()`)
    :return: one `(chunk_title, message)` pair per rule chunk; the role and
        the "do not change behavior" instruction live in the system prompt
        instead (see `_build_incremental_system_prompt()`)
    """
    _LOG.debug(
        hprint.to_str(
            "file_path level max_tokens merge_small_rules "
            "filter_rules_by_relevance order_rules_by_dependency add_todos"
        )
    )
    hdbg.dassert_file_exists(file_path)
    chunks = _build_rule_chunks(
        topic_info,
        level=level,
        max_tokens=max_tokens,
        merge_small_rules=merge_small_rules,
    )
    _LOG.info("Built %d rule chunk(s) at level %d", len(chunks), level)
    if filter_rules_by_relevance:
        chunks = _filter_relevant_chunks(file_path, chunks, model=model)
    if order_rules_by_dependency:
        chunks = _order_chunks_by_dependency(chunks, model=model)
    #
    titled_messages = [
        (
            chunk.title,
            _build_rule_message(
                file_path,
                chunk.content,
                rule_file=chunk.rule_file,
                add_todos=add_todos,
            ),
        )
        for chunk in chunks
    ]
    _LOG.debug("return=%d messages", len(titled_messages))
    return titled_messages


def _build_incremental_messages_for_rule(
    file_path: str, rule_content: str, rule_spec: str, *, add_todos: bool = False
) -> List[Tuple[str, str]]:
    """
    Build incremental rule messages for a `--rule` specification.

    A whole-file rule spec (`path/to/rules.md`) can carry more than one H1
    section, so it is split into one chunk per section, like the `--topic`
    path.
    A line-anchored spec (`path/to/rules.md:N`) already extracts a single
    section, so it is kept as one chunk.

    :param file_path: path of the file to apply the rule to
    :param rule_content: rule text from `hmarsele.extract_rule_from_file()`
    :param rule_spec: the `--rule` value as passed on the command line, used
        as the chunk title when `rule_content` has no H1 section of its own
        to name it, and to derive the rule file path (the part before the
        first `:`) cited when `add_todos` is `True`
    :param add_todos: if `True`, each message asks Claude Code to add `#
        TODO(...): ...` comments instead of applying the rule (see
        `_build_rule_message()`)
    :return: one `(chunk_title, message)` pair per H1 section in
        `rule_content`, or a single pair titled `rule_spec` when it has zero
        or one H1 section
    """
    _LOG.debug(hprint.to_str("file_path rule_spec add_todos"))
    lines = rule_content.split("\n")
    sections = hmarhead.extract_h1_sections_from_lines(lines)
    if len(sections) > 1:
        titled_contents = sections
    else:
        titled_contents = [(rule_spec, rule_content)]
    rule_file = rule_spec.split(":", 1)[0]
    titled_messages = [
        (
            title,
            _build_rule_message(
                file_path, content, rule_file=rule_file, add_todos=add_todos
            ),
        )
        for title, content in titled_contents
    ]
    _LOG.debug("return=%d messages", len(titled_messages))
    return titled_messages


async def _process_file_incrementally(
    file_path: str,
    dry_run: bool,
    model: str,
    context_strategy: str,
    topic_info: Dict,
    *,
    skill: str = "",
    rule: str = "",
    rule_level: int = 2,
    max_chunk_tokens: int = 1500,
    merge_small_rules: bool = False,
    filter_rules_by_relevance: bool = False,
    order_rules_by_dependency: bool = False,
    resume: bool = False,
    journal_file: str = "",
    max_turns_per_chunk: Optional[int] = None,
    add_todos: bool = False,
) -> int:
    """
    Apply rules incrementally, one chunk per Claude Code interaction.

    The chunks sent depend on which "what" was specified, mirroring the
    `--topic`/`--skill`/`--rule`/default dispatch of the
    `_build_one_shot_prompt()` path:
    - `skill`: a single, non-decomposed `/{skill} {file_path}` slash-command
      chunk, since it is a command for Claude Code's own skill loader, not
      declarative rule prose to split
    - `rule`: the rule text from `hmarsele.extract_rule_from_file()`, split
      into H1 sections when it has more than one, else kept as a single
      chunk (see `_build_incremental_messages_for_rule()`)
    - neither: one `RuleChunk` per section across `topic_info["rules"]`,
      shaped by `rule_level`/`max_chunk_tokens`/`merge_small_rules`/
      `filter_rules_by_relevance`/`order_rules_by_dependency`

    Every chunk's outcome is journaled to `journal_file` as it completes
    (see `_append_journal_entries()`), so a run killed partway through can
    be resumed with `resume=True`, which skips chunks already `done`/
    `no_op` for `file_path` (see `_filter_resumable()`).

    :param file_path: Path to the file to process
    :param dry_run: If True, print messages without executing
    :param model: Model to use for Claude invocation (used via SDK
        configuration, and for the `filter_rules_by_relevance`/
        `order_rules_by_dependency` pre-passes)
    :param context_strategy: `"stateless"` for a fresh session per chunk, or
        `"session"` for a single session shared across all chunks (i.e.,
        `--mode` when it is `"session"`/`"stateless"`)
    :param topic_info: topic configuration dict from `_get_rules_for_topic()`,
        used for the system prompt (role, templates) and, when neither
        `skill` nor `rule` is set, for the rule files to split into chunks
    :param skill: skill name to execute via `--skill`, if any
    :param rule: rule specification to execute via `--rule`, if any
    :param rule_level: header level to split rule chunks at, when neither
        `skill` nor `rule` is set
    :param max_chunk_tokens: token budget per merged chunk, used only when
        `merge_small_rules` is `True`
    :param merge_small_rules: if `True`, pack small chunks up to
        `max_chunk_tokens`
    :param filter_rules_by_relevance: if `True`, drop chunks an LLM
        pre-pass finds inapplicable to `file_path`
    :param order_rules_by_dependency: if `True`, reorder chunks via an LLM
        pre-pass so semantic rules apply first and `# Verification` last
    :param resume: if `True`, skip chunks already `done`/`no_op` for
        `file_path` in `journal_file`
    :param journal_file: path to the JSON chunk journal; journaling is
        skipped when `""`
    :param max_turns_per_chunk: per-chunk turn limit forwarded to
        `PromptSequencer(max_turns=...)`, or `None` for no limit
    :param add_todos: if `True`, ask Claude Code to add `#
        TODO(...): ...` comments citing rule violations instead of
        applying the rules (see `_build_add_todos_instructions()`);
        ignored when `skill` is set, since a skill invocation owns its own
        prompt
    :return: Return code (0 on success)
    """
    _LOG.debug(
        hprint.to_str(
            "file_path dry_run model context_strategy skill rule "
            "rule_level max_chunk_tokens merge_small_rules "
            "filter_rules_by_relevance order_rules_by_dependency "
            "resume journal_file max_turns_per_chunk add_todos"
        )
    )
    hdbg.dassert_file_exists(file_path)
    system_prompt = _build_incremental_system_prompt(
        topic_info, add_todos=add_todos
    )
    _LOG.debug("\n%s\n%s", hprint.frame("System prompt:"), system_prompt)
    if skill:
        # A skill invocation is a single command for Claude Code's own skill
        # loader, kept as-is instead of being split into rule chunks.
        full_skill_name = hmarsele.find_skill(skill)
        titled_messages = [
            (f"skill:{full_skill_name}", f"/{full_skill_name} {file_path}")
        ]
    elif rule:
        rule_content = hmarsele.extract_rule_from_file(rule)
        titled_messages = _build_incremental_messages_for_rule(
            file_path, rule_content, rule, add_todos=add_todos
        )
    else:
        titled_messages = _build_incremental_messages(
            file_path,
            topic_info,
            level=rule_level,
            max_tokens=max_chunk_tokens,
            merge_small_rules=merge_small_rules,
            filter_rules_by_relevance=filter_rules_by_relevance,
            order_rules_by_dependency=order_rules_by_dependency,
            model=model,
            add_todos=add_todos,
        )
    if resume and journal_file:
        journal = _load_journal(journal_file)
        titled_messages = _filter_resumable(
            file_path, titled_messages, journal, journal_file
        )
    # Handle dry run.
    if dry_run:
        # Save the full, untrimmed dry-run output to a file instead of
        # printing it to screen.
        dry_run_output = ["Dry Run - System prompt and messages to be sent:"]
        dry_run_output.append(
            "\n%s\n%s" % (hprint.frame("System prompt:"), system_prompt)
        )
        for idx, (title, msg) in enumerate(titled_messages, 1):
            dry_run_output.append(
                "\n%s\n%s"
                % (
                    hprint.frame(
                        f"Message {idx}/{len(titled_messages)} ({title}):"
                    ),
                    msg,
                )
            )
        hio.to_file(_DRY_RUN_FILE, "\n".join(dry_run_output))
        _LOG.warning("Saved dry-run output to '%s'", _DRY_RUN_FILE)
        _LOG.debug("return=0 (dry_run)")
        return 0
    if not titled_messages:
        # `--resume` found every chunk already `done`/`no_op`, so there is
        # nothing left to send to `PromptSequencer` (which requires at
        # least one prompt).
        _LOG.info(
            "Nothing to do for '%s': every chunk is already resolved",
            file_path,
        )
        _LOG.debug("return=0 (nothing to resume)")
        return 0
    # Execute messages using PromptSequencer.
    _LOG.info(
        "Executing %d messages with '%s' context strategy",
        len(titled_messages),
        context_strategy,
    )
    titles = [title for title, _ in titled_messages]
    messages = [msg for _, msg in titled_messages]
    pbar = tqdm(total=len(messages), desc="Executing messages")

    def _on_chunk_done(prompt_idx: int, stats: Dict[str, Any]) -> None:
        pbar.update(1)
        if not journal_file:
            return
        entry = {
            "file_path": file_path,
            "chunk_title": titles[prompt_idx - 1],
            "status": _status_from_chunk_stats(stats),
            "cost_usd": stats["cost_usd"],
            "num_turns": stats["num_turns"],
        }
        _append_journal_entries(journal_file, [entry])

    try:
        sequencer = dshaccli.PromptSequencer(
            allowed_tools=["Read", "Edit", "Grep", "Glob"],
            disallowed_tools=["Bash", "Task", "WebFetch"],
            permission_mode="acceptEdits",
            cwd=os.getcwd(),
            model=model,
            system_prompt=system_prompt,
            context_strategy=context_strategy,
            target_file=file_path,
            max_turns=max_turns_per_chunk,
            on_chunk_done=_on_chunk_done,
        )
        await sequencer.execute(messages)
        stats = sequencer.get_execution_stats()
        _LOG.debug("Execution completed: %s", stats)
        for idx, outcome in enumerate(sequencer.get_outcomes(), 1):
            _LOG.debug("Rule %d/%d outcome: %s", idx, len(messages), outcome)
        _LOG.debug("return=0")
        return 0
    except Exception as e:
        _LOG.error("Sequential execution failed: %s", str(e))
        _LOG.debug("return=1")
        return 1
    finally:
        pbar.close()


def _build_one_shot_prompt(
    file_path: str, args: argparse.Namespace
) -> Tuple[str, str, Dict]:
    """
    Build the single one-shot prompt for `file_path`.

    Shared by `--mode one_shot_with_cc` (executed via a system call to the
    `cc` wrapper, see `_run_claude_code()`) and `--mode one_shot` (executed
    in-process via `PromptSequencer`, see
    `_process_file_one_shot_via_sequencer()`), so both modes send Claude
    Code the exact same prompt and differ only in how it is invoked.

    Mirrors the `--topic`/`--skill`/`--rule`/default dispatch used by the
    `session`/`stateless` incremental path (see
    `_process_file_incrementally()`).

    :param file_path: file to process
    :param args: parsed command-line arguments
    :return: tuple of `(prompt, topic_str, topic_info)`, where `topic_str`
        is used for dry-run/logging labels and `topic_info` is the
        inferred topic's rules/templates configuration
    """
    add_todos = args.add_todos
    if args.skill:
        full_skill_name = hmarsele.find_skill(args.skill)
        prompt = f"/{full_skill_name} {file_path}"
        topic_str = "skill"
        inferred_topic = _infer_topic_from_filename(file_path)
        topic_info = _get_rules_for_topic(inferred_topic)
    elif args.rule:
        _LOG.debug("Executing rule: %s", args.rule)
        rule_content = hmarsele.extract_rule_from_file(args.rule)
        if add_todos:
            rule_file = args.rule.split(":", 1)[0]
            prompt = (
                f"Check the rule below against file {file_path} for "
                f"violations (do not fix them):\n{rule_content}\n\n"
                + _build_add_todos_instructions(rule_file)
            )
        else:
            prompt = (
                f"Execute the rule below on file {file_path}:\n{rule_content}"
            )
        topic_str = "rule"
        inferred_topic = _infer_topic_from_filename(file_path)
        topic_info = _get_rules_for_topic(inferred_topic)
    else:
        if args.topic:
            topic_str = args.topic
        else:
            topic = _infer_topic_from_filename(file_path)
            hdbg.dassert_is_not(topic, None, "Topic detection failed")
            topic_str = cast(str, topic)
        prompt, topic_info = _build_prompt(topic_str, add_todos=add_todos)
        if add_todos:
            prompt += (
                "\n\n- Check the files below against the rules and "
                "conventions above and add TODO\n"
                "  comments for violations without asking questions to the "
                "user\n"
                f"  - `{file_path}`"
            )
        else:
            prompt += (
                "\n\n- Process the files below according to the rules and "
                "conventions above and make the changes without asking "
                "questions to the user\n"
                f"  - `{file_path}`"
            )
    return prompt, topic_str, topic_info


async def _process_file_one_shot_via_sequencer(
    file_path: str,
    dry_run: bool,
    model: str,
    prompt: str,
) -> int:
    """
    Apply `prompt` to `file_path` in a single `PromptSequencer` call.

    Equivalent to `--mode one_shot_with_cc`, but calls `PromptSequencer`
    in-process instead of shelling out to the `cc` wrapper (see
    `_run_claude_code()`).

    :param file_path: file to process
    :param dry_run: if `True`, save `prompt` to `_DRY_RUN_FILE` instead of
        executing
    :param model: model to use for the `PromptSequencer` call
    :param prompt: the single one-shot message to send, built by
        `_build_one_shot_prompt()`
    :return: return code (`0` on success, `1` on `PromptSequencer` failure)
    """
    _LOG.debug(hprint.to_str("file_path dry_run model"))
    hdbg.dassert_file_exists(file_path)
    if dry_run:
        # Save the full, untrimmed dry-run output to a file instead of
        # printing it to screen.
        dry_run_output = [
            "Using model: %s" % model,
            hprint.frame("Message:"),
            prompt,
            "Dry run: command not executed",
        ]
        hio.to_file(_DRY_RUN_FILE, "\n".join(dry_run_output))
        _LOG.warning("Saved dry-run output to '%s'", _DRY_RUN_FILE)
        _LOG.debug("return=0 (dry_run)")
        return 0
    try:
        sequencer = dshaccli.PromptSequencer(
            allowed_tools=["Read", "Edit", "Grep", "Glob"],
            disallowed_tools=["Bash", "Task", "WebFetch"],
            permission_mode="acceptEdits",
            cwd=os.getcwd(),
            model=model,
            context_strategy="stateless",
            target_file=file_path,
        )
        await sequencer.execute([prompt])
        _LOG.debug("return=0")
        return 0
    except Exception as e:
        _LOG.error("One-shot execution failed: %s", str(e))
        _LOG.debug("return=1")
        return 1


def _process_file(
    file_path: str,
    args: argparse.Namespace,
) -> Tuple[int, Dict]:
    """
    Process a single file with the given arguments.

    :param file_path: Path to the file to process.
    :param args: Parsed command-line arguments.
    :return: Tuple of (return code, topic_info dict).
    """
    _LOG.debug("Processing file: '%s'", file_path)
    if args.mode in ("one_shot_with_cc", "one_shot"):
        # Both modes send Claude Code the exact same prompt (see
        # `_build_one_shot_prompt()`) and only differ in how it's invoked:
        # `one_shot_with_cc` shells out to the `cc` wrapper, `one_shot` calls
        # `PromptSequencer` in-process.
        prompt, topic_str, topic_info = _build_one_shot_prompt(file_path, args)
        if args.mode == "one_shot_with_cc":
            rc = _run_claude_code(
                prompt,
                topic_str,
                file_path,
                dry_run=args.dry_run,
                model=args.model,
            )
        else:
            rc = asyncio.run(
                _process_file_one_shot_via_sequencer(
                    file_path, args.dry_run, args.model, prompt
                )
            )
    else:
        # `args.mode` is "session" or "stateless": apply rules incrementally
        # via async processor, with `args.mode` selecting the context
        # strategy, and `args.skill`/`args.rule`/`args.topic` selecting the
        # "what" (mirroring the topic/skill/rule/default dispatch above).
        if args.topic:
            topic_str = args.topic
        else:
            topic_str = _infer_topic_from_filename(file_path)
        topic_info = _get_rules_for_topic(topic_str)
        # `0` means "no limit" on the CLI; `PromptSequencer` expects `None`.
        max_turns_per_chunk = args.max_turns_per_chunk or None
        rc = asyncio.run(
            _process_file_incrementally(
                file_path,
                args.dry_run,
                args.model,
                args.mode,
                topic_info,
                skill=args.skill,
                rule=args.rule,
                rule_level=args.rule_level,
                max_chunk_tokens=args.max_chunk_tokens,
                merge_small_rules=args.merge_small_rules,
                filter_rules_by_relevance=args.filter_rules_by_relevance,
                order_rules_by_dependency=args.order_rules_by_dependency,
                resume=args.resume,
                journal_file=args.journal_file,
                max_turns_per_chunk=max_turns_per_chunk,
                add_todos=args.add_todos,
            )
        )

    _LOG.debug("return=(%d, topic_info)", rc)
    return rc, topic_info


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # File selection options (--files, --from_file, --branch, --modified, etc.).
    hseinout.add_file_selection_args(parser)
    # File type filtering options (--file_types, --skip_file_types).
    hseinout.add_file_type_filter_args(parser, file_types_default="py,ipynb,md")
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--topic",
        type=str,
        default="",
        help="Claude Code skill topic (e.g., 'coding.format'). "
        "Can only be used with a single file.",
    )
    action_group.add_argument(
        "--skill",
        type=str,
        default="",
        help="Execute a skill on selected files. E.g., `coding.fix_inline`",
    )
    hmarsele.add_rule_cli_arg(action_group)
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["one_shot_with_cc", "one_shot", "session", "stateless"],
        help=hprint.dedent("""
        Execution mode:
        - 'one_shot_with_cc' applies all rules in a single Claude Code
          invocation, shelling out to the `cc` wrapper
        - 'one_shot' applies all rules in a single Claude Code invocation
          too, but calls `PromptSequencer` in-process instead of shelling
          out; equivalent to 'one_shot_with_cc' otherwise
        - 'session' and 'stateless' apply rules incrementally, one H1 section
          per Claude Code interaction, sharing one session across all chunks
          ('session') or opening a fresh session per chunk ('stateless')
        """),
    )
    parser.add_argument(
        "--add_todos",
        action="store_true",
        help="Instead of applying rules, add "
        "'# TODO(...): ... (rule_file:header)' comments citing each "
        "rule violation; cannot be combined with --skill",
    )
    parser.add_argument(
        "--rule_level",
        type=int,
        default=2,
        help="Header level to split rule chunks at in --mode "
        "session/stateless (1=H1, 2=H2, ...); an H1 section with no header "
        "at this level is kept whole",
    )
    parser.add_argument(
        "--max_chunk_tokens",
        type=int,
        default=1500,
        help="Token budget per merged rule chunk; used only with "
        "--merge_small_rules",
    )
    parser.add_argument(
        "--merge_small_rules",
        action="store_true",
        help="Greedily pack consecutive small rule chunks under the same "
        "parent H1 up to --max_chunk_tokens",
    )
    parser.add_argument(
        "--filter_rules_by_relevance",
        action="store_true",
        help="Drop rule chunks an LLM pre-pass finds inapplicable to the "
        "file being processed",
    )
    parser.add_argument(
        "--order_rules_by_dependency",
        action="store_true",
        help="Reorder rule chunks via an LLM pre-pass so semantic rules "
        "apply before structural and formatting rules, with the "
        "Verification checklist always last",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip chunks in --mode session/stateless already marked "
        "'done' or 'no_op' for the file in --journal_file",
    )
    parser.add_argument(
        "--journal_file",
        type=str,
        default=_DEFAULT_JOURNAL_FILE,
        help="JSON journal recording each chunk's outcome in --mode "
        "session/stateless, read by --resume",
    )
    parser.add_argument(
        "--max_turns_per_chunk",
        type=int,
        default=15,
        help="Per-chunk turn limit in --mode session/stateless, passed as "
        "ClaudeAgentOptions.max_turns; pass 0 for no limit",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help=f"Save the command to '{_DRY_RUN_FILE}' instead of executing",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-haiku-4-5-20251001",
        help="Model name to use using cc conventions",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> int:
    """
    Main entry point.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Select files.
    # Mutual exclusivity between `--topic`/`--skill`/`--rule` is already
    # enforced by their argparse mutually exclusive group.
    # `--mode` is orthogonal to `--topic`/`--skill`/ `--rule`.
    num_exclusive = sum(
        [
            bool(args.topic),
            bool(args.skill),
            bool(args.rule),
        ]
    )
    hdbg.dassert_lte(
        num_exclusive,
        1,
        "Only one of --topic, --skill, or --rule can be used simultaneously",
    )
    hdbg.dassert(
        not (args.add_todos and args.skill),
        "--add_todos cannot be combined with --skill, since a skill "
        "invocation owns its own prompt",
    )
    files = hseinout.parse_file_selection_args(args, remove_dirs=False)
    files = hseinout.parse_file_type_filter_args(args, files)
    # --topic option can only be used with exactly one file.
    if args.topic:
        hdbg.dassert_eq(
            len(files),
            1,
            "--topic can only be used with a single file",
        )
    _LOG.info("Processing %d file(s)", len(files))
    ret = 0
    for file_path in tqdm(files, desc="Processing files"):
        rc, topic_info = _process_file(file_path, args)
        ret |= rc
        if topic_info:
            if topic_info.get("run_jupytext"):
                cmd = ["jupytext", "--sync", file_path]
                hsystem.system(" ".join(cmd))
            if topic_info.get("run_lint"):
                hlint.lint_file(file_path)
    return ret


if __name__ == "__main__":
    ret = _main(_parse())
    exit(ret)
