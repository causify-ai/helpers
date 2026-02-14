## Template Nodes
```
digraph WindTurbineCKG {
  rankdir=LR;
  splines=true;
  nodesep=0.8;
  ranksep=1.2;
  bgcolor="white";

subgraph cluster_legend {
  label="Legend: Node Types";
  fontsize=11;
  fontname="Helvetica";
  color=gray70;
  style="rounded,dashed";
  bgcolor="white";

  // Put every legend node on the SAME rank (same vertical alignment)
  { rank=same;
    leg_exog; leg_op; leg_latent; leg_obs; leg_health; leg_out;
  }

  leg_exog   [label="Exogenous /\nEnvironmental", shape=ellipse, style=filled, fontcolor=black, color=royalblue4, fillcolor=lightsteelblue1];
  leg_op     [label="Operational /\nMechanism", shape=box, style="rounded,filled,solid", fontcolor=black, color=darkgreen, fillcolor=palegreen1];
  leg_latent [label="Latent /\nHidden State", shape=box, style="filled,dashed", fontcolor=gray40, color=gray40, fillcolor=gray90];
  leg_obs    [label="Observable\nSignal", shape=ellipse, style=filled, fontcolor=black, color=darkgreen, fillcolor=palegreen1];
  leg_health [label="Health\nIndicator", shape=ellipse, style=filled, fontcolor=black, color=gray40, fillcolor=gray90];
  leg_out    [label="Outcome /\nTarget", shape=box, penwidth=2, style=filled, fontcolor=black, color=darkorange3, fillcolor=moccasin];

  // Keep left-to-right ordering without changing ranks
  leg_exog   -> leg_op     [style=invis, weight=10];
  leg_op     -> leg_latent [style=invis, weight=10];
  leg_latent -> leg_obs    [style=invis, weight=10];
  leg_obs    -> leg_health [style=invis, weight=10];
  leg_health -> leg_out    [style=invis, weight=10];
}

}
```

## Edge Legend
```
digraph legend {
    graph [rankdir=TB, nodesep=0.5, ranksep=0.7];
    node [shape=point, width=0, height=0, margin=0];
    edge [dir=forward];

    // Row 1: Direct causation
    {
        rank=same;
        a1 [label="", style=invis];
        b1 [label="", style=invis];
        t1 [shape=plaintext, style=solid, label="Direct causation", fontsize=16, fontname="Arial"];
        a1 -> b1 [style=solid, color=black, penwidth=3, arrowsize=1.2, minlen=3];
        b1 -> t1 [style=invis, minlen=1];
    }

    // Row 2: Uncertain/hypothesized causation
    {
        rank=same;
        a2 [label="", style=invis];
        b2 [label="", style=invis];
        t2 [shape=plaintext, style=solid, label="Uncertain / hypothesized causation", fontsize=16, fontname="Arial"];
        a2 -> b2 [style=dotted, color=black, penwidth=2, arrowsize=1.0, minlen=3];
        b2 -> t2 [style=invis, minlen=1];
    }

    // Row 3: Correlation/association
    {
        rank=same;
        a3 [label="", style=invis];
        b3 [label="", style=invis];
        t3 [shape=plaintext, style=solid, label="Correlation / association (non-causal)", fontsize=16, fontname="Arial"];
        a3 -> b3 [style=dotted, color=gray50, penwidth=2, arrowhead=none, minlen=3];
        b3 -> t3 [style=invis, minlen=1];
    }

    // Row 4: Positive effect
    {
        rank=same;
        a4 [label="", style=invis];
        b4 [label="", style=invis];
        t4 [shape=plaintext, style=solid, label="Positive effect (+ / ++ / +++)", fontsize=16, fontname="Arial"];
        a4 -> b4 [style=solid, color="#228B22", penwidth=3, arrowsize=1.2, minlen=3];
        b4 -> t4 [style=invis, minlen=1];
    }

    // Row 5: Negative effect
    {
        rank=same;
        a5 [label="", style=invis];
        b5 [label="", style=invis];
        t5 [shape=plaintext, style=solid, label="Negative effect (- / -- / ---)", fontsize=16, fontname="Arial"];
        a5 -> b5 [style=solid, color="#DC143C", penwidth=3, arrowsize=1.2, minlen=3];
        b5 -> t5 [style=invis, minlen=1];
    }

    // Row 6: Strength encoding - using <-> instead of Unicode
    {
        rank=same;
        a6 [label="", style=invis];
        b6 [label="", style=invis];
        t6 [shape=plaintext, style=solid, label="Strength encoding (weak <-> strong)", fontsize=16, fontname="Arial"];
        a6 -> b6 [style=solid, color="#228B22", penwidth=3, arrowsize=1.2, minlen=3];
        b6 -> t6 [style=invis, minlen=1];
    }

    // Force vertical ordering and left alignment
    a1 -> a2 -> a3 -> a4 -> a5 -> a6 [style=invis];
    b1 -> b2 -> b3 -> b4 -> b5 -> b6 [style=invis];
}
```
