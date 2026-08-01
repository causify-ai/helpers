#!/usr/bin/env python3 -u

import sys
import json
import subprocess

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    sys.stderr.write(".")
    sys.stderr.flush()

    try:
        obj = json.loads(line)
        if obj.get("type") != "assistant":
            continue

        for content in obj.get("message", {}).get("content", []):
            if content.get("type") == "thinking":
                print(f"=== THINKING ===\n{content.get('thinking', '')}\n")
            elif content.get("type") == "text":
                print(f"=== ASSISTANT ===\n{content.get('text', '')}\n")
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

sys.stderr.write("\n")
sys.stderr.flush()
