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

## Slide Density Guidelines
- Maximum 5-7 bullet points per slide (excluding sub-points)
- Maximum 2-3 lines per bullet point
- Use diagrams instead of long text descriptions
- Break complex topics across multiple slides

# Document Organization

## Section Structure

- Major sections to start new page/major topic:
  ```markdown
  # ##############################################################################
  # Section Title
  # ##############################################################################
  ```

- Subsections (within a major section):
  ```markdown
  ## #############################################################################
  ## Subsection Title
  ## #############################################################################
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

- Every first level bullet point should start with a bold label `<bold label>`
  for pedagogical structure like in the following:
  - **Definition**: A definition of a concept
  - **Question**: A question to introduce a problem
  - **Solution**: A solution to a previously introduced problem
  - **Remark**: A simple but useful fact
  - **Proposition**: A result worth stating, but not as central as a theorem
  - **Lemma**: stepping stone used to prove a bigger result
  - **Claim**: A smaller assertion inside a proof or argument
  - **Intuition**: Explains the "why it makes sense"
  - **Example**: Concrete illustration
  - **Counterexample**: Shows what doesn't work
  - **Interpretation**: What the result means in context

- Template:
  ```markdown
  * <slide title>

  - **<Bold label>**:
    - ...
    - ...
  ```

### Example
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

### Example
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
- `$\Pr(... | ...)$`: Conditional probability (do not use `\mid`)
- `$\EE[...]$`: Expectation (mean)
- `$\VV[...]$`: Variance
- `$\mathcal{X}$`: Sets or spaces (use calligraphic)
- `\defeq`: "Defined as"
- `\iff`: "If and only if"
- `\perp`: Independence (perpendicular symbol)
- `\vx`, `\vy`: Vectors (if defined in preamble)

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

- Example — showing variable elimination step by step:
  ```latex
  \Pr(\blue{x_1, ..., x_{n-1}}, \red{x_n})
  = \Pr(\red{x_n} | \blue{x_{n-1}, ..., x_1}) \Pr(\blue{x_{n-1}, ..., x_1})
  ```

- Example — multi-line elimination with distinct colors:
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

# Visual Elements and Diagrams

## GraphViz Diagrams
- When to use: flowcharts, networks, agent interactions, system relationships,
  process flows

- Standard template with styling:
  ```graphviz
  digraph DiagramName {
      splines=true;
      nodesep=1.0;
      ranksep=0.75;

      node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, penwidth=1.4];

      NodeName [label="Display Name", fillcolor="#A6C8F4"];
      OtherNode [label="Other", fillcolor="#B2E2B2"];

      { rank=same; Node1; Node2; }

      NodeName -> OtherNode [label="  relationship"];
  }
  ```

- Color palette (use consistently throughout all diagrams):

| Color       | Code      | Use For                                |
| ----------- | --------- | -------------------------------------- |
| Red/Pink    | `#F4A6A6` | Agents, actors, primary entities       |
| Orange      | `#FFD1A6` | Input data, sources                    |
| Green       | `#B2E2B2` | Processed data, environments           |
| Teal        | `#A0D6D1` | Algorithms, processes, transformations |
| Light Blue  | `#A6E7F4` | Parameters, configuration, settings    |
| Blue        | `#A6C8F4` | Outputs, results, final states         |
| Purple      | `#C6A6F4` | External entities, mixed dependencies  |

### Annotating Nodes with Probability Expressions

- Use `xlabel` to display conditional probability expressions inline on GraphViz
  nodes:
  ```graphviz
  Rain [label="Rain", fillcolor="#A6C8F4", xlabel="P(R | W)"];
  ```
  - The `xlabel` text appears outside the node box, not inside
  - Use it to annotate Bayesian network nodes with their CPT expressions:
    - Source nodes: `xlabel="P(W)"`
    - Conditional nodes: `xlabel="P(R | W)"`, `xlabel="P(G | R, S)"`
    - Nodes with known probabilities: `xlabel="P(B) = 0.001"`

- Example:
  ```graphviz
  digraph AgentEnv {
      splines=true;
      nodesep=1.0;
      ranksep=0.75;

      node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, penwidth=1.4];

      Agent [label="Agent", fillcolor="#F4A6A6"];
      Env [label="Environment", fillcolor="#B2E2B2"];

      Agent -> Env [label="  Action"];
      Env -> Agent [label="  Reward"];
  }
  ```

## Mermaid Diagrams
- When to use: Mind maps, hierarchical taxonomies, classification structures

- Example:
  ```mermaid
  mindmap
    root((**Machine Learning**))
      (**Paradigms**)
        Supervised
        Unsupervised
        RL
      (**Models**)
        Linear
        Neural networks
        SVM
  ```

## Tables

- Use markdown tables for structured data comparisons

- Example
  ```markdown
  \begingroup \scriptsize
  | **Column1** | **Column2** | **Column3** |
  | ----------- | ----------- | ----------- |
  | Value 1     | Value 2     | Value 3     |
  | Value 4     | Value 5     | Value 6     |
  \endgroup
  ```

# Example Slide Styles

## Side-by-Side Content

- For symmetric content (two equal columns):
  ```markdown
  ::: columns
  :::: {.column width=50%}
  **Left Heading**
  - Point 1
  - Point 2
  ::::
  :::: {.column width=50%}
  **Right Heading**
  - Point 1
  - Point 2
  ::::
  :::
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
