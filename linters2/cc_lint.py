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

Quick examples:
# Lint specific Python files:
> cc_lint.py --files "file1.py file2.py"

# Lint modified files:
> cc_lint.py --modified

# Apply specific topic rules:
> cc_lint.py --files "file.py" --topic coding

# Execute a skill:
> cc_lint.py --files "file.py" --skill coding.fix_inline

# Save command to `tmp.cc_lint_dry_run.txt` without executing:
> cc_lint.py --files "*.md" --dry_run
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
    _LOG.debug(
        "topic_info=%s", topic_info
    )
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
# Rule Chunking and Filtering
# #############################################################################


@dataclasses.dataclass
class RuleChunk:
    """
    One rule section ready to be applied as a single incremental turn.
    """

    title: str
    content: str
    order: int


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
    # Greedily fold each subsequent chunk into the current bucket when it
    # shares the parent H1 and still fits the token budget, otherwise flush
    # the bucket and start a new one.
    for chunk in chunks[1:]:
        chunk_tokens = _estimate_tokens(chunk.content)
        same_h1 = _chunk_h1_title(chunk) == bucket_h1
        fits_budget = bucket_tokens + chunk_tokens <= max_tokens
        if same_h1 and fits_budget:
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
                )
            )
            bucket_titles = [chunk.title]
            bucket_content = [chunk.content]
            bucket_tokens = chunk_tokens
            bucket_h1 = _chunk_h1_title(chunk)
    # Flush the last bucket.
    merged.append(
        RuleChunk(
            title=" / ".join(bucket_titles),
            content="\n\n".join(bucket_content),
            order=len(merged),
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
    _LOG.debug(
        hprint.to_str("level max_tokens merge_small_rules")
    )
    # Split every rule file's H1 sections into chunks at `level`.
    rule_files = topic_info["rules"]
    all_sections: List[Tuple[str, str]] = []
    for rule_file in rule_files:
        hdbg.dassert_file_exists(rule_file, "Rule file not found")
        lines = hio.from_file(rule_file).split("\n")
        all_sections.extend(
            hmarhead.extract_sections_at_level(lines, level=level)
        )
    chunks = [
        RuleChunk(title=title, content=content, order=idx)
        for idx, (title, content) in enumerate(all_sections)
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
            "Relevance filter selected zero chunks; keeping all %d "
            "chunk(s)",
            len(chunks),
        )
        return chunks
    kept = [
        dataclasses.replace(chunk, order=idx)
        for idx, chunk in enumerate(kept)
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
# Prompt Building
# #############################################################################


def _build_prompt(topic: str) -> Tuple[str, Dict]:
    """
    Build a Claude Code prompt for the given skill.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :return: Tuple of (prompt string, topic_info dict)
    """
    _LOG.debug("Building prompt for topic: '%s'", topic)
    topic_info = _get_rules_for_topic(topic)
    role = topic_info["role"]
    rules = topic_info["rules"]
    templates = topic_info["templates"]
    prompt_parts = []
    hdbg.dassert_file_exists(role, "Role file not found")
    role_content = hio.from_file(role)
    prompt_parts.append(role_content)
    if rules:
        prompt_parts.append(
            "You MUST look for each rule below that is not followed and apply them:"
        )
        for rule_file in rules:
            prompt_parts.append(f"- {rule_file}")
    if templates:
        prompt_parts.append("You MUST follow the templates below:")
        for template_file in templates:
            prompt_parts.append(f"- {template_file}")
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
    _LOG.debug(
        hprint.to_str("prompt topic file_path dry_run model")
    )
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
    _LOG.info("\n%s\n%s", hprint.frame("Prompt (%s):") % topic, prompt)
    _LOG.info("Claude command: %s", cmd)
    hsystem.system(cmd)
    _LOG.debug("return=0")
    return 0


# #############################################################################
# File Processing
# #############################################################################


def _build_incremental_system_prompt(topic_info: Dict) -> str:
    """
    Build the system prompt for incremental rule application.

    The role and the "do not change behavior" instruction are sent once as
    the system prompt instead of being repeated in a message, since they
    apply to every rule turn.

    :param topic_info: topic configuration dict from `_get_rules_for_topic()`
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
    templates = topic_info["templates"]
    if templates:
        msg = "You MUST follow the templates below:"
        system_prompt.append(msg)
        for template_file in templates:
            system_prompt.append(f"- {template_file}")
    #
    system_prompt_as_str = "\n".join(system_prompt)
    _LOG.debug(hprint.to_str("system_prompt_as_str"))
    return system_prompt_as_str


def _build_rule_message(file_path: str, rule_content: str) -> str:
    """
    Build one rule message re-anchored on `file_path` with the no-op contract.

    Naming `file_path` in every message keeps its referent from drifting
    once the context holds several rule sections; the no-op contract lets a
    compliant rule produce zero edits instead of forced churn.

    :param file_path: path of the file the rule applies to
    :param rule_content: H1 rule section content to apply
    :return: prompt text requiring a structured `LLM> NO-OP` or `LLM>
        CHANGED: <summary>` reply
    """
    rule_message: List[str] = []
    header = f"""
    - Re-read `{file_path}` from disk
    - Apply ONLY the rule below to `{file_path}`
    - Do not revisit rules applied earlier
    """
    rule_message.append(hprint.dedent(header))
    #
    rule_message.append("```")
    rule_message.append(rule_content)
    rule_message.append("```")
    #
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
) -> List[str]:
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
    :return: one message per rule chunk; the role and the "do not change
        behavior" instruction live in the system prompt instead (see
        `_build_incremental_system_prompt()`)
    """
    _LOG.debug(
        hprint.to_str(
            "file_path level max_tokens merge_small_rules "
            "filter_rules_by_relevance order_rules_by_dependency"
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
    messages = [
        _build_rule_message(file_path, chunk.content) for chunk in chunks
    ]
    _LOG.debug("return=%d messages", len(messages))
    return messages


def _build_incremental_messages_for_rule(
    file_path: str, rule_content: str
) -> List[str]:
    """
    Build incremental rule messages for a `--rule` specification.

    A whole-file rule spec (`path/to/rules.md`) can carry more than one H1
    section, so it is split into one chunk per section, like the `--topic`
    path.
    A line-anchored spec (`path/to/rules.md:N`) already extracts a single
    section, so it is kept as one chunk.

    :param file_path: path of the file to apply the rule to
    :param rule_content: rule text from `hmarsele.extract_rule_from_file()`
    :return: one message per H1 section in `rule_content`, or a single
        message when it has zero or one H1 section
    """
    _LOG.debug(hprint.to_str("file_path"))
    lines = rule_content.split("\n")
    sections = hmarhead.extract_h1_sections_from_lines(lines)
    if len(sections) > 1:
        contents = [section_content for _, section_content in sections]
    else:
        contents = [rule_content]
    messages = [_build_rule_message(file_path, content) for content in contents]
    _LOG.debug("return=%d messages", len(messages))
    return messages


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
) -> int:
    """
    Apply rules incrementally, one chunk per Claude Code interaction.

    The chunks sent depend on which "what" was specified, mirroring the
    `--topic`/`--skill`/`--rule`/default dispatch of the `one_shot` path:
    - `skill`: a single, non-decomposed `/{skill} {file_path}` slash-command
      chunk, since it is a command for Claude Code's own skill loader, not
      declarative rule prose to split
    - `rule`: the rule text from `hmarsele.extract_rule_from_file()`, split
      into H1 sections when it has more than one, else kept as a single
      chunk (see `_build_incremental_messages_for_rule()`)
    - neither: one `RuleChunk` per section across `topic_info["rules"]`,
      shaped by `rule_level`/`max_chunk_tokens`/`merge_small_rules`/
      `filter_rules_by_relevance`/`order_rules_by_dependency` (see
      `_build_incremental_messages()`)

    :param file_path: Path to the file to process
    :param dry_run: If True, print messages without executing
    :param model: Model to use for Claude invocation (used via SDK
        configuration, and for the `filter_rules_by_relevance`/
        `order_rules_by_dependency` pre-passes)
    :param context_strategy: `"stateless"` for a fresh session per chunk, or
        `"session"` for a single session shared across all chunks (i.e.,
        `--mode` when it is not `"one_shot"`)
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
    :return: Return code (0 on success)
    """
    _LOG.debug(
        hprint.to_str(
            "file_path dry_run model context_strategy skill rule "
            "rule_level max_chunk_tokens merge_small_rules "
            "filter_rules_by_relevance order_rules_by_dependency"
        )
    )
    hdbg.dassert_file_exists(file_path)
    system_prompt = _build_incremental_system_prompt(topic_info)
    if skill:
        # A skill invocation is a single command for Claude Code's own skill
        # loader, kept as-is instead of being split into rule chunks.
        full_skill_name = hmarsele.find_skill(skill)
        messages = [f"/{full_skill_name} {file_path}"]
    elif rule:
        rule_content = hmarsele.extract_rule_from_file(rule)
        messages = _build_incremental_messages_for_rule(
            file_path, rule_content
        )
    else:
        messages = _build_incremental_messages(
            file_path,
            topic_info,
            level=rule_level,
            max_tokens=max_chunk_tokens,
            merge_small_rules=merge_small_rules,
            filter_rules_by_relevance=filter_rules_by_relevance,
            order_rules_by_dependency=order_rules_by_dependency,
            model=model,
        )
    # Handle dry run.
    if dry_run:
        # Save the full, untrimmed dry-run output to a file instead of
        # printing it to screen.
        dry_run_output = ["Dry Run - System prompt and messages to be sent:"]
        dry_run_output.append(
            "\n%s\n%s" % (hprint.frame("System prompt:"), system_prompt)
        )
        for idx, msg in enumerate(messages, 1):
            dry_run_output.append(
                "\n%s\n%s"
                % (hprint.frame(f"Message {idx}/{len(messages)}:"), msg)
            )
        hio.to_file(_DRY_RUN_FILE, "\n".join(dry_run_output))
        _LOG.warning("Saved dry-run output to '%s'", _DRY_RUN_FILE)
        _LOG.debug("return=0 (dry_run)")
        return 0
    # Execute messages using PromptSequencer.
    _LOG.info(
        "Executing %d messages with '%s' context strategy",
        len(messages),
        context_strategy,
    )
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
        )
        await sequencer.execute(messages)
        stats = sequencer.get_execution_stats()
        _LOG.info("Execution completed: %s", stats)
        for idx, outcome in enumerate(sequencer.get_outcomes(), 1):
            _LOG.info("Rule %d/%d outcome: %s", idx, len(messages), outcome)
        _LOG.debug("return=0")
        return 0
    except Exception as e:
        _LOG.error("Sequential execution failed: %s", str(e))
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
    topic_info = {}
    if args.mode != "one_shot":
        # Apply rules incrementally via async processor, with `args.mode`
        # ("session" or "stateless") selecting the context strategy, and
        # `args.skill`/`args.rule`/`args.topic` selecting the "what"
        # (mirroring the topic/skill/rule/default dispatch below).
        if args.topic:
            topic_str = args.topic
        else:
            topic_str = _infer_topic_from_filename(file_path)
        topic_info = _get_rules_for_topic(topic_str)
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
            )
        )
    elif args.skill:
        # Execute a specific skill on the file.
        full_skill_name = hmarsele.find_skill(args.skill)
        prompt = f"/{full_skill_name} {file_path}"
        topic_str = "skill"
        inferred_topic = _infer_topic_from_filename(file_path)
        topic_info = _get_rules_for_topic(inferred_topic)
        rc = _run_claude_code(
            prompt,
            topic_str,
            file_path,
            dry_run=args.dry_run,
            model=args.model,
        )
    elif args.rule:
        # Execute a specific rule on the file.
        _LOG.debug("Executing rule: %s", args.rule)
        rule_content = hmarsele.extract_rule_from_file(args.rule)
        prompt = f"Execute the rule below on file {file_path}:\n{rule_content}"
        #
        topic_str = "rule"
        inferred_topic = _infer_topic_from_filename(file_path)
        topic_info = _get_rules_for_topic(inferred_topic)
        #
        rc = _run_claude_code(
            prompt,
            topic_str,
            file_path,
            dry_run=args.dry_run,
            model=args.model,
        )
    else:
        # Infer topic from file and build prompt from topic rules.
        if args.topic:
            topic_str = args.topic
            prompt, topic_info = _build_prompt(topic_str)
        else:
            topic = _infer_topic_from_filename(file_path)
            hdbg.dassert_is_not(topic, None, "Topic detection failed")
            topic_str = cast(str, topic)
        prompt, topic_info = _build_prompt(topic_str)
        prompt += (
            f"\n\nProcess the file {file_path} and make the changes "
            + "according to the rules and conventions without asking "
            + "questions to the user"
        )
        rc = _run_claude_code(
            prompt,
            topic_str,
            file_path,
            dry_run=args.dry_run,
            model=args.model,
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        default="one_shot",
        choices=["one_shot", "session", "stateless"],
        help=hprint.dedent("""
        Execution mode:
        - 'one_shot' applies all rules in a single "Claude Code invocation
        - 'session' and 'stateless' apply rules incrementally, one H1 section
          per Claude Code interaction, sharing one session across all chunks
          ('session') or opening a fresh session per chunk ('stateless')
        """)
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
        "--dry_run",
        action="store_true",
        help=f"Save the command to '{_DRY_RUN_FILE}' instead of executing",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Optional model name to use using cc conventions",
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
