- Commands in a readme must follow the format below
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
