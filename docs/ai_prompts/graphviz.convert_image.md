1) Given the graphviz dot below

digraph legend {
    graph [rankdir=TB, nodesep=0.5, ranksep=0.7];
    node [shape=point, width=0, height=0, margin=0];
    edge [dir=forward];

    // Row 1: Direct causation
    {
        rank=same;
        a1 [label="", style=invis];
        b1 [label="", style=invis];
        t1 [shape=plaintext, style=solid, label="          Direct causation", fontsize=16, fontname="Arial"];
        a1 -> b1 [style=solid, color=black, penwidth=3, arrowsize=1.2, minlen=3];
        b1 -> t1 [style=invis, minlen=1];
    }

    // Row 2: Uncertain/hypothesized causation
    {
        rank=same;
        a2 [label="", style=invis];
        b2 [label="", style=invis];
        t2 [shape=plaintext, style=solid, label="          Uncertain / hypothesized causation", fontsize=16, fontname="Arial"];
        a2 -> b2 [style=dotted, color=black, penwidth=2, arrowsize=1.0, minlen=3];
        b2 -> t2 [style=invis, minlen=1];
    }

    // Row 3: Correlation/association
    {
        rank=same;
        a3 [label="", style=invis];
        b3 [label="", style=invis];
        t3 [shape=plaintext, style=solid, label="          Correlation / association (non-causal)", fontsize=16, fontname="Arial"];
        a3 -> b3 [style=dotted, color=gray50, penwidth=2, arrowhead=none, minlen=3];
        b3 -> t3 [style=invis, minlen=1];
    }

    // Row 4: Positive effect
    {
        rank=same;
        a4 [label="", style=invis];
        b4 [label="", style=invis];
        t4 [shape=plaintext, style=solid, label="          Positive effect (+ / ++ / +++)", fontsize=16, fontname="Arial"];
        a4 -> b4 [style=solid, color="#228B22", penwidth=3, arrowsize=1.2, minlen=3];
        b4 -> t4 [style=invis, minlen=1];
    }

    // Row 5: Negative effect
    {
        rank=same;
        a5 [label="", style=invis];
        b5 [label="", style=invis];
        t5 [shape=plaintext, style=solid, label="          Negative effect (- / -- / ---)", fontsize=16, fontname="Arial"];
        a5 -> b5 [style=solid, color="#DC143C", penwidth=3, arrowsize=1.2, minlen=3];
        b5 -> t5 [style=invis, minlen=1];
    }

    // Row 6: Strength encoding - using <-> instead of Unicode
    {
        rank=same;
        a6 [label="", style=invis];
        b6 [label="", style=invis];
        t6 [shape=plaintext, style=solid, label="          Strength encoding (weak <-> strong)", fontsize=16, fontname="Arial"];
        a6 -> b6 [style=solid, color="#228B22", penwidth=3, arrowsize=1.2, minlen=3];
        b6 -> t6 [style=invis, minlen=1];
    }

    // Force vertical ordering and left alignment
    a1 -> a2 -> a3 -> a4 -> a5 -> a6 [style=invis];
    b1 -> b2 -> b3 -> b4 -> b5 -> b6 [style=invis];
}

2) Create a graphviz dot to match exactly the figure.png

3) Use
./helpers_root/dev_scripts_helpers/documentation/dockerized_graphviz.py to
generate a png

4) Keep tweaking it until it looks like the figure
