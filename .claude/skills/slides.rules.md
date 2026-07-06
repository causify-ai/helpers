- This document consolidates formatting rules and conventions for creating
  professional lecture slides for graduate-level courses

# Core Writing Principles

## Pedagogical Progression
- **Start with motivation**: Explain why the topic matters before diving into
  details
- **Intuition before formalism**: Explain the concept intuitively, then provide
  mathematical formalism
- **Build incrementally**: Progress from simple to complex, referencing earlier
  concepts
- **Use multiple representations**: Combine text, equations, diagrams, and
  real-world examples
- **Concrete examples**: Always include practical examples labeled
- **Reference context**: Connect new concepts to previously introduced material

## Engagement Strategies
- **Open with motivation**: "Why does this matter?"
- **Use questions**: Mark rhetorical questions with `**Question**:`
- **Ground in examples**: Always include `**Example**:` with concrete scenarios
- **Reference prior knowledge**: "As we saw in [previous topic]..."
- **Contrast approaches**: Show what doesn't work vs what does

## Problem-Solution Arc
- Introduce hard topics as a `**Problem**` $\to$ `**(Naive) Solution**` $\to$
  `**Solution**` progression so students see why the final approach is needed
- Make the naive solution's weaknesses explicit with `Cons:` sub-bullets, then
  let the real solution address them
- Example arc (from Lesson 06.1):
  - Slide 1: `**Problem**`: logic-based AI fails under uncertainty (partial
    observability, non-determinism, ...)
  - Slide 2: `**(Naive) Solution**`: belief states + exhaustive rules, each with
    a `Cons:` line
  - Slide 3: `**Solution**`: combine _probability_ and _utility functions_

## Recurring Running Example
- Carry one concrete example across many slides to build intuition
  incrementally, varying the question asked of it
  - E.g., the "Garden World" ($Rain$, $Sprinkler$, $WetGrass$, $Weather$) is
    reused to illustrate conditional independence, explaining away, marginal vs
    conditional dependence, and sampling
- Reuse the identical diagram across slides that revisit the same example so the
  student anchors on a stable picture
- Pair each abstract concept with at least one domain example beyond the running
  one (e.g., medical diagnosis, finance, car insurance) to show generality

## Defining Terms
- When a concept has multiple common names, list them up front with an `Aka:`
  bullet before the definition:
  ```markdown
  * Bayesian Networks: Definition
  - Aka:
    - "Bayes nets"
    - "Belief networks"
    - "Graphical models" (somehow a broader class of statistical models)
  ```
- Introduce notation inline by binding each symbol to a quoted plain-language
  meaning:
  ```markdown
  - $Rain$ = _"it rains"_
  - $WetGrass$ = _"the grass is wet"_
  ```

## Slide Density Guidelines
- Maximum 5-7 bullet points per slide (excluding sub-points)
- Maximum 2-3 lines per bullet point
- Use diagrams instead of long text descriptions
- Break complex topics across multiple slides

# Document Organization

## Section Structure
- Major sections to start new page/major topic:
  ```markdown
  # Section Title
  ```

- Subsections (within a major section):
  ```markdown
  ## Subsection Title
  ```

- Individual slides: use `*` with no leading spaces
  ```markdown
  * <Slide Title>

  - <Main bullet point>
    - <Sub-point> (2-space indent)
      - Further nesting (4-space indent)
  ```

# Slide Organization

## General Formatting Rules
- Don't use emoji
- Don't use page separators
- Don't use unicode characters but use LaTeX symbols if needed
  - Instead of → use `$\to$`

## Slide Structure
- Each slide should start with:
  ```markdown
  * Slide title
  ```
- Each slide contains bullet points arranged in a hierarchical structure
  - Every line starts with a bullet point
  - Do not use period at the end of a phrase

## Use Bold for Slide Sections
- Every first level bullet point (starting with `- ` and not `*`) should start
  with a bold label `<bold label>` for pedagogical structure
