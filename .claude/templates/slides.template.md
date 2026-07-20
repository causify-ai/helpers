# Example Slide Styles

## Frontmatter

// type=UMD_slides
// course_title=MSML610: Advanced Machine Learning
// lesson_title=L03.1: Knowledge Representation
// slides_engine=typst
// references=
// - Russell et al.: _"Artificial Intelligence: A Modern Approach"_ (4th ed, 2020)
//  - Chap 7: Logical agents
//  - Chap 8, First-order logic
//  - Chap 9: Inference in first-order logic
//  - Chap 10, Knowledge representation

## Side-by-Side Symmetric Content

- For symmetric content use two equal columns:
  ```markdown
  | **Left Heading** | **Right Heading** |
  |---|---|
  | - Point 1<br>- Point 2 | - Point 1<br>- Point 2 |
  ```

### Example
  ```
  | Property | Chatbot | Agent |
  |---|---|---|
  | Output | Text only | Text and side effects (files, API calls, transactions) |
  | State | Conversation history | Environment state + memory |
  | Loop | Single turn → response | Perceive → plan → act, repeated |
  | Failure mode | Wrong answer | Wrong answer *or* wrong action taken |
  ```

## Side-by-Side Asymmetric Content
- For asymmetric content (text + diagram):
  ```markdown
  ::: columns
  :::: {.column width=65%}
  - Main content with text
  - Multiple bullet points
  - Detailed explanation
  ::::
  :::: {.column width=30%}
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

  - @Definition@: <Term> is [concise definition in plain language]
    - Property or characteristic 1
    - Property or characteristic 2
    - Property or characteristic 3

  - Mathematically:
    $$
    [mathematical formula or equation]
    $$

  - **Example**: [concrete, real-world scenario that demonstrates the concept]
  ```

### Example
  ```markdown
  * Machine Learning: Definition

  - @Definition@: Machine learning is building machines to do useful things without being 
    explicitly programmed
    - Learns from experience
    - Improves with data
    - Performs tasks without hardcoded rules

  - **Formally**: _"A computer program is said to learn from experience E with respect 
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

### Example
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
