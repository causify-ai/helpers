# TODO

- [ ] Add an option to cache_simple to store hash also based on docstring and
  type hints
  - [ ] Remove cache invalidation from @llm
- [ ] Rename cache_simple to cache
- [ ] Use LLM structure output

- [ ] Why bounding arguments

- [ ] The caching is orthogonal to llm but enabled by default

- [ ] Add support to call back Python code

# Plan: LLM-as-Function Decorator Library

## 1. Design the core `@llm` decorator (`helpers/hllm_decorator.py`)
- Decorator wraps a function stub (type hints + docstring = LLM prompt)
- Uses `inspect` to extract signature, types, and docstring at decoration time
- At call time: serializes args/kwargs, constructs prompt, calls `apply_llm()`, parses response to return type

- The decorator accepts a use_cache: bool = True
- Layers caching via `hcache_simple.py` (keyed on function hash + arguments)

## 2. Implement type coercion and validation
- Map Python type annotations to output parsing instructions in the LLM prompt
- After LLM response: coerce string to `int`, `float`, `bool`, `List`, `Dict`, etc.

## 3. Implement caching layer
- Integrate with `hcache_simple.simple_cache` — each decorated function auto-cached
- Cache key: hash of (function source, model, args, kwargs)
- Support `force_refresh` to bypass cache

## 4. Implement batching / vectorization
- Not implemented in first iteration — design only
- When a user decorates a function with `@llm(vectorize=True)`, the decorator
  detects that the function operates on a data structure (e.g., `list`, `map`,
  `set`)
- Instead of calling the LLM once per element (N sequential calls), the decorator
  batches all elements into a single LLM request with a structured prompt for
  parallel processing
- The LLM returns results for all elements at once, and the decorator dispatches
  them back to the caller in the original type/structure
- This amortizes per-call overhead (token preamble, network latency) over the
  batch

## 5. Implement multi-shot prompting
- Allow user to register example input/output pairs via decorator param: `@llm(examples=[...])`
- Inject examples into the system prompt to guide LLM behavior

## 6. Implement tool-use (LLM calls registered Python functions)
- The `@llm` decorator supports a `tools` parameter: a list of callable Python
  functions the LLM can invoke during its execution
- The LLM receives function signatures and docstrings in the prompt as available
  tools
- Workflow: (a) LLM emits a tool-call request (function name + arguments), (b)
  decorator intercepts the response, executes the Python function, (c) feeds the
  result back to the LLM as context, (d) loop until the LLM produces a final
  answer of the declared return type
- This mirrors the OpenAI tool-use / Anthropic tool-use pattern but expressed
  natively in Python

## 7. Implement compilation (`hllm_decorator.compile()`)
- **Step 1 — Record**: The decorator records all (input, output) pairs produced
  by the LLM over time (stored in the cache)
- **Step 2 — Create unit tests**: Auto-generate a test class from the recorded
  I/O pairs, following `testing.rules.md` conventions (three sections: prepare
  inputs, prepare outputs, check outputs with `self.assert_equal()`)
- **Step 3 — Generate pure Python code**: Feed the I/O pairs + generated tests to
  a code-generating LLM with the prompt: "Write a pure Python function that
  passes all these tests." The resulting function replaces the LLM-backed stub,
  evolving from uncertain LLM behavior to deterministic, auditable code
- This enables the "from all LLM to all code" evolution: start with an LLM for
  rapid prototyping, compile to Python once the behavior stabilizes

## 8. Implement unit test auto-generation
- `@llm` decorator auto-generates test class with input/output pairs
- Uses the caching layer's recorded calls as test fixtures
- Follows `testing.rules.md`: `Test_<FunctionName>`, `test1`/`test2` naming,
  three-section structure, `self.assert_equal()` for assertions

## 9. Create comparison matrix with alternatives
- Compare against: DSPy, LMQL, Guidance, Marvin, Outlines, LangChain LCEL,
  Semantic Kernel
- Dimensions: type safety, caching, batching, tool use, compilation, Python
  integration, learning curve, structured output support, async support,
  ecosystem maturity

## 10. Write unit tests
- Follow `testing.rules.md` conventions
- Test each component: decorator, type coercion, caching, batching, multi-shot,
  tool use, compilation pipeline
- Use `mock_apply_llm()` for deterministic LLM responses in tests
