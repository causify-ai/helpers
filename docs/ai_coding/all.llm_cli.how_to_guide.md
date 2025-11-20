# Install

```
> uv tool install llm

> export PATH="/Users/saggese/.local/bin:$PATH"
```

```
> uvx llm --version
Installed 33 packages in 45ms
llm, version 0.27.1

- The code and the documentation is at 
- https://github.com/simonw/llm
- https://llm.datasette.io/en/stable/

## Getting help

```
> llm --help
```

## Models

- To list the models
  ```
  > llm models
  OpenAI Chat: gpt-4o (aliases: 4o)
  OpenAI Chat: chatgpt-4o-latest (aliases: chatgpt-4o)
  OpenAI Chat: gpt-4o-mini (aliases: 4o-mini)
  ...
  OpenAI Chat: gpt-5
  OpenAI Chat: gpt-5-mini
  OpenAI Chat: gpt-5-nano
  OpenAI Chat: gpt-5-2025-08-07
  OpenAI Chat: gpt-5-mini-2025-08-07
  OpenAI Chat: gpt-5-nano-2025-08-07
  OpenAI Completion: gpt-3.5-turbo-instruct (aliases: 3.5-instruct, chatgpt-instruct)
  Default: gpt-4o-mini
  ```

## Fragments

```
more my_fragment.txt
The solar eclipse will occur on April 8, 2024, visible across North America.
```

> llm -f my_fragment.txt "Summarize the above in one sentence."

## How to
- How to execute a prompt from a file and save it
  ```
  > cat prompt.txt | llm | tee output.txt
  ```

- Execute a prompt from a file using a template
  ```
  > cat prompt.txt | llm -t llm-markdown.yaml | tee output.txt
  ```
