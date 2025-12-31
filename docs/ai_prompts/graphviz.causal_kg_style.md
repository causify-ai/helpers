# Task: Represent a Causal Knowledge Graph (CKG)

You are an expert in causal inference and graphical models. 

I will give you a graphviz dot graph and your task is to produce a Graphviz/DOT
representation of that graph that follows the rules below exactly.

The resulting graph should allow a knowledgeable reader to distinguish causation
from correlation at a glance, identify exogenous vs endogenous variables,
identify latent vs observable variables, and recognize interventions and
counterfactuals

## General Graph Rules
- Use Graphviz DOT syntax
- Use a directed graph (`digraph`)
- Set `rankdir=LR` for left-to-right causal flow
- Prefer readability over compactness

## Node Representation Rules

### Exogenous vs Endogenous Variables
- Exogenous variable (no causal parents)
  - `shape=ellipse`
  - `penwidth=2`
- Endogenous variable (has at least one causal parent)
  - `shape=box,rounded`
  - `penwidth=1` (default)
- Target variable (one that has no descendant and it's under study)
  - `shape=box`
  - `penwidth=2`

### Observable vs Unobservable (Latent) Variables
- Observable variable
  - `style=solid`
  - `color=black`
- Unobservable / latent variable
  - `style=dashed`
  - `color=gray40`
  - `fontcolor=gray40`

### Special Node Types
- Intervened variable (`do(X)`)
  - `shape=doublecircle`
  - Label must be `do(X)`
  - Incoming causal edges to `X` must be omitted
- Counterfactual variable
  - `style=dotted`
  - Label must include counterfactual context (e.g., `Y | do(X=1)`)

## Edge Representation Rules

### Causation
- Direct causal effect
  - Solid arrow (`->`)
  - `style=solid`
  - `dir=forward`
- Uncertain or hypothesized causation
  - Dotted arrow (`style=dotted`)
  - Must include `label="?"`

### Correlation / Association (Non-causal)
- Correlation without causal claim
  - Dashed edge
  - No arrowheads (`dir=none`)
  - Use `constraint=false`
  - Label with a statistical symbol

### Effect Attributes (Optional)
- Positive effect
  - Default arrowhead
  - Label `"+"`
- Negative effect
  - Default arrowhead
  - Label `"-"`
- Effect strength
  - Encode using multiple symbols
    - Strong: `+++`, `---`
    - Weak: `+`, `-`

## Confounding and Common Causes
- Represent confounders explicitly
  - Use a latent node with dashed gray styling
  - Draw causal arrows from the confounder to each affected variable
- Do not use correlation edges to represent confounding

## Layout and Structure
- Use subgraphs (clusters) when helpful
  - Structural model vs observational associations
  - Different time slices or mechanisms
- Ensure correlation edges do not affect node ranking

## Output Requirements
- Output only valid Graphviz/DOT code without triple backticks
- Do not explain the code in natural language
- Follow all visual and semantic conventions above exactly

