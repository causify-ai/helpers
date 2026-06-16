# `llm_cli.py`

## What It Does

General-purpose CLI script to apply LLM transformations to text files or text
input. This script provides a command-line interface to the
`apply_llm_with_files` function from `helpers.hllm_cli`. It reads text from an
input file or command line, processes it using an LLM (either via the llm CLI
executable or the llm Python library), and writes the result to an output file or
prints to screen.

Key features:
- Supports multiple LLM models (GPT-4, Claude, etc.) via either the llm CLI
  executable or Python library
- Can process input files in-place, write to output files, or print to stdout
- Supports reading from stdin and writing to stdout for pipeline integration
- Optional system prompts (inline or from file) to guide LLM behavior
- Progress bar support with automatic or explicit output size estimation
- Optional automatic linting of output files

## Architecture

- The architecture of the script has several stages:
  - Read input:
      - `--input <file>`: it can be a file, stdin (using `-`)
      - `--input_text <text>`: text specified via command line
  - (Optional) Extract a chunk of input:
      - `--select <token>`: various selection criteria
      - `--modify_in_place`: replace a chunk of file with the output
  - Select a prompt:
      - `-p`: prompt specified from command line
      - `-pf <file>`: prompt from a file
      - `--rule <topic>`: use a file from a `.claude/skills/<topic>.rules.md`
      - `--skill <skill>`: use a file from a `.claude/skill/<skill>/SKILL.md`
  - (Optional)
    - `--lint`: A linting step
  - Write output
      - `--output`: it can be a file, stdout (using `-`), or in place (`-m`)

- Models are specified in the same way used for `llm`
  - `anthropic/claude-haiku-4-5-20251001`
  - `anthropic/claude-opus-4.8`
  - `anthropic/claude-sonnet-4.6`
  - `gpt-4o-mini`
  - `openrouter/anthropic/claude-haiku-4.5`
  - `openrouter/deepseek/deepseek-v4-flash`
  - `openrouter/meta-llama/llama-3.1-8b-instruct`
  - `openrouter/openai/gpt-oss-120b`
  - `openrouter/openai/gpt-oss-20b`

## Examples

- Basic usage with input and output files
  ```bash
  > llm_cli.py --input input.txt --output output.txt
  > llm_cli.py -i input.txt -o output.txt
  ```

- In-place editing (writes back to input file)
  ```bash
  > llm_cli.py --input input.txt
  > llm_cli.py -i input.txt
  ```

- Read from stdin and write to stdout
  ```bash
  > echo "What is 2+2?" | llm_cli.py --input - --output -
  ```

- Read from stdin and write to file
  ```bash
  > echo "What is 2+2?" | llm_cli.py --input - --output output.txt
  > cat input.txt | llm_cli.py -i - -o output.txt
  ```

- Basic usage with input text
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output output.txt
  ```

- Print to screen instead of file
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output -
  > llm_cli.py -i input.txt -o -
  > echo "What is 2+2?" | llm_cli.py -i - -o -
  ```

- Use llm CLI executable instead of library
  ```bash
  > llm_cli.py -i input.txt -o output.txt --use_llm_executable
  ```

- With system prompt and specific model
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt "You are a helpful assistant" \
      --model gpt-4
  ```

- With system prompt from file
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt_file system_prompt.txt
  ```

- With automatic progress bar (estimates output size)
  ```bash
  > llm_cli.py -i input.txt -o output.txt -b
  > llm_cli.py -i input.txt -o output.txt --progress_bar
  ```

- With progress bar and explicit output size
  ```bash
  > llm_cli.py -i input.txt -o output.txt --expected_num_chars 5000
  ```

- Apply linting to output file after processing
  ```bash
  > llm_cli.py -i input.txt -o output.txt --lint
  > llm_cli.py -i input.txt --lint  # In-place editing with linting
  ```

// TODO(ai_gp): Fix this

- Apply a single Claude rule to an entire set of slides (in place)
  ```bash
  > llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt --rule '.claude/skills/slides.rules.md:58:# Slide Organization'
  ```

- Apply an entire skill to an entire file (in place)
  ```
  > llm_cli.py -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt --skill slides.criticize_structure
  ```
  - `--skill slides.criticize_structure` is a shortcut for
    `-pf .claude/skills/slides.criticize_structure/SKILL.md`

- Apply a prompt to a chunk of file selected with lines (`--select X:Y`) in place
  (`-m`)
  ```
  > llm_cli.py -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt --select 133:162  -pf .claude/skills/slides.fix_errors/SKILL.md -m
  ```

- Apply a style to graphviz in place
  ```
  > llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt --select 205 -m -pf .claude/templates/graphviz.template.md
  ```

- Apply 
  ```
  llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt -pf /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/slides.fix_errors/SKILL.md --select 482 --lint -m
  ```

- Test a model
  ```
  > llm_cli.py --input_text "Say hello" --model "openrouter/anthropic/claude-haiku-4.5" --backend executable -o -
  Hello! 👋 How are you doing today? Is there anything I can help you with?
  Total cost: Cost: 0.00u$, Elapsed: 8.47s (input_tokens=0, output_tokens=0, cost_from_llm_library=0.0, cost_from_tokencost=0.0, )
  ```

- Summarize text and then lint the answer
  ```
  > llm_cli.py -p "Summarize the following text in 5 bullet points and less than 200 words" --input We_should_be_more_tired_than_the_model.hn_comments.txt --model openrouter/anthropic/claude-haiku-4.5 --lint
  ```

- Apply a single rule
  ```
  > llm_cli.py  --rule '.claude/skills/slides.rules.md:58:# Slide Organization'
  ```
