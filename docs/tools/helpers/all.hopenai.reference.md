# hopenai.get_completion – Reference

<!-- toc -->

- [Function Overview](#function-overview)
- [Signature](#signature)
- [Parameters](#parameters)
- [Returns](#returns)
- [Cache Modes](#cache-modes)
- [Exceptions](#exceptions)
- [Related Utilities](#related-utilities)

<!-- tocstop -->

## Function Overview

The `get_completion()` function is a high-level wrapper around OpenAI or
OpenRouter language model APIs. It provides optional caching, cost logging, and
response processing logic.

Its primary purpose is to send a structured prompt to a model and return its
textual output, while optionally handling caching and tracking API costs.

## Signature

```python
def get_completion(
    user_prompt: str,
    *,
    system_prompt: str = "",
    model: str = "",
    report_progress: bool = False,
    print_cost: bool = False,
    cache_mode: str = "DISABLED",
    cache_file: str = "cache.get_completion.json",
    temperature: float = 0.1,
    **create_kwargs,
) -> str
```

## Parameters

| Name              | Type  | Required | Description                                                 |
| ----------------- | ----- | -------- | ----------------------------------------------------------- |
| `user_prompt`     | str   | ✅       | The user's input message to the LLM                         |
| `system_prompt`   | str   | ❌       | System message that sets assistant behavior                 |
| `model`           | str   | ❌       | Model to use (`gpt-4`, `openrouter/mistral`, etc.)          |
| `report_progress` | bool  | ❌       | Prints debug information if enabled                         |
| `print_cost`      | bool  | ❌       | Outputs estimated cost to console                           |
| `cache_mode`      | str   | ❌       | One of: `"DISABLED"`, `"REPLAY"`, `"FALLBACK"`, `"CAPTURE"` |
| `cache_file`      | str   | ❌       | Path to cache JSON file                                     |
| `temperature`     | float | ❌       | Sampling temperature (controls randomness)                  |
| `**create_kwargs` | dict  | ❌       | Extra keyword arguments forwarded to the model API          |

## Returns

- `str`: The final message content from the model's response.

## Cache Modes

| Mode       | Description                                                                   |
| ---------- | ----------------------------------------------------------------------------- |
| `DISABLED` | Caching is ignored entirely.                                                  |
| `REPLAY`   | Loads response from cache only. Raises error if not found.                    |
| `FALLBACK` | Returns cached result if present; otherwise makes API call and updates cache. |
| `CAPTURE`  | Forces new API call and overwrites cache entry.                               |

## Exceptions

| Exception         | When it Occurs                                                    |
| ----------------- | ----------------------------------------------------------------- |
| `KeyError`        | When cache mode is `REPLAY` and entry is missing                  |
| `ValueError`      | When an unknown cache mode is passed                              |
| API-related error | If the model call fails (e.g. connection error, rate limit, etc.) |

## Related Utilities

- `_CompletionCache`: Manages reading, writing, and lookup of cache entries
- `_calculate_cost()`: Computes cost based on token usage and model type
- `start_logging_costs()`, `get_current_cost()`: For accumulating and inspecting
  session cost totals
