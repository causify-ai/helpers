# hopenai – Explanation

<!-- toc -->

- [Overview](#overview)
- [Guide](#guide)
  * [Parameters](#parameters)
- [Reference](#reference)
  * [Function Signature](#function-signature)
- [Explanation](#explanation)
  * [Caching Logic](#caching-logic)
    + [Key Generation](#key-generation)
    + [Cache Storage Format](#cache-storage-format)
    + [Disk I/O](#disk-io)
  * [Cost Calculation](#cost-calculation)
    + [OpenAI Models](#openai-models)
    + [OpenRouter Models](#openrouter-models)
    + [Runtime Behavior](#runtime-behavior)
  * [Entire Flow](#entire-flow)
- [How Testing Works](#how-testing-works)
- [Cache Refreshing](#cache-refreshing)
  * [What This Does](#what-this-does)
    + [When to Use](#when-to-use)

<!-- tocstop -->

# Overview

- `hopenai.get_completion()` is a helper function that sends prompts to LLMs
  (OpenAI or OpenRouter) and returns their responses
- It includes a custom caching mechanism to reduce redundant requests and allow
  unit testing

- An example call to the LLM interface is
  ```python
  from helpers import hopenai

  response = hopenai.get_completion(
      user_prompt="What is machine learning?",
      system_prompt="You are a helpful assistant.",
      model="gpt-4o-mini",
      cache_mode="FALLBACK",
      cache_file="cache.get_completion.json",
      temperature=0.5
  )
  ```

- The parameter used are:
  - `user_prompt`: User's message to the LLM.
  - `system_prompt`: Context-setting instruction for the assistant.
  - `model`: OpenAI or OpenRouter model to use.
  - `cache_mode`: One of:
    - `"DISABLED"`: No caching.
    - `"REPLAY"`: Only use cached response; raise error if not found.
    - `"FALLBACK"`: Use cache if available, else make an API call.
    - `"CAPTURE"`: Always make an API call and update the cache.
  - `cache_file`: Path to JSON cache file.
  - `temperature`: Sampling temperature (0-2).
  - `**create_kwargs`: Additional arguments passed to the API.

## Caching Logic

- The caching mechanism uses a hashed key generated from:
  - `user_prompt`
  - `system_prompt`
  - `model`
  - `temperature`
  - Additional parameters

- The caching layer
  - Reads from `cache_file` on load
  - Writes to disk when cache is updated
  - Tracks metadata:
    - `hits` : Number of times the cache returned a value.
    - `misses`: Number of times the function looked for response in cache but
      didn't find
    - timestamps : Stores both `created_at` and `last_updated` timestamps.

- The cache storage format:
  ```json
  {
    "version": "1.0",
    "metadata": {
      "created_at": "...",
      "last_updated": "...",
      "hits": 10,
      "misses": 5
    },
    "entries": {
      "<hash_key>": {
        "request": { ... },
        "response": { ... }
      }
    }
  }
  ```

## Cost Calculation

### OpenAI Models

- For OpenAI models like `gpt-4o` or `gpt-3.5-turbo`, the cost is computed using
  hardcoded pricing from [OpenAI's pricing page](https://openai.com/api/pricing)
- Each model has a per-token price for both the **prompt** and **completion**
  components:

  ```python
  pricing = {
      "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
      "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
      ...
  }
  ```

- The formula used is:
  ```text
  cost = (prompt_tokens / 1e6) * prompt_price + (completion_tokens / 1e6) * completion_price
  ```

### OpenRouter Models

- For OpenRouter models the price is extracted through the API
  1. If the local file `tmp.openrouter_models_info.csv` does not exist:
     - It queries `https://openrouter.ai/api/v1/models`
     - Saves the returned model pricing and metadata to a CSV file
  2. The cost is computed using:
     ```python
     cost = prompt_tokens * prompt_price + completion_tokens * completion_price
     ```
     - Note: OpenRouter prices are already in per-token format.

### Runtime Behavior

- The cost is printed if `print_cost=True`
- It's also stored in the cache JSON under `response["cost"]`
- All costs (if `start_logging_costs()` is called) accumulate in a global
  counter accessible via `get_current_cost()`

## Entire Flow

This section summarizes how `get_completion()` operates internally.

1. **Input Handling**
   - Accepts `user_prompt`, `system_prompt`, `model`, `cache_mode`, and other
     parameters.
   - Builds OpenAI-compatible `messages` list.

2. **Cache Key Creation**
   - Calls `_CompletionCache.hash_key_generator()` using model, prompts, and
     parameters to produce a unique hash key.

3. **Cache Behavior**
   - If `cache_mode == "REPLAY"`:
     - Looks up the response using hash key.
     - If not found, raises an error.
   - If `cache_mode == "FALLBACK"`:
     - Returns cached response if available.
     - Otherwise proceeds to make an API call and saves the new response to
       cache.
   - If `cache_mode == "CAPTURE"`:
     - Always makes a fresh API call and updates cache.
   - If `cache_mode == "DISABLED"`:
     - Makes a fresh API call and does not touch cache.

4. **API Call Execution**
   - Calls OpenAI API synchronously (with or without streaming).
   - Collects the completion output and underlying response object.

5. **Cost Estimation**
   - Uses `_calculate_cost()` to compute token usage cost.
   - If enabled, accumulates cost using `start_logging_costs()`.

6. **Response Caching**
   - Saves response to cache via `_CompletionCache.save_response_to_cache()` (if
     applicable).
   - Cost and response metadata are saved in JSON.

7. **Return**
   - Returns only the final text content from the model.

- All caching operations are handled by the `_CompletionCache` class.

# How Testing Works

- During unit tests, the cache:
  - Is set in `REPLAY` mode to avoid real API calls
    (tests raise error if the required response is not cached)
  - Uses for cache a file that is checked into the repo
  - Expected prompts and responses are cached beforehand or as tests are executed

## Cache Refreshing

- When testing, it might be necessary to regenerate cached responses, e.g.,
  - Prompts or expected completions have changed.
  - You are adding a new test using a LLM prompt
  - You want to ensure the cache reflects the latest LLM output.

- When testing, it might be necessary to regenerate cached responses after making
  prompt or model changes. You can trigger cache refreshing using:
  ```bash
  > pytest --update_llm_cache
  ```
  - This sets the global `UPDATE_LLM_CACHE` flag (defined in your conftest or
    test setup for now later it will be moved to `hopenai.py`).
  - Internally, this sets `cache_mode="CAPTURE"` when calling `get_completion()`.
    - All API calls will be re-executed even if cached versions exist.
    - The cache file (e.g., `cache.get_completion.json`) is updated with new
      responses.
    - Metadata like `last_updated`, `hits`, and `misses` are also updated.

- Note that the cache might contain old prompts that are not needed anymore
  - If you want to generate a cache with all and only what is needed, you
    can delete the unit test cache and then run all the tests with
    `--update_llm_cache`

- Once the cache is refreshed, the cache should be reviewed and committed the
  updated cache file to version control
