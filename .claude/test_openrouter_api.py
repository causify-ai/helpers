#!/usr/bin/env python
import os
import sys
from anthropic import Anthropic

BASE_URL = os.environ["ANTHROPIC_BASE_URL"]
API_KEY = os.environ["ANTHROPIC_AUTH_TOKEN"]
MODEL = os.environ["ANTHROPIC_DEFAULT_HAIKU_MODEL"]

if not API_KEY:
    print("ERROR: ANTHROPIC_AUTH_TOKEN is not set")
    sys.exit(1)

print(f"Endpoint : {BASE_URL}")
print(f"Model    : {MODEL}")
print("Testing...\n")

try:
    client = Anthropic(
        api_key=API_KEY,
        base_url=BASE_URL,
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=20,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: API_OK"
            }
        ],
    )
    text = "".join(
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text"
    )
    print("SUCCESS")

except Exception as e:
    print("FAILED")
    sys.exit(2)
