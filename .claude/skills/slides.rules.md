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
- **Use questions**: Mark rhetorical questions with `@Question@:`
- **Ground in examples**: Always include `@Example@:` with concrete scenarios
- **Reference prior knowledge**: "As we saw in [previous topic]..."
- **Contrast approaches**: Show what doesn't work vs what does

## Problem-Solution Arc
- Introduce hard topics as a progression
  `@Problem@$\to$ `@Naive Solution@` $\to$ `@Solution@`
  so students see why the final approach is needed
- Make the naive solution's weaknesses explicit with `Cons:` sub-bullets, then
  let the real solution address them

- Example arc (from Lesson 06.1):
  ```
  - Slide 1: `@Problem@`: logic-based AI fails under uncertainty (partial
    observability, non-determinism, ...)
  - Slide 2: `@(Naive) Solution@`: belief states + exhaustive rules, each with
    a `Cons:` line
  - Slide 3: `@Solution@`: combine _probability_ and _utility functions_
  ```

## Recurring Running Example
- Carry one concrete example across many slides to build intuition incrementally,
  varying the question asked of it
  - E.g., the "Garden World" ($Rain$, $Sprinkler$, $WetGrass$, $Weather$) is
    reused to illustrate conditional independence, explaining away, marginal vs
    conditional dependence, and sampling
- Reuse the identical diagram across slides that revisit the same example so the
  student anchors on a stable picture
- Pair each abstract concept with at least one domain example beyond the running
  one to show generality
  - E.g., medical diagnosis, finance, car insurance

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
  - Instead of `→` use `$\to$`

## Use 80 columns
- Wrap text into 80 columns

## Slide Structure
- Each slide should start with:
  ```markdown
  * <slide title>
  ```
- Each slide contains bullet points arranged in a hierarchical structure
  - Every line starts with a bullet point
  - Do not use period at the end of a phrase
  ```markdown
  * <slide title>

  - @Definition@:
    - ...
    - ...

  - @Problem@:
    - ...

  - @Solution@:
    - ...
  ```

## Use Tags for Slide Sections
- Every first level bullet point (starting with `- ` and not `*`) should start
  with a bold label `<bold label>` for pedagogical structure

### Tags

- Use `@TAG@` formatting (not `**Bold**:`) for semantic markup
- The tag appears before the colon and in italics/boldface, making the tag system
  more visible and machine-readable

#### Core Definition & Structure Tags

- _Definition_: Defines a concept formally
  - Use `@Definition@` formatting
  - The defined term should be in bold
  - E.g.,
    ```
    - @Definition@: A **time series** is modeled as a random process, ...
    ```
  - E.g.,
    ```
    - @Definition@: **Bayesian updating** revises a belief over an unknown $\theta$
      by combining a _prior_ with the _likelihood_ of observed data $X$
    ```

- _Components_: Describes building blocks, parts, or elements of a structure
  - Use when breaking down a concept into its parts
  - E.g., (from Lesson 03.3):
    ```
    - @Components@
      - _Classes_: abstract groups (e.g., $Person$, $Animal$)
      - _Properties_: binary relations (e.g., $hasChild$, $ownsPet$)
      - _Instances_: specific objects (e.g., $GP$, $Nuvolo$)
    ```

- _Characteristics_ / _Properties_: Notable features or qualities
  - Use `@Characteristics@` or `@Properties@` to list key attributes
  - E.g.,
    ```
    - @Characteristics@
      - Deals with incomplete, uncertain, ambiguous information
      - Relies on defaults, heuristics, patterns not strict proofs
    ```

#### Content Organization Tags

- _Comparison_: Contrasts different approaches or perspectives
  - Use when showing what distinguishes one method from another
  - E.g.,
    ```
    - @Comparison@:
      - _Classical logic_: once proven, conclusions remain true
      - _Non-monotonic logic_: conclusions change with new facts
    ```

- _Example_ (singular): A single concrete illustration
  - Use for one specific example with detail
  - E.g.,
    ```
    - @Example@: _"All students take some course"_:
      $\text{Student} \equiv \exists \text{takes}.\text{Course}$
    ```

- _Examples_ (plural): Multiple concrete illustrations
  - Use `@Examples@` when listing several instance of a concept
  - E.g.,
    ```
    - @Examples@:
      - _Propositional logic_: world consists of facts
      - _First-order logic_: objects with relations
      - _Temporal logic_: facts hold at particular times
    ```

- _Problem_: A difficulty or open issue that motivates a solution
  - E.g.,
    ```
    - @Problem@: a purely predictive model learns $\Pr(Y | X)$ from historical
      data and absorbs any association in the data, spurious or not
    ```

- _Intuition_: Explains the "why it makes sense" conceptually
  - Use to provide reasoning or conceptual clarity
  - E.g.,
    ```
    - @Intuition@: the posterior is a compromise between what was believed
      before and what the data says now
    ```

#### Evaluation & Application Tags

- _Pros_ / _Cons_: Advantages and disadvantages of an approach
  - E.g.,
    ```
    - @Pros@
      - Express precise theory of the human mind as a computer program
    
    - @Cons@
      - Unknown workings of the human mind
    ```

- _Challenges_: Difficulties, limitations, or constraints
  - Use `@Challenges@` to highlight what is hard or problematic
  - E.g.,
    ```
    - @Challenges@
      - Knowledge is vast, informal, imprecisely defined
      - Difficult to encode in machine-readable form
    ```

- _Techniques_ / _Methods_: Approaches or procedures for achieving something
  - Use when describing how something is done
  - E.g.,
    ```
    - @Techniques@
      - Knowledge graphs, non-monotonic logic, probabilistic reasoning
    ```

- _Variants_: Different types or variations of a concept
  - E.g.,
    ```
    - @Variants@:
      - _OWL Lite_: simpler, for classification hierarchies
      - _OWL DL_: full expressiveness with decidable reasoning
    ```

- _Applications_: Practical uses or domains where a concept applies
  - Use `@Applications@` to show real-world relevance
  - E.g.,
    ```
    - @Applications@: semantic search, biomedical data, knowledge graphs
    ```

#### Traditional Mathematical Tags

- _Question_: A question to introduce a problem
  - E.g.,
    ```
    - @Question@: does the data provide evidence for or against a specific
      hypothesis, such as "this coin is fair" or "this treatment has no effect"?
    ```

- _Goal_: What we are trying to achieve before describing how
  - E.g.,
    ```
    - @Goal@: Analyze and study algorithms for the _simple_ end of the decision
      spectrum
    ```

- _Assumptions_: Preconditions or constraints that apply
  - E.g.,
    ```
    - @Assumptions@
      - Single agent, one objective, a model that is either fully known or
        learnable from direct interaction
    ```

- _Naive Solution_: A first, flawed attempt whose cons motivate a better one
  - E.g.,
    ```
    - @Naive Solution@: grid the parameter space and evaluate the posterior
      pointwise
      - Cons: the grid grows exponentially with the number of parameters
    ```

- _Solution_: A solution to a previously introduced problem
  - E.g.,
    ```
    - @Solution 1: Markov Chain Monte Carlo (MCMC)@
      - Build a Markov chain whose stationary distribution is the posterior
    ```

- _Key idea_: The single most important takeaway
  - E.g.,
    ```
    - @Key idea@: shipping a prediction when the business needs a decision delivers
      little or no business value, however accurate the prediction is
    ```

- _Remark_: A simple but useful fact
  - E.g.,
    ```
    - @Remark@: sequential updating and batch updating reach the same posterior
      - The order evidence arrives in does not change the final belief
    ```

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

### Tag Ordering Convention

- When organizing content within a slide, use this preferred tag order (apply
  only relevant tags):

  1. **Motivation** or **Problem**: why this matters or what problem exists
  2. **Definition**: formal definition of the concept
  3. **Comparison** or **Characteristics**: how it differs from others, key
     features
  4. **Examples** or **Example**: concrete illustrations
  5. **Components**: parts or building blocks (for structured concepts)
  6. **Intuition**: conceptual explanation (why it works)
  7. **Pros** / **Challenges**: advantages and disadvantages
  8. **Techniques** or **Variants**: variations or methods
  9. **Applications**: practical uses and domains

- This ordering places context and definition first, then concrete examples,
  evaluation, and finally applications, mirroring the pedagogical progression
  from abstract to concrete.

### Example1
- **Good**
  ```markdown
  * Individual Treatment Effect
  - @Definition@: the impact of the treatment $T$ on the outcome $Y$ for an
    individual unit $i$ is:
    $$\tau_i \defeq Y_i|do(T=t_1) - Y_i|do(T=t_0)$$
    - The effect $\tau_i$ of going from treatment $t_0$ to $t_1$ for unit $i$ is
      the difference in the outcome of that unit under $t_1$ compared to $t_0$

  - @Example@: for the sales example
    $$AmountSold_i|do(IsOnSales=1) - AmountSold_i|do(IsOnSales=0)$$

  - @Problem@: you can only observe one term due to the fundamental problem of
    causal inference
    - Represent it in theory, but can't recover it from data
  ```

### Example2
- **Good**
  ```markdown
  * Potential Outcomes
  - Aka "counterfactuals"

  - @Definition@: the $do()$ operator represents _"unit $i$ outcome $Y$ if
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

  - @Remark@: there is a difference between conditioning and intervention
    - $Y|do(T=t)$ is _"what a business would sell if it cut prices"_
    - $Y|T=t$ is _"what a business that cut the prices sold"_
