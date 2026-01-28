When there are commands in a readme the format should be like

- Description
  ```bash
  > command
  ```

- Good
  ````
  - With system prompt from file:
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt_file system_prompt.txt
  ```
  ````

- Bad
  ````
  **With system prompt from file:**
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt_file system_prompt.txt
  ```
  ````
