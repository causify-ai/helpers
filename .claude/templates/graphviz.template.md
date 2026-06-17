- Maintain the structure of the text as it is

## Template
- All graphviz dot diagram must follow the template below
  ```graphviz
  digraph <name> {
      splines=true;
      nodesep=0.8;
      ranksep=0.8;

      node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, penwidth=1.7];

      // Nodes
      Rain       [label="Rain", fillcolor="#A6C8F4"];
      WetGrass   [label="WetGrass", fillcolor="#B2E2B2"];
      Cover      [label="Cover", fillcolor="#FFD1A6"];
      Evaporate  [label="Evaporate", fillcolor="#F4A6A6"];
      Sprinkler  [label="Sprinkler", fillcolor="#A0D6D1"];
      Dew        [label="Dew", fillcolor="#A6E7F4"];

      // Force ranks
      { rank=same; Cover; Evaporate; }
      { rank=same; Sprinkler; Dew; }

      // Edges
      Rain -> WetGrass;
      Rain -> Cover;
      Rain -> Evaporate;
      Cover -> WetGrass [label="blocks", style=dashed];
      Evaporate -> WetGrass [label="blocks", style=dashed];
      Sprinkler -> WetGrass;
      Dew -> WetGrass;
  }
  ```

## Annotating Nodes with Probability Expressions

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
