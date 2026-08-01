#!/usr/bin/env python3 -u

import sys
import json

current_type = None
first_delta = {"thinking": True, "text": True}

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    # sys.stderr.write(".")
    # sys.stderr.flush()

    try:
        obj = json.loads(line)

        # Handle stream events with deltas
        if obj.get("type") == "stream_event":
            event = obj.get("event", {})

            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                delta_type = delta.get("type")

                if delta_type == "thinking_delta":
                    if current_type != "thinking":
                        if first_delta["thinking"]:
                            first_delta["thinking"] = False
                        else:
                            print()  # blank line between blocks
                        print("\n=== THINKING ===\n", end="", flush=True)
                        current_type = "thinking"

                    content = delta.get("thinking", "")
                    print(content, end="", flush=True)

                elif delta_type == "text_delta":
                    if current_type != "text":
                        if first_delta["text"]:
                            first_delta["text"] = False
                        else:
                            print()  # blank line between blocks
                        print("\n=== ASSISTANT ===\n", end="", flush=True)
                        current_type = "text"

                    content = delta.get("text", "")
                    print(content, end="", flush=True)

    except (json.JSONDecodeError, KeyError, TypeError):
        pass

print()  # final newline
# sys.stderr.write("\n")
# sys.stderr.flush()
