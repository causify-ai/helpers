Rules for writing structured text using bullet lists

# Goals and Philosophy

- Make the text is easy to consume for both humans and AI, i.e., it's
  well-organized, structured, without fluff, and AI slop

- Focus on:
  - Clarity
  - Brevity
  - Visual structure

- Think of notes as a hybrid between a textbook and a student's notebook

# Writing Style

## Clear Language

- Use explicit references instead of unclear pronouns
  - **Bad**: "it"
  - **Good**: "TCP protocol"
- Maintain consistent labels for recurring ideas
- Avoid redundancy in concepts
- Prefer plain language over academic jargon

## Structured Over Prose

- Prefer structured notes over narrative prose
- Use a first-person, self-directed voice:
  - **Good**: "Key thing to remember: entropy increases"

- Convert abstract principles into short, direct statements:
  - **Bad**:
    ```
    Eunset OPENROUTER_API_KEY CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_KEY OPENROUTER_KEYveryone takes responsibility, owns their projects, and blames no one if
    something doesn't get finished
    ```
  - **Good**:
    ```
    Everyone takes responsibility: no blaming others if work isn't finished
    ```

# Formatting

## Use Only Text

- Avoid emojis and icons
- Avoid any decorative formatting
  - Do not use line separator like `---`
- Use only basic text and ASCII
  - **Bad**: A → B
  - **Good**: A -> B

## Use `:` Instead of `-`

- When writing bullet points with an explanation, use `:` and not `-` to separate
  the first part from the comment
  - **Bad**
    ```
    `SKILL.md` - Main skill instruction file
    ```
  - **Good**
    ```
    `SKILL.md`: Main skill instruction file
    ```

# Bullet List Structure

## Bullet Fundamentals

- Every text should start with a bullet point
  - **Bad**
    ```markdown
    Hello, my name is ...
    ```
  - **Good**
    ```markdown
    - Hello, my name is ...
    ```
- Each bullet expresses one complete atomic idea (1–3 lines)
- Do not end a bullet point with a period
- Group bullets under clear paragraph headings

## Bullet Usage

- Use bullets to show definitions, purpose, components, pros/cons, and examples
- Start all introductory text with a bullet as well:
  - **Bad**:
    ```markdown
    Always follow these guidelines:
    - `.claude/skills/notebook.rules.md`: General notebook conventions
    ```
  - **Good**:
    ```markdown
    - Always follow these guidelines:
      - `.claude/skills/notebook.rules.md`: General notebook conventions
    ```

- Example: Well-Structured Bullets
  ```markdown
  - What it does:
    - Extracts each page of a PDF file as a separate PNG image
    - Numbers output files sequentially (`slides001.png`, `slides002.png`, etc.)
    - Supports customizable DPI for image quality control
    - Creates output directory automatically with optional from-scratch mode
  ```

## Nested Bullets

- Use nested bullets for dependencies, relationships, and hierarchy
  - Dependencies and relationships (e.g., cause -> effect)
  - Hierarchy of concepts
  - Components and lists
  - Elaboration (definitions, examples, implications)
- Keep nesting logical: general rule first, then example, then mathematical formulation
- Example hierarchy:
  ```
  - Technology
    - Hardware
      - Computers
      - Mobile Devices
    - Software
      - Operating Systems
      - Applications
  ```

## Converting Prose to Bullet Points

- Create 4-5 bullet points capturing main ideas
- Use nested structure with maximal clarity and fewer words
  - Use `-` for first-level bullets
  - Use indented `-` for sub-bullets
  - Organize hierarchically: general rule first, then example, then mathematical formulation
- Use LaTeX notation for formulas
- Avoid non-ASCII symbols (use `->` not `→`)
- Extract concrete examples
- Remove narrative prose, keep only key facts and relationships

## Multi-Level Organization

- Organize bullet points into cohesive chunks using multiple levels
- **Bad**: Flat list with no hierarchy (hard to follow logical relationships)
- **Good**: Structured with sub-bullets that clarify relationships and dependencies

- Example:
  - **Bad** (unclear grouping):
    ```
    - Evaluation answers "how good is this policy"
    - The linear system $(I - gamma P) U = b$ is solved directly with `numpy`
    - With a fixed action, the $max$ disappears: equations are linear
    - A bad policy yields low utilities near the $-1$ terminal
    ```
  - **Good** (clear relationships):
    ```
    - Evaluation is the first half of policy iteration
      - Evaluation answers "how good is this policy", not "what should I do instead"
    - With a fixed action per state, $max$ disappears: equations are linear
      - The linear system $(I - gamma P) U = b$ is solved directly with `numpy`
    ```

## Lists Over Prose

- Use lists to structure text and improve legibility
- Break dense prose into organized sub-bullets
  - **Bad**
    ```
    This document covers how to publish documents, books, and blogs across
    different repos (e.g., `//helpers`, `//csfy`, `//tutorials`, and
    `//umd_classes`)
    ```
  - **Good**
    ```
    - This document covers how to publish:
      - Documents
      - Books
      - Blogs
      across different repos, e.g.,
      - `//helpers`
      - `//csfy`
      - `//tutorials`
      - `//umd_classes`
    ```

- Example
  - **Bad**
    ```markdown
    - They appear everywhere: husbands with controlling wives, overly helpful
      friends with chaotic lives, seemingly stable men who suddenly fall apart
    ```
  - **Good**
    ```markdown
    - They appear everywhere:
      - Husbands with controlling wives
      - Overly helpful
      - Friends with chaotic lives
      - Seemingly stable men who suddenly fall apart
    ```

## Keep Number Lists in Order

- If there are numbered lists, make sure they are in order starting from 1
  - **Bad**
    ```markdown
    ## 2. First
    ## 2. Second
    ## 3. Third
    ```
  - **Good**
    ```markdown
    ## 1. First
    ## 2. Second
    ## 3. Third
    ```

# Constraints

- Preserve fenced code blocks without modification

# Examples

## Example 1: Chains

  ```markdown
  - In case of $T \to M \to Y$:
    - $M$ is "mediator" since it mediates the relationship between $T$ and $Y$
    - Causation flows only in the direction of the arrows
    - Association flows both ways

  - E.g., $Study \to SolveProblems \to JobPromotion$
    - Job promotion is causally dependent on studying
    - The association goes both ways
      - The more you study, the more likely to get a promotion
      - The greater the chances of promotion, the greater your chance of having
        studied (otherwise it would be difficult to get a promotion)
    - So $Study$ and $JobPromotion$ are
      - Dependent or
      - Not independent $Study \cancel \perp JobPromotion$

  - If you hold the intermediary variable fixed (i.e., conditioning on $M$, looking
    for only people with the same skills at problem solving), the dependency is
    blocked
    - $T$ and $Y$ are independent given $M$, i.e., $(T \perp Y) | M$
    - $\EE[Y | T, M] = \EE[Y | M]$ and also the inverse $\EE[T | Y, M] = \EE[T | M]$
  ```

## Example 2: Core Values

  ```markdown
  - Are a timeless set of guiding principles
  - Define the culture, who fits and who doesn't
  - Define what makes the Company different and unique

  ## Culture > strategy

  - In a Company, culture wins in the long term
  - A Company
    - Needs to know who it is
    - Is defined by the Core Values

  ## Uses of Core Values

  - Hire
  - Fire
  - Review everyone

  ## Core values: EOS Worldwide example

  - Be humble but confident
  - Grow or die
  - Help first
  - Do what you say
    - E.g., if you commit to a date, you hit it
    - You fully deliver and finish what you start: no half-assed things
    - If you can't do it, don't commit
  - Do the right thing
  ```
