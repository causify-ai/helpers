# Graphviz diagram
- Any graphviz diagram should be follow the template below

```graphviz
digraph BayesianFlow {
    splines=true;
    nodesep=1.0;
    ranksep=0.75;

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

# Tikz diagram
- Any Tikz diagram should be follow the template below

```latex
\usepackage{tikz}
\begin{document}

\newcommand{\gridpattern}[2]{
...
}

%\begin{center}
\begin{tikzpicture}
...
%\end{center}
\end{document}
```

# Graphic image

- Any graphic image should follow the template below

```image
High-end editorial illustration for a business technology magazine. 

Lighting is studio-grade and cinematic, with realistic reflections on glass and
metal. Materials look physically accurate (optical glass, brushed aluminum, matte
screens).

Color palette is restrained and corporate: cool whites, slate blues, soft greens,
with small warm amber highlights for contrast.

Style is photorealistic illustration with the polish of a Fortune-500 annual
report or The Economist technology cover — no fantasy, no cyberpunk, no glowing
neon, no cartoon outlines.

<description of the content>
```
