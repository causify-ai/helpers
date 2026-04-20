This document contains all the rules that must be followed to write text in terms
of bullet lists.

## Goals and Philosophy

- Make the text easy to consume for both humans and AI

- Focus on:
  - Clarity
  - Brevity
  - Visual structure

- Think of notes as a hybrid between a textbook and a student's notebook

- This document is written using the rules described in this document itself

## Writing Style

### Writing Style

- Use explicit references instead of unclear ones
  - **Bad**: "it"
  - **Good**: "TCP protocol"
- Maintain consistent labels for recurring ideas
- Avoid redundancy in concepts
- Prefer plain language over academic jargon
- Make sure text is short and not unnecessarily long

### Avoid Long Prose

- Prefer structured notes over narrative prose
- Use a first-person, self-directed voice, e.g.,
  - **Good**: "Key thing to remember: entropy increases"

### Use Direct Statements

- Convert abstract principles into short, direct statements, e.g.,
  - **Bad**: "Everyone takes responsibility, owns their projects, and blames no
    one if something doesn't get finished."
  - **Good**: "Everyone takes responsibility: no blaming others if work isn't
    finished."

## Use Only Text

- Avoid emojis and icons
- Avoid any decorative formatting
  - Do not use line separator like `---`
- Use only basic text
  - **Bad**: A → B
  - **Good**: A -> B

## Text is Formatted with Bullets

- Every text should start with a bullet point

- **Bad**
  ```
  Hello, my name is ...
  ```
- **Good**
  ```
  - Hello, my name is ...
  ```

## Use Bullets

- Use bullet points inside a paragraph

- Each bullet should express one complete atomic idea
  - Keep bullets concise but meaningful (1–3 lines)

- Use bullets to show:
  - Definitions
  - Purpose
  - Components
  - Pros and cons
  - Examples

- Group bullets under clear paragraph headings

- Do not end a bullet point with a period `.`

## Use Nested Bullets

- Use nested bullets to show:
  - Dependencies and relationships
    - E.g., cause -> effect
  - Hierarchy of concepts, e.g.,
    ```
    - Technology
      - Hardware
        - Computers
        - Mobile Devices
      - Software
        - Operating Systems
        - Applications
    ```
  - Components and lists, e.g.,
    ```
    - Allowed formats:
      - Graphviz
      - Mermaid
      - TikZ-style charts
    ```
  - Elaboration, not to extend main bullets, e.g., for
    - Definitions
    - Examples
    - Implications

## Try to Use Lists

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

- **Bad**
  ```
  - They appear everywhere: husbands with controlling wives, overly helpful
    friends with chaotic lives, seemingly stable men who suddenly fall apart
  ```
- **Good**
  ```
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

## Organize text in bullet points

- Make sure all the text is organized in bullet points
  ```
  **What it does**:
  - Extracts each page of a PDF file as a separate PNG image
  - Numbers output files sequentially (`slides001.png`, `slides002.png`, etc.)
  - Supports customizable DPI for image quality control
  - Creates output directory automatically with optional from-scratch mode
  ```

## Summarize the text into structured markdown bullet points

- Create 4-5 bullet points capturing the main ideas
- Use nested markdown bullets with maximal clarity and fewer words
  - Use `-` for first-level bullets
  - Use indented `-` for sub-bullets
  - Organize sub-bullets hierarchically: general rule first, then example, then
    mathematical formulation
- Use Latex notation for formulas
- Avoid non-ASCII symbols
- Extract concrete examples
- Be concise: remove narrative prose, keep only key facts and relationships

## Use `*` for top-level topic headers

- E.g., `* Markov Chains`

# Examples

## Example 1: Chains

  ```
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

## Example 2: Core values

  ```
  - Are a timeless set of guiding principles
  - Define the culture, who fits and who doesn't
  - Define what makes the Company different and unique

  **Culture > strategy**

  - In a Company, culture wins in the long term
  - A Company
    - Needs to know who it is
    - Is defined by the Core Values

  **Uses of Core Values**

  - Hire
  - Fire
  - Review everyone

  **Core values: EOS Worldwide example**

  - Be humble but confident
  - Grow or die
  - Help first
  - Do what you say
    - E.g., if you commit to a date, you hit it
    - You fully deliver and finish what you start: no half-assed things
    - If you can't do it, don't commit
  - Do the right thing
  ```