```

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

## Numbered List Bullets
- Use a numbered list under a bold label when the sub-points are an ordered
  procedure or an enumerated set; use bullets otherwise:
  ```markdown
  - @Problem@: Real-world agents face _uncertainty_ from:
    1. Partial observability
       - Agent can't see the full state of the world
    2. Non-determinism
       - Actions don't always have predictable outcomes
  ```

## Use Bold
- Use bold **term** when
  - Defining a term as part of `@Definition` tag
  - Highlighting a term that is particular important

## Use Italic
- Use _italic_ (`_text_`) for:
  - Quoted statements
    ```markdown
    _"If we lower prices by 10%, will revenue increase?"_
    ```
  - Key terms
  - Important concepts
  - Emphasized definitions

### Emphasis Precedence: Bold Over Italic
- When a bullet point or line contains both bold and italic text, **bold takes
  precedence**: make the entire emphasis bold rather than mixing styles
- This keeps visual hierarchy clear and reduces visual noise

- Examples
  - **Bad** (mixing bold and italic on same line):
    ```markdown
    - _Order the nodes_ according to **cause-effect dependencies**
    ```
  - **Good** (bold for the entire emphasized phrase):
    ```markdown
    - **Order the nodes** according to cause-effect dependencies
    ```
  - **Bad** (mixing styles in emphasis):
    ```markdown
    - The _parents_ of $X$ (shown in **bold** for importance)
    ```
  - **Good** (consistent bold emphasis):
    ```markdown
    - **Parents** of $X$: the nodes that influence $X$
    ```

## Use Inline Verbatim
- Use inline verbatim (`code`) for:
  - Technical terms
  - Function names
  - Variable names
  - Implementation-oriented notation

## Typst Tables
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
- `$\EE[...]$`: Expectation (mean), instead of  `\mathbb{E}`
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

### Avoid `\text{...}` in Math Mode
- Do **not** use `\text{...}` for variable or concept names inside `$ $`
- Write identifiers directly in math mode without `\text{}` wrapper
- Cleaner rendering and simpler code

- **Bad**
  ```markdown
  $\Pr(\text{Rain}) = 0.5$
  $\text{Parents}(X_i)$
  ```

- **Good**
  ```markdown
  $\Pr(Rain) = 0.5$
  $Parents(X_i)$
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

# Examples and Templates
- See examples `.claude/templates/slides.template.md`
