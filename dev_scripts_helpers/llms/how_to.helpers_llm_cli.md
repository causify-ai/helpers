## `llm_cli.py`

### What It Does

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

### Examples

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

Apply a rule
> llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt > --rule '.claude/skills/slides.rules.md:58:# Slide Organization'

Apply a skill to an entire file
llm_cli.py -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt --skill slides.criticize_structure

Apply a prompt to a chunk of file
llm_cli.py -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt --select 133:162  -pf .claude/skills/slides.fix_errors/SKILL.md 

Apply a style to graphviz
llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt --select 205 -m -pf .claude/templates/graphviz.template.md

llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt -pf /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/slides.fix_errors/SKILL.md --select 482 --lint -m

llm_cli.py --input_text "Say hello" --model "openrouter/anthropic/claude-opus-4.6" --backend executable -o -

