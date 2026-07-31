#!/usr/bin/env python

"""
Extract a human-readable narrative from a Claude Code streaming JSON log.

Parses `log.txt` and produces a chronological transcript interleaving
thinking blocks, tool calls, results, and cost per request.

Usage:
> ./extract_cc_log.py --file log.txt
> ./extract_cc_log.py --file log.txt --output_dir /tmp
> ./extract_cc_log.py --file log.txt --output_dir /tmp --text_only
"""

import argparse
import json
import logging
import os
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

# Default path to the Claude Code log file.
DEFAULT_LOG_FILE = "log.txt"


# #############################################################################
# Helper functions
# #############################################################################


def _parse_records(log_file: str) -> List[Dict[str, Any]]:
    """
    Parse each line of the log file as a JSON object.

    Skips non-JSON lines (e.g., shell command headers, env vars), reporting
    the count of skipped lines in debug output.

    :param log_file: Path to the log file to parse
    :return: List of parsed JSON record dicts
    """
    _LOG.debug("Parsing records from '%s'", log_file)
    hdbg.dassert_file_exists(log_file, "Log file must exist")
    records: List[Dict[str, Any]] = []
    skipped = 0
    with open(log_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError:
                _LOG.debug(
                    "Skipping non-JSON line %d: '%s'", line_num, line[:60]
                )
                skipped += 1
    _LOG.info("Parsed '%d' JSON records from '%s'", len(records), log_file)
    _LOG.debug("Skipped '%d' non-JSON lines", skipped)
    return records


def _get_record_counts(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count records by type and subtype.

    Groups `stream_event` records by their `.event.type` and `system` records
    by their `.subtype`, using the top-level `type` field for all others.

    :param records: Parsed JSON records from the log file
    :return: Dict mapping record type labels to counts
        ```
        {"system/init": 1, "system/status": 2, "stream_event/message_start": 2}
        ```
    """
    counts: Dict[str, int] = {}
    for rec in records:
        t = rec.get("type", "MISSING")
        if t == "stream_event":
            event_type = rec.get("event", {}).get("type", "MISSING")
            key = f"stream_event/{event_type}"
        elif t == "system":
            subtype = rec.get("subtype", "MISSING")
            key = f"system/{subtype}"
        else:
            key = t
        counts[key] = counts.get(key, 0) + 1
    return counts


def _extract_init_info(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract session initialization metadata.

    Finds the first `system/init` record and returns its key configuration
    fields.

    :param records: Parsed JSON records from the log file
    :return: Dict with session metadata
        ```
        {
            "session_id": "fdac299b-...",
            "model": "deepseek/deepseek-v4-flash",
            "claude_code_version": "2.1.173",
            "permissionMode": "bypassPermissions"
        }
        ```
    """
    info: Dict[str, Any] = {}
    for rec in records:
        if rec.get("type") == "system" and rec.get("subtype") == "init":
            info = {
                "session_id": rec.get("session_id", ""),
                "model": rec.get("model", ""),
                "claude_code_version": rec.get("claude_code_version", ""),
                "permissionMode": rec.get("permissionMode", ""),
            }
            break
    return info


def _extract_requests(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract per-request start and delta records.

    Pairs each `message_start` with its corresponding `message_delta` by
    matching across records in order. A `message_stop` record separates one
    request from the next.

    :param records: Parsed JSON records from the log file
    :return: List of request info dicts with start and delta data
        ```
        [
            {
                "message_id": "gen-...",
                "model": "deepseek/...",
                "provider": "Alibaba",
                "ttft_ms": 7907,
                "input_tokens": 26451,
                "output_tokens": 320,
                "thinking_tokens": 62,
                "cost": 0.003630,
                "speed": "standard"
            }
        ]
        ```
    """
    requests: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for rec in records:
        if rec.get("type") != "stream_event":
            continue
        event = rec.get("event", {})
        event_type = event.get("type", "")
        if event_type == "message_start":
            msg = event.get("message", {})
            current = {
                "message_id": msg.get("id", ""),
                "model": msg.get("model", ""),
                "provider": msg.get("provider", ""),
                "ttft_ms": rec.get("ttft_ms", 0),
            }
        elif event_type == "message_delta":
            usage = event.get("usage", {})
            current["input_tokens"] = usage.get("input_tokens", 0)
            current["output_tokens"] = usage.get("output_tokens", 0)
            output_details = usage.get("output_tokens_details", {})
            current["thinking_tokens"] = output_details.get("thinking_tokens", 0)
            current["cost"] = usage.get("cost", 0)
            current["speed"] = usage.get("speed", "")
            requests.append(dict(current))
        elif event_type == "message_stop":
            current = {}
    return requests


def _extract_thinking_timeline(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract thinking token progression records.

    Captures each `system/thinking_tokens` record with its estimated token
    count and per-block delta.

    :param records: Parsed JSON records from the log file
    :return: List of thinking token info dicts
        ```
        [
            {"estimated_tokens": 1, "estimated_tokens_delta": 1},
            {"estimated_tokens": 4, "estimated_tokens_delta": 3}
        ]
        ```
    """
    thinking_records: List[Dict[str, Any]] = []
    for rec in records:
        if (
            rec.get("type") == "system"
            and rec.get("subtype") == "thinking_tokens"
        ):
            thinking_records.append(
                {
                    "estimated_tokens": rec.get("estimated_tokens", 0),
                    "estimated_tokens_delta": rec.get(
                        "estimated_tokens_delta", 0
                    ),
                }
            )
    return thinking_records


def _reconstruct_stream(
    records: List[Dict[str, Any]],
    *,
    stream_type: str,
) -> List[Dict[str, Any]]:
    """
    Reconstruct full content blocks from streaming delta events.

    Groups consecutive `content_block_delta` events by their `index` field
    within each request (bounded by `message_start`/`message_stop`) and joins
    their delta text. Supports `thinking_delta` and `text_delta` stream types.

    :param records: Parsed JSON records from the log file
    :param stream_type: Delta type to reconstruct, e.g. `"thinking_delta"` or
        `"text_delta"`
    :return: List of assembled content block dicts, each with:
        ```
        {"index": 0, "text": "...full assembled text..."}
        ```
    """
    assembled: List[Dict[str, Any]] = []
    current_block: Dict[str, Any] = {}
    in_message = False
    for rec in records:
        if rec.get("type") != "stream_event":
            continue
        event = rec.get("event", {})
        event_type = event.get("type", "")
        if event_type == "message_start":
            # Flush any in-progress block.
            if current_block:
                assembled.append(dict(current_block))
                current_block = {}
            in_message = True
        elif event_type == "message_stop":
            # Flush the final block.
            if current_block:
                assembled.append(dict(current_block))
                current_block = {}
            in_message = False
        elif event_type == "content_block_delta" and in_message:
            delta = event.get("delta", {})
            if delta.get("type") == stream_type:
                block_index = event.get("index", 0)
                text = delta.get(
                    "thinking" if stream_type == "thinking_delta" else "text",
                    "",
                )
                # Start a new block or append to the current one.
                if (
                    not current_block
                    or current_block.get("index") != block_index
                ):
                    if current_block:
                        assembled.append(dict(current_block))
                    current_block = {"index": block_index, "text": text}
                else:
                    current_block["text"] += text
        elif event_type == "content_block_start" and in_message:
            # A new content block starting resets the delta accumulator.
            block_index = event.get("index", 0)
            block = event.get("content_block", {})
            if block.get("type") == stream_type.replace("_delta", ""):
                if current_block:
                    assembled.append(dict(current_block))
                current_block = {"index": block_index, "text": ""}
    # Flush any remaining block.
    if current_block:
        assembled.append(dict(current_block))
    return assembled


def _extract_assistant_text_blocks(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract full-text content from assistant messages.

    Collects both:
    - Complete `text` blocks from `assistant` type records
    - Reconstructed text from `text_delta` stream events

    :param records: Parsed JSON records from the log file
    :return: List of text content dicts with source and text
        ```
        [
            {"source": "assistant_block", "text": "..."},
            {"source": "stream_reconstructed", "index": 0, "text": "..."}
        ]
        ```
    """
    blocks: List[Dict[str, Any]] = []
    # Collect complete text blocks from assistant messages.
    for rec in records:
        if rec.get("type") == "assistant":
            for block in rec.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    blocks.append(
                        {
                            "source": "assistant_block",
                            "text": block.get("text", ""),
                        }
                    )
    # Reconstruct text from stream deltas.
    stream_blocks = _reconstruct_stream(records, stream_type="text_delta")
    for sb in stream_blocks:
        sb["source"] = "stream_reconstructed"
        blocks.append(dict(sb))
    return blocks


def _extract_thinking_blocks(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract thinking content from assistant messages and stream events.

    Collects both:
    - Complete `thinking` blocks from `assistant` type records
    - Reconstructed thinking from `thinking_delta` stream events

    :param records: Parsed JSON records from the log file
    :return: List of thinking content dicts with source and text
        ```
        [
            {"source": "assistant_block", "text": "..."},
            {"source": "stream_reconstructed", "index": 0, "text": "..."}
        ]
        ```
    """
    blocks: List[Dict[str, Any]] = []
    # Collect complete thinking blocks from assistant messages.
    for rec in records:
        if rec.get("type") == "assistant":
            for block in rec.get("message", {}).get("content", []):
                if block.get("type") == "thinking":
                    blocks.append(
                        {
                            "source": "assistant_block",
                            "text": block.get("thinking", ""),
                        }
                    )
    # Reconstruct thinking from stream deltas.
    stream_blocks = _reconstruct_stream(records, stream_type="thinking_delta")
    for sb in stream_blocks:
        sb["source"] = "stream_reconstructed"
        blocks.append(dict(sb))
    return blocks


def _extract_tool_calls(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract assistant tool calls and user tool results in chronological order.

    Captures each `assistant` record's `tool_use` blocks and each `user`
    record's `tool_result` blocks, preserving the order they appear in the
    log.

    :param records: Parsed JSON records from the log file
    :return: List of tool event dicts with direction, tool name, and summary
        ```
        [
            {"direction": "call", "tool_name": "WebFetch", "id": "call_...", "summary": "..."},
            {"direction": "result", "tool_name": "", "id": "call_...", "is_error": false, "summary": "..."}
        ]
        ```
    """
    events: List[Dict[str, Any]] = []
    for rec in records:
        t = rec.get("type", "")
        if t == "assistant":
            msg = rec.get("message", {})
            content = msg.get("content", [])
            for block in content:
                if block.get("type") == "tool_use":
                    inp = block.get("input", {})
                    inp_summary = json.dumps(inp)[:80]
                    events.append(
                        {
                            "direction": "call",
                            "tool_name": block.get("name", ""),
                            "id": block.get("id", ""),
                            "summary": inp_summary,
                        }
                    )
        elif t == "user":
            msg = rec.get("message", {})
            content = msg.get("content", [])
            for block in content:
                if block.get("type") == "tool_result":
                    res_content = block.get("content", "")
                    content_type = type(res_content).__name__
                    content_len = (
                        len(res_content)
                        if isinstance(res_content, str)
                        else len(res_content)
                    )
                    events.append(
                        {
                            "direction": "result",
                            "tool_name": "",
                            "id": block.get("tool_use_id", ""),
                            "is_error": block.get("is_error", False),
                            "content_type": content_type,
                            "content_len": content_len,
                            "url": block.get("url", ""),
                            "duration_ms": block.get("durationMs", 0),
                        }
                    )
    return events


def _write_output(
    output: str,
    file_name: str,
    *,
    output_dir: str = "",
) -> None:
    """
    Print output and optionally write to a file.

    :param output: String content to print and optionally save
    :param file_name: File name to save under `output_dir`
    :param output_dir: Optional directory to write the output file
    """
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "w") as f:
            f.write(output)
        _LOG.info("Output written to '%s'", file_path)
    print(output)


# #############################################################################
# Output functions
# #############################################################################


def _print_narrative(
    records: List[Dict[str, Any]],
    *,
    output_dir: str = "",
    text_only: bool = False,
) -> None:
    """
    Print a chronological narrative of the Claude Code session.

    Interleaves thinking blocks, tool calls, results, and cost per request
    in the order they occurred. When `text_only` is True, only the assistant
    text messages are printed.

    :param records: Parsed JSON records from the log file
    :param output_dir: Optional directory to write the narrative output
    :param text_only: If True, only print assistant text messages
    """
    init_info = _extract_init_info(records)
    requests = _extract_requests(records)
    thinking_blocks = _extract_thinking_blocks(records)
    text_blocks = _extract_assistant_text_blocks(records)
    tool_events = _extract_tool_calls(records)

    lines: List[str] = []

    # Header.
    if init_info:
        model = init_info.get("model", "")
        cc_ver = init_info.get("claude_code_version", "")
        session_id = init_info.get("session_id", "")[:8]
        lines.append(f"=== Session: {session_id} | {model} | CC {cc_ver} ===")
    else:
        lines.append("=== Claude Code Session ===")

    # --- Text-only mode: just the assistant text output ---
    if text_only:
        lines.append("")
        lines.append("-" * 60)
        lines.append("ASSISTANT TEXT")
        lines.append("-" * 60)
        lines.append("")
        seen_text: set = set()
        for tb in text_blocks:
            text = tb.get("text", "")
            if text.strip() and text not in seen_text:
                seen_text.add(text)
                lines.append(text)
                lines.append("")
        output = "\n".join(lines)
        _write_output(output, "cc_log_assistant_text.txt", output_dir=output_dir)
        return

    # --- Full narrative mode ---
    lines.append("")
    lines.append("-" * 60)
    lines.append("NARRATIVE")
    lines.append("-" * 60)
    lines.append("")

    # Pre-extract thinking text in order.
    thinking_texts: List[str] = []
    for tb in thinking_blocks:
        text = tb.get("text", "")
        if text.strip():
            thinking_texts.append(text)
    # Pre-extract assistant text in order.
    assistant_texts: List[str] = []
    seen_text: set = set()
    for tb in text_blocks:
        text = tb.get("text", "")
        if text.strip() and text not in seen_text:
            seen_text.add(text)
            assistant_texts.append(text)

    # Walk through records in chronological order emitting events.
    msg_num = 0
    think_idx = 0
    text_idx = 0
    in_message = False
    for rec in records:
        if rec.get("type") != "stream_event":
            continue
        event = rec.get("event", {})
        event_type = event.get("type", "")
        if event_type == "message_start":
            msg_num += 1
            req = requests[msg_num - 1] if msg_num - 1 < len(requests) else {}
            provider = req.get("provider", "?")
            ttft = req.get("ttft_ms", "?")
            lines.append(
                f"--- Message {msg_num} ({provider}, {ttft}ms TTFT) ---"
            )
            in_message = True
        elif event_type == "message_delta":
            usage = event.get("usage", {})
            cost = usage.get("cost", 0)
            inp = usage.get("input_tokens", 0)
            out = usage.get("output_tokens", 0)
            think = usage.get("output_tokens_details", {}).get(
                "thinking_tokens", 0
            )
            lines.append(
                f"  [Cost] {inp} in, {out} out, {think} think, ${cost:.6f}"
            )
            lines.append("")
        elif event_type == "message_stop":
            in_message = False

        # When a content block stops, check if it was a thinking block.
        if event_type == "content_block_stop" and in_message:
            if think_idx < len(thinking_texts):
                text = thinking_texts[think_idx]
                lines.append("  [Think] " + text.replace("\n", "\n          "))
                lines.append("")
                think_idx += 1

    # Emit tool calls paired with their results.
    lines.append("")
    lines.append("Tools:")
    unmatched_calls: Dict[str, Dict] = {}
    for ev in tool_events:
        if ev["direction"] == "call":
            unmatched_calls[ev["id"]] = ev
        else:
            call_ev = unmatched_calls.pop(ev["id"], None)
            tool_name = call_ev["tool_name"] if call_ev else "?"
            inp_summary = call_ev["summary"] if call_ev else "?"
            err = "ERROR" if ev.get("is_error") else "OK"
            content_type = ev.get("content_type", "")
            content_len = ev.get("content_len", 0)
            url = ev.get("url", "")
            dur = ev.get("duration_ms", 0)
            if len(inp_summary) > 120:
                inp_summary = inp_summary[:120] + "..."
            lines.append("  " + tool_name + "(" + inp_summary + ")")
            detail = (
                "    -> ("
                + err
                + ", "
                + content_type
                + ", "
                + str(content_len)
                + " chars)"
            )
            if url:
                detail += " url=" + url
            if dur:
                detail += " duration=" + str(dur) + "ms"
            lines.append(detail)

    # Append assistant text at the end.
    lines.append("")
    lines.append("-" * 60)
    lines.append("ASSISTANT TEXT")
    lines.append("-" * 60)
    lines.append("")
    for tb in text_blocks:
        text = tb.get("text", "")
        if text.strip():
            lines.append(text)
            lines.append("")

    output = "\n".join(lines)
    _write_output(output, "cc_log_narrative.txt", output_dir=output_dir)


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        action="store",
        default=DEFAULT_LOG_FILE,
        help="Path to the Claude Code log file to parse",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        default="",
        help="Directory to write narrative output (default: print only)",
    )
    # Extraction options.
    parser.add_argument(
        "--text_only",
        action="store_true",
        help="Only print the assistant text messages, no narrative",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse the log file.
    records = _parse_records(args.file)
    # Print a chronological narrative.
    _print_narrative(
        records,
        output_dir=args.output_dir,
        text_only=args.text_only,
    )


if __name__ == "__main__":
    _main(_parse())