- Use the following tags:
  - **Definition**: A definition of a concept
    - The definition term needs to be in italic
    - E.g.,
      ```
      - **Definition**: A _time series_ is modeled as a random process,
      ```
  - **Question**: A question to introduce a problem
  - **Goal**: What we are trying to achieve before describing how
  - **Problem**: A difficulty or open issue that motivates a solution
  - **Solution**: A solution to a previously introduced problem
  - **Pros** / **Cons**: Advantages and disadvantages of an approach
  - **Example**: Concrete illustration
  - **Intuition**: Explains the "why it makes sense"
  - **Key idea**: The single most important takeaway
  - **(Naive) Solution**: A first, flawed attempt whose cons motivate a better
    one
  - **Remark**: A simple but useful fact
  - **Fact**: A statement asserted as true, used without proof
  - **Theorem**: A central, proven result
  - **Proof**: The argument establishing a theorem (often numbered steps)
  - **Proposition**: A result worth stating, but not as central as a theorem
  - **Lemma**: stepping stone used to prove a bigger result
  - **Claim**: A smaller assertion inside a proof or argument
  - **Algorithm**: A step-by-step procedure (often with **Input**/**Output**)
  - **Input** / **Output**: What an algorithm consumes and produces
  - **Limitations**: Conditions under which the approach fails or is weak
  - **Counterexample**: Shows what doesn't work
  - **Interpretation**: What the result means in context

- Do not change the title `* <title>`, but only the content of the slide

- Use a numbered list under a bold label when the sub-points are an ordered
  procedure or an enumerated set; use bullets otherwise:
  ```markdown
  - **Problem**: Real-world agents face _uncertainty_ from:
    1. Partial observability
       - Agent can't see the full state of the world
    2. Non-determinism
       - Actions don't always have predictable outcomes
  ```

- Template:
  ```markdown
  * <slide title>

  - **<Bold label>**:
    - ...
    - ...
  ```

### Example
- **Good**
  ```markdown
  * Individual Treatment Effect
  - **Definition**: the impact of the treatment $T$ on the outcome $Y$ for an
    individual unit $i$ is:
    $$\tau_i \defeq Y_i|do(T=t_1) - Y_i|do(T=t_0)$$
    - The effect $\tau_i$ of going from treatment $t_0$ to $t_1$ for unit $i$ is
      the difference in the outcome of that unit under $t_1$ compared to $t_0$

  - **Example**: for the sales example
    $$AmountSold_i|do(IsOnSales=1) - AmountSold_i|do(IsOnSales=0)$$

  - **Problem**: you can only observe one term due to the fundamental problem of
    causal inference
    - Represent it in theory, but can't recover it from data
  ```

- **Good**
  ```markdown
  * Potential Outcomes
  - Aka "counterfactuals"

  - **Definition**: the $do()$ operator represents _"unit $i$ outcome $Y$ if
    treatment is set to $t$"_
    - $Y_{t,i}$ is Rubin's notation
    - $Y_i | do(T_i = t)$ is Pearl's notation

  - For binary treatment:
    - $Y_{0i}$ potential outcome without treatment
    - $Y_{1i}$ potential outcome with treatment
    - One is "factual" (i.e., observable)
    - The other is "counterfactual" (i.e., theoretical, not observable)
    - Alternative expression:
      $$
      Y_i = T_i * Y_{1i} + (1 - T_i) * Y_{0i} = Y_{0i} + (Y_{1i} - Y_{0i}) * T_i
      $$

  - **Remark**: there is a difference between conditioning and intervention
    - $Y|do(T=t)$ is _"what a business would sell if it cut prices"_
    - $Y|T=t$ is _"what a business that cut the prices sold"_
```

## Use Italic
- Use _italic_ (`_text_`) for:
  - Quoted statements
    ```markdown
    _"If we lower prices by 10%, will revenue increase?"_
    ```
  - Key terms
  - Important concepts
  - Emphasized definitions

## Use Inline Verbatim
- Use inline verbatim (`code`) for:
  - Technical terms
  - Function names
  - Variable names
  - Implementation-oriented notation

## Tables
- Create tables using the `styled-table` function from
  `./dev_scripts_helpers/documentation/pandoc_touying.typ` to maintain
  consistent formatting and professional appearance across all slides
- `styled-table` provides proper borders, header formatting, and alignment
  automatically

### Syntax

- The table is enclosed in a fenced div with `{=typst}`
  ````
  ```{=typst}
  #styled-table(
    headers: ("Column 1", "Column 2", "Column 3"),
    rows: (
      ("Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"),
      ("Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"),
    ),
    caption: "Table Caption (optional)",
    col-widths: (1fr, 1.5fr, 1fr),  // optional
    bold-first-col: true  // optional
  )
  ```
  ````

### Parameters
- **headers**: Array of column header strings (required)
- **rows**: Array of rows, where each row is an array of cell contents
  (required)
- **caption**: Optional table caption displayed below the table
- **col-widths**: Optional array of column width specifications
  - Default: equal widths (`1fr` for each column)
  - Example: `(1fr, 1.5fr, 1fr)` makes middle column 50% wider
- **bold-first-col**: Optional boolean to bold the first column (default:
  `true`)
  - Set to `false` for symmetric data; use `true` for row labels

### Guidelines
- Use `bold-first-col: true` when the first column contains row labels
- Adjust `col-widths` when column content varies significantly in length
- Always include `headers` to make table structure clear

### Example
- **Good** (labeled data with consistent styling)
  ```typst
  #styled-table(
    headers: ("Method", "Accuracy", "Speed"),
    rows: (
      ("Baseline", "75%", "Fast"),
      ("Proposed", "92%", "Slow"),
      ("Optimized", "90%", "Fast"),
    ),
  )
  ```

- **Bad** (inconsistent inline table formatting)
  ```markdown
  | Method | Accuracy | Speed |
  |--------|----------|-------|
  | Baseline | 75% | Fast |
  | Proposed | 92% | Slow |
  ```

## Mathematical Notation

### Display Modes
- Inline math within text:
  ```markdown
  The probability is $\Pr(X | Y)$ or expectation $\EE[X]$.
  ```

- Centered display math on own line:
  ```markdown
  $$
  \Pr(X | Y) = \frac{\Pr(Y | X) \Pr(X)}{\Pr(Y)}
  $$
  ```

- Multi-line equations with alignment:
  ```markdown
  \begin{align*}
  & \Pr(x_1, x_2) \\
  & = \Pr(x_1) \Pr(x_2 | x_1)
  \end{align*}
  ```

### Standard LaTeX Commands
Use these commands consistently across all slides:

- `$\Pr(...)$`: Probability
- `$\Pr(... | ...)$`: Conditional probability (use `|`, do not use `\mid`)
- `$\EE[...]$`: Expectation (mean)
- `$\VV[...]$`: Variance
- `$\mathcal{X}$`: Sets or spaces (use calligraphic)
- `\defeq`: "Defined as"
- `\iff`: "If and only if"
- `\implies`: Logical implication ($X \implies Y$)
- `\land`, `\lor`, `\lnot`: Logical and / or / not
- `\perp`: Conditional independence, e.g., `$X \perp Y | Z$`
- `\not\perp`: Dependence, e.g., `$Rain \not\perp Sprinkler$`
- `\cancel{...}`: Cross out conditioning variables made irrelevant, e.g.,
  `$\Pr(Call | Alarm, \cancel{Fire, Toast}) = \Pr(Call | Alarm)$`
- `Parents(X_i)`, `parents(X_i)`: parent set of a node in a Bayesian network
- `\vx`, `\vy`, `\vE`, `\ve`: Vectors (if defined in preamble)
- `\alpha` as a normalization constant in inference, e.g.,
  `$\Pr(X | \ve) = \alpha \Pr(X, \ve)$`

- Express conditional independence statements compactly, optionally pairing the
  `\perp` form with its factorization or an arrow form:
  ```markdown
  $$Rain \perp Sprinkler | Weather$$
  $$Rain \not\perp Sprinkler \iff Rain \leftrightarrow Sprinkler$$
  ```

### Color-Coded Variables in Equations
- Color variables to highlight different parts and make multi-step derivations
  easier to follow
- Wrap each variable in a color command:

  | Command        | Use For                                                     |
  | -------------- | ----------------------------------------------------------- |
  | `\blue{...}`   | Variables being isolated, subtracted, or primary focus      |
  | `\red{...}`    | Variables being substituted or replaced                     |
  | `\green{...}`  | Results, children nodes                                     |
  | `\gray{...}`   | Already-processed terms, less relevant parts                |
  | `\violet{...}` | Variables outside the main variable set, secondary groups   |
  | `\teal{...}`   | Additional grouped variables                                |
  | `\olive{...}`  | Further grouped variables                                   |
  | `\orange{...}` | Supplementary variables                                     |
  | `\brown{...}`  | Hidden or unobservable variables (e.g., in causal diagrams) |
  | `\black{...}`  | Explicitly black text (override inherited color)            |

- Example: showing variable elimination step by step:
  ```latex
  \Pr(\blue{x_1, ..., x_{n-1}}, \red{x_n})
  = \Pr(\red{x_n} | \blue{x_{n-1}, ..., x_1}) \Pr(\blue{x_{n-1}, ..., x_1})
  ```

- Example: multi-line elimination with distinct colors:
  ```latex
  \begin{align*}
  & \Pr(\gray{x_1}, \violet{x_2}, ..., \teal{x_{n-2}}, \olive{x_{n-1}}, \orange{x_n}) \\
  & = \Pr(\orange{x_n} | x_{n-1}, ..., x_1) \Pr(x_{n-1}, ..., x_1) \\
  & = \Pr(\orange{x_n} | x_{n-1}, ..., x_1)
  \Pr(\olive{x_{n-1}} | x_{n-2}, ..., x_1) \Pr(x_{n-2}, ..., x_1) \\
  & = ...
  \end{align*}
  ```

### Spacing and Breaks
- Use comments (`//`) for internal notes (not rendered in output)
- Do NOT use page separators (`---` markdown syntax)

### Symbols and Characters
- Do NOT use non-ASCII characters, but use LaTeX instead:

- ε → `$\varepsilon$`
- → → `$\to$`
- ∝ → `$\propto$`
- ≈ → `$\approx$`
- ∩ → `$\cap$`
- ∪ → `$\cup$`

### Font Sizing
- Group all font size changes with LaTeX:
  ```markdown
  \begingroup \large
  Large text here
  \endgroup
  ```
- Common size commands: `\large`, `\Large`, `\small`, `\scriptsize`

### Latex Equation Style
- For complex LaTeX expressions, use indentation and line breaks to visually
  represent the nesting structure of operators, expectations, sums, integrals,
  conditionals, and other hierarchical constructs
  - Avoid placing the entire expression on a single line when it contains
    multiple nested levels
  - Align major operators and indent subordinate expressions to make the
    mathematical structure easier to read
  - Keep all equations in standard Markdown LaTeX blocks ($$ ... $$)
  - **Bad** (everything on one line)
    ```latex
    $$
    a^* = \arg\max_{a \in \mathcal{A}} \EE_{\theta \sim \Pr(\theta | \mathcal{D})}
          \left[ \EE_{Y \sim \Pr(Y | do(a), \theta)}[U(Y)] \right]
    $$
    ```
  - **Good** (indentation reflects nesting)
    ```latex
    $$
    a^*
      = \arg\max_{a \in \mathcal{A}}
          \EE_{\theta \sim \Pr(\theta | \mathcal{D})}
          \left[
            \EE_{Y \sim \Pr(Y | do(a), \theta)}[U(Y)]
          \right]
    $$
    ```

- The goal is to make the hierarchical structure of the expression immediately
  apparent while preserving the Latex expression

# Visuals

## Type of Visuals
- Follow the instructions from `.claude/skills/visuals.rules.md`

# Example Slide Styles

## Side-by-Side Content

- For symmetric content (two equal columns):
  ```markdown
  | **Left Heading** | **Right Heading** |
  |---|---|
  | - Point 1<br>- Point 2 | - Point 1<br>- Point 2 |
  ```

- E.g.,
  ```
  | Property | Chatbot | Agent |
  |---|---|---|
  | Output | Text only | Text and side effects (files, API calls, transactions) |
  | State | Conversation history | Environment state + memory |
  | Loop | Single turn → response | Perceive → plan → act, repeated |
  | Failure mode | Wrong answer | Wrong answer *or* wrong action taken |
  ```

- For asymmetric content (text + diagram):
  ```markdown
  ::: columns
  :::: {.column width=65%}
  - Main content with text
  - Multiple bullet points
  - Detailed explanation
  ::::
  :::: {.column width=35%}
  ```graphviz
  [diagram code here]
  ```
  ::::
  :::
  ```

## Definition Slide

- Use for introducing a new concept or term
  ```markdown
  * <Term>: Definition

  - **Definition**: <Term> is [concise definition in plain language]
    - Property or characteristic 1
    - Property or characteristic 2
    - Property or characteristic 3

  - Mathematically:
    $$
    [mathematical formula or equation]
    $$

  - **Example**: [concrete, real-world scenario that demonstrates the concept]
  ```

- Real example
  ```markdown
  * Machine Learning: Definition

  - **Machine learning** is building machines to do useful things without being 
    explicitly programmed
    - Learns from experience
    - Improves with data
    - Performs tasks without hardcoded rules

  - Formally: _"A computer program is said to learn from experience E with respect 
    to some task T and some performance measure P, if P(T) improves with experience E"_
    (Mitchell, 1998)

  - **Example**: Computer vision system that learns to recognize cats from labeled 
    image datasets without being programmed with cat detection rules
  ```

## Algorithm Slide
- Use for describing a step-by-step procedure or algorithm
  ```markdown
  * <Algorithm Name>

  - **Input**: [describe what data/values go in]
  - **Output**: [describe what the algorithm produces]

  - **Steps**:
    1. Initialize parameters or setup phase
    2. Main algorithm step or iteration
    3. Update or transform values
    4. Convergence check or termination condition

  - **Complexity**:
    - Time: $O(...)$
    - Space: $O(...)$
  ```

## Pros/Cons Slide
- Use for evaluating approaches or concepts against criteria.
  ```markdown
  - <Topic>: Advantages and Disadvantages

  - **Pros**
    - Advantage 1: [why it's good]
    - Advantage 2: [why it's good]
    - Advantage 3: [why it's good]

  - **Cons**
    - Disadvantage 1: [why it's problematic]
    - Disadvantage 2: [why it's problematic]
    - Disadvantage 3: [why it's problematic]
  ```

- Example (from Lesson 01.1):
  ```markdown
  - AI as Thinking Humanly: Pros and Cons

  - **Pros**
    - Express precise theory of the human mind as a computer program

  - **Cons**
    - Unknown workings of the human mind
    - Anthropocentric definition (not applicable to non-human intelligence)
  ```

## Question Slide
- Use for posing rhetorical or engagement questions
  ```markdown
  * <Question or Topic>

  - **Question**: [specific question that engages the audience]

  - Consider these options:
    - Option A: [description]
    - Option B: [description]
    - Option C: [description]

  - **Answer**: Option X because [reasoning]

  - **Key takeaway**: [what students should learn from this]
  ```

## Theorem / Proof Slide
- Use for stating a result and deriving it in numbered steps
  ```markdown
  * <Theorem Name>
  - **Theorem**: [statement of the result, with the conditions it holds under]

  - **Proof**
  1. **<First step name>** [what is done and why]
     $$
     [equation for step 1, with \blue{}/\red{} colors to track variables]
     $$
  2. Apply the same formula **recursively** until [termination condition]
     \begin{align*}
     & [line 1] \\
     & = [line 2] \\
     & = ... \\
     & = [closed form] \\
     \end{align*}
  ```
- Real example (from Lesson 06.2 — chain rule): isolate one variable per step,
  color it to show what is being peeled off, and end at a product/closed form

## Worked Computation Slide
- Use for a `**Problem**` $\to$ `**Solution**` numeric or symbolic derivation
  tied to a diagram
  ```markdown
  * <Topic>: Example
  ::: columns
  :::: {.column width=60%}
  - **Problem**: [what to compute, stated in words and symbols]
  ::::
  :::: {.column width=35%}
  ```graphviz
  [the network the computation refers to]
  ```
  ::::
  :::

  - **Solution**
  - [express the target as a product of CPTs / conditional probabilities]
    \begin{align*}
    & \Pr(\text{query}) \\
    & = \Pr(\cdot | \cdot) \cdot \\
    & \hspace{1cm} \Pr(\cdot | \cdot) \cdot \\
    & \hspace{1cm} ... \\
    \end{align*}
  ```
- Use `\hspace{1cm}` to indent continuation lines of a long product so factors
  align visually

## Annotated-Diagram Slide (Target / Roles)
- Use when classifying the nodes of a diagram into roles (e.g., a Markov
  blanket: target, parents, children, spouses)
- Color the bold role labels to match the node `fillcolor` in the diagram so the
  text and picture reinforce each other:
  ```markdown
  * Markov Blanket: <Domain> Example
  ::: columns
  :::: {.column width=30%}
  - Consider [the system]
  ::::
  :::: {.column width=70%}
  ```graphviz
  [diagram with role-colored nodes]
  ```
  ::::
  :::
  - **\red{Target node}**
    - $X$ — [the variable of interest]
  - **\blue{Parent nodes}**
    - [direct causes / influences of $X$]
  - **\green{Children nodes}**
    - [outcomes directly influenced by $X$]
  - [closing takeaway: knowing these roles is sufficient to predict $X$]
  ```
- Reuse this same template across multiple domains (medical, economic, finance)
  to show the abstraction generalizes — only the nodes change, not the structure

## Node-Coloring Legend Slide
- When a complex diagram uses fill colors to encode variable categories, state
  the legend in bold colored labels above the diagram:
  ```markdown
  * <Topic>: <System> (2/2)
  - **\blue{Blue nodes}**: [category, e.g., observable inputs]
  - **\brown{Brown nodes}**: [category, e.g., hidden / unobservable variables]
  - **\violet{Violet nodes}**: [category, e.g., target variables]
  ```graphviz
  [large multi-node network using those fill colors]
  ```
  ```
- Split a large worked system across two slides — `(1/2)` for the textual
  problem setup, `(2/2)` for the full diagram

## Multi-Slide Continuation
- For a topic that spans several slides, repeat the same `* <Title>` verbatim on
  each slide rather than numbering them, OR append `(1/2)`, `(2/2)` when the
  parts are explicitly sequential halves of one whole
- Keep the running-example diagram identical across the continuation slides;
  vary only the surrounding text and the conditional-independence question being
  asked
