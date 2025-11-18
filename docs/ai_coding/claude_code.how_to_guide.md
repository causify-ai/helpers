# Using Claude Code

Claude Code is a coding-focused interface for the Claude AI assistant. It helps
you write, understand, and debug code more efficiently.

## 1. Opening Claude Code

- Run `claude` in your Git client

- Initially you should give permissions to `claude` for any action

- It's not a good idea to use `claude --dangerously-skip-permissions`
  unless you know what you are doing

## 2. Creating And Editing Code

You can use Claude Code in two ways:

1. Paste or write code directly
   - Paste existing code into the editor.
   - Ask Claude something like:
     - "Explain what this function does."
     - "Refactor this into smaller functions."
     - "Convert this from JavaScript to Python."

2. Start from a natural-language request
   - Type a prompt such as:
     - "Create a Python script that reads a CSV and prints summary stats."
     - "Generate a React component for a login form with validation."

3. I like to use a `instr.md` file with the instructions to `claude`
   so that
   - E.g., see the template `ai/ai.instruction_template.md`
   ```bash
   > cp ai/ai.instruction_template.md instr.md
   # Customize instr.md with detailed instructions
   claude> execute instr.md
   ```

Claude will:
- Propose code in the chat
- Often insert or update code directly in the editor

Save or copy the generated code into your own environment to run it.

## 3. Running And Testing Code

Depending on the integration, Claude Code may:

- Simulate running code (describe what would happen, spot logical issues)
- Provide test cases and examples
- Help you write unit tests

Ask things like:
- "Write unit tests for this function using pytest."
- "What edge cases might break this code?"
- "Can you step through this algorithm with an example input?"

Then paste results or error messages back into the chat so Claude can help debug.

## 4. Debugging With Claude Code

When you get an error in your local environment:

1. Copy the error message and the relevant code snippet.
2. Paste them into Claude Code.
3. Ask:
   - "Here is the error I am seeing. Can you help me fix it?"
   - "Why does this raise a TypeError? Suggest a fix."

Claude will:
- Explain the error
- Suggest changes
- Sometimes give rewritten code blocks

Review changes carefully and test them yourself.

## 5. Working With Larger Projects

For multi-file projects:

- Use any available file browser or project view
- Open individual files in the editor.
- Ask questions like:
  - "Give me a high-level overview of this repository."
  - "Where is the main entry point for this app?"
  - "Find where the user authentication logic is implemented."

Claude can:
- Summarize architecture
- Trace how functions call each other
- Suggest refactors at the project level

## 6. Prompting Tips

To get better results:

1. Be specific
   - Instead of "Fix this", say:
     - "Reduce the time complexity."
     - "Make this function pure and side-effect free."
     - "Rewrite this using async/await."

2. Set constraints
   - "Use only standard library."
   - "Target Python 3.10."
   - "Avoid external dependencies."

3. Iterate
   - Start with a rough version.
   - Ask Claude to optimize, clean up, or document it:
     - "Add comments explaining each step."
     - "Improve variable names and structure."

# Workflows





This document consolidates all AI development workflows, coding conventions, and tools used in the Causify/helpers ecosystem.

## Overview

This documentation provides comprehensive guidelines for:

- Writing Python code following Causify conventions
- Creating unit tests
- Formatting notes and documentation
- Using AI-powered review and transformation tools
- Integrating with ChatGPT API
- Understanding the helpers repository architecture

## Interesting files

- `ai/code_template.py` shows our coding style
- `ai/unit_test_template.py` shows how our unit tests look like

- `CLAUDE.md`: Project architecture overview and development conventions for
  Claude Code working with the `helpers` repository
- `ai/ai.instruction_template.md`: Workflow template for creating Python scripts with
  tests, documentation, planning steps, and AI todos
- `ai/ai.coding_instructions.md`: Python coding standards including hdbg assertions,
  hsystem usage, logging patterns, and script templates
- `ai/ai.unit_test_instructions.md`: Unit testing conventions including
  test structure, naming patterns, and golden file testing

- `ai/ai.blog_instructions.md`: Markdown formatting guidelines for writing blog
  posts with proper structure, code blocks, and metadata

- `ai/ai.notes_instructions.txt`: Style guide for writing structured bullet-point
  notes optimized for clarity and AI/human readability

## AI Development Workflow Template

When creating a Python script:

1. **Write a Python script** following the instructions in `ai/ai.coding_instructions.md`

2. **Generate unit tests** for the code following the instructions in `ai/ai.unit_test_instructions.md`

3. **Generate a short description** of how to use the script in a file close to the script with extension `.md`

   - Explain the goal of the script
   - Report some examples of how to use the tool
   - Describe the architecture

## AI Review and Transform Tools

### Operations Overview

There are several operations we want to perform using LLMs:

- Apply a transformation to a chunk of text (e.g., create a unit test)
- Create comments and lints in the form of a `cfile` (e.g., lint or AI review based on certain criteria)
- Apply modifications from a `cfile` to a set of files (e.g., from linter and AI review)
- Add TODOs from a `cfile` to Python or markdown files
- Apply a set of transformations to an entire Python file (e.g., styling/formatting code)
- Rewrite an entire markdown to fix English mistakes without changing its structure

**Important:** Always commit your code before applying automatic transforms, in the same way that we run the `linter` on a clean tree. This way, modifying a file is a separate commit and it's easy to review.

### Use Templates

We use templates for code and documentation to show and describe how a document or code should look like:

- `all.how_to_guide_template_doc.md` shows how a Diataxis how-to guide should be structured and look like

The same templates have multiple applications:

- **For Humans:**
  - Understand how to write documentation and code
  - As boilerplate (e.g., "copy the template and customize it to achieve a certain goal")
- **For LLMs:**
  - As reference style to apply transforms
  - To report violations of coding styles
  - As boilerplate (e.g., "explain this piece of code using this template")

### Available Tools

- `llm_transform.py`
- `transform_notes.py`: Some transformations don't need LLMs and are implemented as code.
- `ai_review.py`: The rules for AI are saved in
  `./docs/code_guidelines/all.coding_style_guidelines.reference.md`. This file
  has a special structure:
  - First level represents the target language (e.g., `General`, `Python`)
  - Second level represents a rule topic (e.g., `Imports`, `Functions`)
  - Third level represents instructions for an LLM vs Linter
- `inject_todos.py`: Injects TODOs from a `cfile` into source files.
- `apply_todos.py`: Automatically applies TODOs from a `cfile` using an LLM.
