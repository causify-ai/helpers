- Explain how to run from stdin / stdout


# Basic Usage
> llm_transform.py -i input.txt -o output.txt -p uppercase

# List of transforms
> llm_transform.py -i input.txt -o output.txt -p list

# Code review
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_review

# Propose refactoring
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_propose_refactoring
"
