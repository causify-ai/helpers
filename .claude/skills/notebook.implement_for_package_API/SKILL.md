---
description: Implement a Jupyter notebook tutorial for a Python package
model: haiku
---

Create a self-contained Jupyter notebook that teaches the Python package
`<PACKAGE_NAME>` by progressively introducing its core primitives, mental model,
and API surface

The notebook should be optimized for learning the library itself, not for solving
a large real-world problem

## Teaching Philosophy

1. Start from the smallest possible working example
2. Introduce one new concept at a time
3. Use the minimum amount of code necessary to demonstrate each concept
4. Prefer toy examples with 2–5 objects instead of realistic datasets
5. Every code cell should answer exactly one question
6. Avoid helper functions, abstractions, and boilerplate unless they are part of
   the library's API
7. Focus on understanding:
   - What are the primitive objects?
   - How are they created?
   - How do they interact?
   - What methods are available?
   - What state do they hold?
   - How do they compose into larger structures?

## Notebook Structure

### Use Standard Template Structure
- Use the structure from `.claude/templates/notebook.template.py` for consistent
  notebook initialization

- First Cell: Include autoreload, logging, and core dependencies
- Second Cell: Optionally install packages on-the-fly
- Third Cell: Notebook-specific imports and logger

### Use Python Style
- For all Python code in notebooks, follow the rules in
  `.claude/skills/coding.rules.md`

### Markdown Cells
- For all the markdown cells use bullet points with nested bullets for clarity
  and conciseness, following the rules in
  - `.claude/skills/slides.rules.md`: rules for formatting slides
  - `.claude/skills/text.rules.md`: rules for formatting bullet points

### 1. Library Overview

Briefly explain:

- What problem the library solves
- The key abstractions
- The most important classes
- A conceptual diagram of how the pieces fit together

### 2. Primitive-by-Primitive Exploration

For each important primitive:

#### Template

Mental Model
- Explain what the object "means"

Smallest Construction
```
python # minimal example 
```

Inspect the Object
```
python type(obj) dir(obj) 
```

Important Methods
```
python obj.method(...) 
```

### 3. Composition Examples

Build progressively:

Example 1:
- Smallest meaningful object

Example 2:
- Add one new concept

Example 3:
- Combine two primitives

Example 4:
- Minimal end-to-end workflow

Each example should fit within roughly 10–20 lines

### 4. API Patterns

Identify recurring patterns:

- Builder patterns
- Fit/predict patterns
- Graph construction patterns
- Context managers
- Iterators
- Serialization
- Configuration

Show the smallest example of each pattern

### 5. Interactive Exploration

Provide cells that encourage experimentation:

```
python dir(obj) help(obj.method) 
```

and questions such as:

- What happens if you remove this argument?
- What is the default value?
- What type is returned?

#### Summary: The Mental Model

Synthesize the core mental model: what are the fundamental abstractions and how
do they fit together? This should be 2-4 sentences capturing the essence of the
library's design. 

## Special Instructions

- Use executable Python code throughout
- Minimize imports
- Keep examples independent whenever possible
- Do not skip intermediate steps
- Avoid advanced topics until all primitives are covered
- Prefer many tiny examples over a few large examples
- If the library has hidden state or non-obvious behavior, explicitly inspect it
- Whenever a class is introduced, show:
  - Construction
  - Inspection
  - Mutation
  - Interaction with another object
- The notebook should feel like a guided reverse-engineering of the library's design
