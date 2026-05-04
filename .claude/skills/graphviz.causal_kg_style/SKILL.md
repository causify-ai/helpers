---
description: Represent a causal knowledge graph in Graphviz DOT format following visual conventions for causal inference
---

You are an expert in causal inference and graphical models.

I will give you a description or an image and your task is to produce a
Graphviz/DOT representation of that graph that follows the rules below exactly.

The resulting graph should allow a knowledgeable reader to
- Distinguish causation from correlation at a glance
- Identify exogenous vs endogenous variables
- Identify latent vs observable variables
- Recognize interventions and counterfactuals

Use color to distinguish variable types consistently.

# Step 1: Generate DOT file

## General Graph Rules

- Use Graphviz DOT syntax
- Use a directed graph (`digraph`)
- Set `rankdir=LR` for left-to-right causal flow
- Use both `color` (border) and `fillcolor` + `style=filled` to encode variable
  type (do not rely on color alone; keep shape conventions too)

## Node Representation Rules

### Variable Type Colors (Required)

Use these colors consistently for node borders/fills:

- Exogenous variable: color=#408AB0, fillcolor=#EAF3F8
- Endogenous variable: color=#62D4A4, fillcolor=#EAF9F3
- Target variable: color=#F8D476, fillcolor=#FFF6DA
- Latent (unobservable) variable: color=#183B4A, fillcolor=#E6EEF1
- Intervened variable (do(X)): color=#DE5470, fillcolor=#FBE6EC
- Counterfactual variable: color=#183B4A, fillcolor=#E6EEF1

### Exogenous vs Endogenous vs Target

- Exogenous variable (no causal parents)
  - `shape=ellipse`
  - `penwidth=2`
  - Must be colored using the exogenous palette above
- Endogenous variable (has at least one causal parent)
  - `shape=box,rounded`
  - `penwidth=1` (default)
  - Must be colored using the endogenous palette above
- Target variable (no descendants; under study)
  - `shape=box`
  - `penwidth=2`
  - Must be colored using the target palette above

### Observable vs Unobservable (Latent) Variables

- Observable variable
  - `style=filled,solid`
  - Use the appropriate color palette for its type
    (exogenous/endogenous/target/etc.)
  - `fontcolor=black`
- Unobservable / latent variable
  - `style="filled,dashed"`
  - Must use the latent palette above (`color=gray40`, `fillcolor=gray90`,
    `fontcolor=gray40`)
  - Keep the same shape rule based on exogenous/endogenous/target if known;
    otherwise default to `shape=ellipse`

### Special Node Types

- Intervened variable (`do(X)`)
  - `shape=doublecircle`
  - Label must be `do(X)`
  - `style=filled,solid`
  - Must use the intervened palette above
  - Incoming causal edges to `X` must be omitted
- Counterfactual variable
  - `style="filled,dotted"`
  - Must use the counterfactual palette above
  - Label must include counterfactual context (e.g., `Y | do(X=1)`)

## Edge Representation Rules

### Causation

- Direct causal effect
  - Solid arrow (`->`)
  - `style=solid`
  - `dir=forward`
  - Default `color=black` unless overridden by effect sign/strength
- Uncertain or hypothesized causation
  - Dotted arrow (`style=dotted`)
  - Must include `label="?"`
  - Use `color=gray30`

### Correlation / Association (Non-causal)

- Correlation without causal claim
  - Dashed edge
  - No arrowheads (`dir=none`)
  - Use `constraint=false`
  - Label with a statistical symbol
  - Use `color=gray50`

### Effect Attributes (Optional)

- Positive effect
  - Default arrowhead
  - Label `"+"`, `"++"`, `"+++"`
  - Use `color=darkgreen`
- Negative effect
  - Default arrowhead
  - Label `"-"`, `"--"`, `"---"`
  - Use `color=firebrick3`
- Effect strength (by symbols in the label)
  - Strong: `+++`, `---`
  - Weak: `+`, `-`

## Confounding and Common Causes

- Represent confounders explicitly
  - Use a latent node with dashed gray styling (latent palette)
  - Draw causal arrows from the confounder to each affected variable
- Do not use correlation edges to represent confounding

## Layout and Structure

- Use subgraphs (clusters) when helpful
  - Structural model vs observational associations
  - Different time slices or mechanisms
- Ensure correlation edges do not affect node ranking (`constraint=false`)

# Step 2: Save File

- Save the output in a `causal_graph.dot` file

## Output Requirements

- Output only valid Graphviz/DOT code without triple backticks
- Do not explain the code in natural language
- Follow all visual and semantic conventions above exactly

# Step 3: Render Graph

- After the graph description is generated, generate an image with:
  ```
  > dot -Tpng causal_graph.dot -o causal_graph.png
  > open causal_graph.png
  ```

# Step 4: Read the PNG file

- If an image was specified, read the PNG file
- If the generated PNG image is very different from the input image:
  - Find the differences in terms of layout
  - Apply changes to the causal_graph.dot to approximate the input image
