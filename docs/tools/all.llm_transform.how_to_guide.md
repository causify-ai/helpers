<!-- toc -->

- [Structure of files](#structure-of-files)
- [Step-by-step execution](#step-by-step-execution)
  * [Example](#example)

<!-- tocstop -->

# Structure of files
Search files...
Based on the code analysis, I can explain the structure of these three files 
and how they work together. Here's a comprehensive breakdown:

1. **Overall Architecture**
The system is designed to apply LLM-based transformations to code and text 
files, with a focus on code quality, documentation, and formatting. 
The architecture consists of three main components:

2. **llm_transform.py** (Main Entry Point)
- This is the primary script that users interact with
- Key features:
  - Handles input/output from either stdin/stdout or files
  - Manages Docker container setup and execution
  - Provides command-line interface for various transformations
- Main functions:
  - `_parse()`: Sets up command-line argument parsing
  - `_run_dockerized_llm_transform()`: Manages Docker container execution
  - `_main()`: Orchestrates the overall transformation process

3. **dockerized_llm_transform.py** (Docker Container Script)
- Runs inside a Docker container
- Key features:
  - Handles the actual LLM transformation
  - Manages dependencies within the container
  - Processes input/output files
- Main functions:
  - `_parse()`: Parses command-line arguments
  - `_main()`: Executes the transformation using LLM prompts

4. **llm_prompts.py** (Prompt Management)
- Contains all the transformation prompts and their configurations
- Key features:
  - Defines various transformation types (code fixes, reviews, markdown processing)
  - Manages pre and post-transformation steps
  - Handles prompt templates and contexts
- Main components:
  - Prompt definitions (e.g., `code_fix_docstrings`, `code_review_correctness`)
  - Transformation management (`run_prompt()`)
  - Context definitions (`_CODING_CONTEXT`, `_MD_CONTEXT`)

5. **Transformation Types**
The system supports several categories of transformations:
- Code Fixes:
  - Docstring improvements
  - Type hint additions
  - Logging statement fixes
  - String formatting fixes
- Code Reviews:
  - Correctness review
  - Refactoring suggestions
- Markdown Processing:
  - Document rewriting
  - Summarization
  - How-to guide formatting
  - Explanation document formatting

6. **Transformation Process Flow**
1. User calls `llm_transform.py` with input/output files and transformation type
2. `llm_transform.py` sets up Docker container and passes control to 
   `dockerized_llm_transform.py`
3. `dockerized_llm_transform.py` uses `llm_prompts.py` to:
   - Apply pre-transformations
   - Execute LLM transformation
   - Apply post-transformations
4. Results are written back to the output file

7. **Docker Integration**
- Uses Python 3.12 Alpine as base image
- Installs necessary dependencies (PyYAML, requests, pandas, openai)
- Manages file paths between host and container
- Handles environment variables (e.g., OPENAI_API_KEY)

8. **Error Handling and Logging**
- Comprehensive logging system
- Type checking and assertions
- Error handling for file operations
- Docker container management error handling

This architecture provides a robust and flexible system for applying LLM-based 
transformations to code and text files, with proper isolation of dependencies 
through Docker and a clear separation of concerns between the different components.

# Step-by-step execution 

Please note that same steps are followed for any transformation execution. 
The input and output file extensions could be .txt, .py, .md, stdout
depending upon the type of transformation.

- Choose the input file
  - Locate the Python file you want to transform.
  - Alternatively, you may use stdin to input the code manually.
- Specify the output file
  - Provide a path to save the transformed output.
  - Example path: research_amp/causal_kg/scrape_fred_metadata.new
- Open a terminal and run the following command:
  ```bash
     > llm_transform.py -i input-file -o output-file -p <prompt-tag>
  ```
- Verify the result
  - The output would be copied to the output file.

## Example

- In case of an input file
  - step 1: Input file is 'research_amp/causal_kg/scrape_fred_metadata.py'.
    - Suppose, the file contains the following imports:
      ```python
        from utils import parser
        from helpers import hopenai
      ```
  - step 2: Output file is 'research_amp/causal_kg/scrape_fred_metadata_new.py'.
  - step 3: Run the following command:
    ```bash
     > llm_transform.py -i research_amp/causal_kg/scrape_fred_metadata.py 
     -o research_amp/causal_kg/scrape_fred_metadata_new.py -p code_fix_from_imports
    ```
  - step 4: The output is following and saved in the above-mentioned output file:
    ```python
       import utils.parser
       import helpers.hopenai
    ```

- In case of stdin
  - step 1: Input is stdin
  - step 2: Output is stdout
  - step 3: Run the following command:
    ```bash
     > llm_transform.py -i - -o - -p code_fix_from_imports
     # input:
     from utils import parser
     from helpers import hopenai
     [press Ctrl + D]
    ```
  - step 4: The output is following and saved in the above-mentioned output file:
    ```python
       import parser.utils
       import helpers.hopenai
    ```
