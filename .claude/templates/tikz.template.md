- Skeletons and worked examples for TikZ figures inside `.smd` lecture slides
- See `.claude/skills/tikz.rules.md` for the fence-type contract, color
  palette, and polish rules these examples follow
- Pick `` ```tikz `` by default; only reach for `` ```raw_latex `` when the
  figure needs a `\newcommand`, extra `\usetikzlibrary{...}`, or
  `\begin{tikzpicture}[...]`-level options (see "Choosing a Fence Type")

# Choosing a Fence Type

| Need | Fence |
|---|---|
| Plain drawing commands, default libraries are enough | `` ```tikz `` |
| Named styles / `font=...` shared across the whole picture | `` ```raw_latex `` (needs `\begin{tikzpicture}[...]`) |
| `arrows.meta`, `shapes.geometric`, `calc`, `fit`, `backgrounds` | `` ```raw_latex `` |
| A parameterized sub-figure reused several times (`\newcommand`) | `` ```raw_latex `` |
| Multiple `\begin{tikzpicture}` in one figure | `` ```raw_latex `` |

# `tikz` Fence (Default)

## Skeleton

- Fence header: `` ```tikz `` or `` ```tikz[width=NN%] ``; omit the
  `[width=NN%]` when the figure already fits its column at native scale
  (tune the drawing's own coordinates / `scale=` instead)

```tikz
% Drawing commands only -- no \documentclass, \usepackage, \begin{document},
% \begin{tikzpicture}, or \end{...}: render_images.py adds all of that.
% Optional shared styling goes through \tikzset{}, since there is no
% \begin{tikzpicture}[...] bracket to hook into here.
\tikzset{
  mystyle/.style={draw=blue!70!black, fill=blue!10, rounded corners},
}
\draw[thick] (0,0) -- (3,0);
\node[mystyle] at (1.5,1) {Label};
```

## Examples

### Concentric Circles (Concept Hierarchy)

Nested categories (e.g. AI ⊃ ML ⊃ DL ⊃ LLMs), each ring a `\definecolor` from
the shared palette (see `tikz.rules.md` "Colors"):

```tikz
% Define colors.
\definecolor{AIcolor}{RGB}{244,166,166}    % Red/Pink
\definecolor{MLcolor}{RGB}{178,226,178}    % Green
\definecolor{DLcolor}{RGB}{160,214,209}    % Teal
\definecolor{LLMcolor}{RGB}{198,166,244}   % Purple

% Draw AI circle.
\fill[AIcolor] (0,0) circle (3);
\draw (0,0) circle (3);
\node[above] at (0,2) {\textbf{AI}};

% Draw ML circle inside AI.
\fill[MLcolor] (0.5,-0.5) circle (2);
\draw (0.5,-0.5) circle (2);
\node[above] at (0.5,0.5) {\textbf{ML}};

% Draw DL circle inside ML.
\fill[DLcolor] (1,-1) circle (1);
\draw (1,-1) circle (1);
\node[above] at (1,-0.6) {\textbf{DL}};

% Draw LLM circle inside DL.
\fill[LLMcolor] (1.2,-1.2) circle (0.6);
\draw (1.2,-1.2) circle (0.6);
\node[above] at (1.2,-1.4) {\textbf{LLMs}};
```

### Overlapping Sets

Colored, unfilled circles to show overlap between events/sets:

```tikz[width=90%]
% Draw the three overlapping colored circles.
\draw[thick, red] (0,0) circle(2cm);         % B1
\draw[thick, green] (1,0.5) circle(2cm);     % B2
\draw[thick, blue] (0.5,-1) circle(2cm);     % B3

% Colored labels.
\node[text=red] at (-2.3,0) {$\mathcal{B}_1$};
\node[text=green] at (2.2,0.7) {$\mathcal{B}_2$};
\node[text=blue] at (0.3,-2.5) {$\mathcal{B}_3$};
```

### Rectangle with Labeled Points and a Separator

A bounding box with points, symbol markers, and a dashed classification
boundary:

```tikz
% Draw rectangle.
\draw[thick] (0,0) rectangle (5,3.5);

% Define coordinates for points.
\coordinate (A) at (2.5,3);   % top circle
\coordinate (B) at (3.8,2);   % right cross
\coordinate (C) at (2.5,1);   % bottom circle
\coordinate (D) at (1,1.2);   % left cross

% Draw symbols.
\node at (A) {\Large $\circ$};
\node at (B) {\Large $\times$};
\node at (C) {\Large $\circ$};
\node at (D) {\Large $\times$};

% Add labels.
\node[above right] at (A) {$A$};
\node[above left] at (B) {$B$};
\node[below right] at (C) {$C$};
\node[below left] at (D) {$D$};

% Draw single separating line.
\draw[red, dotted, thick] (5, 0) -- (0, 3.5);
```

### Axis with Labeled Regions

A number line with samples, a decision boundary, and region labels, built
with `\foreach`:

```tikz
% Draw axis.
\draw[thick,->] (-1,0) -- (8,0) node[right] {};

% Draw negative samples (crosses).
\foreach \i in {0, 1, 2, 3} {
    \draw[thick, red] (\i,0) node[below=3pt] {$x_{\the\numexpr\i+1}$} node {\textsf{x}};
}
\node at (3.5, -0.3) {$\cdots$};

% Draw decision boundary.
\draw[thick, dotted, blue] (4.5,-0.3) -- (4.5,1.2) node[above] {$a$};

% Draw positive samples (circles).
\foreach \i in {5, 6, 7} {
    \draw[thick, blue] (\i,0) circle (3pt);
}
\node at (7,0) [below=3pt] {$x_N$};

% Labels for h(x).
\node at (2,0.8) {$h(x) = -1$};
\node at (6,0.8) {$h(x) = +1$};
\draw[thick,blue,->] (4.5,0.4) -- (7,0.4);
```

# `raw_latex` Fence (Custom Preamble / Reusable Macros)

## Skeleton

- Fence header: `` ```raw_latex `` or `` ```raw_latex[width=NN%] ``, used the
  same way as `` ```tikz[width=NN%] `` for sizing

```raw_latex
\documentclass[tikz]{standalone}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning}

\begin{document}
\begin{tikzpicture}[
  font=\sffamily,
  mystyle/.style={draw=blue!70!black, fill=blue!10, rounded corners},
]
\draw[thick] (0,0) -- (3,0);
\node[mystyle] at (1.5,1) {Label};
\end{tikzpicture}
\end{document}
```

## Examples

### Diagonal Timeline with Alternating Labels

Named per-picture styles (`year/.style`, `event/.style`), `\foreach` over a
tuple list, and events alternating above/below the line:

```raw_latex
\documentclass[tikz]{standalone}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning}

\begin{document}
\begin{tikzpicture}[
  font=\sffamily,
  year/.style={font=\large\bfseries, text=blue!70!black},
  circlemark/.style={
    draw=blue!70!black, fill=white, line width=2pt, circle, minimum size=10pt
  },
  event/.style={
    align=left, text width=5.5cm, font=\large
  }
]

% Diagonal timeline.
\draw[blue!70!black, thick] (0,0) -- (10,10);

% Adjusted coordinates: x and y increase together.
\foreach \i/\x/\y in {
  1950/0/0, 1960/2/2, 1970/4/4, 1980/6/6, 1990/8/8, 2000/10/10
} {
  \node[circlemark] at (\x,\y) {};
  \node[year, left=5pt] at (\x-0.1,\y-0.0) {\i};
}

% Events alternating left and right of the line.
\node[event, above left=6pt and 6pt] at (1,1) {
  \textbf{Milestone A}\\
  Detail 1\\
  Detail 2
};
\node[event, below right=6pt and 6pt] at (3,3) {
  \textbf{Milestone B}\\
  Detail 1
};

\end{tikzpicture}
\end{document}
```

### Curve with Shaded Regions and Axis Ticks

Custom axes, `\foreach`-generated tick labels, shaded background rectangles,
and a smooth `plot coordinates` curve:

```raw_latex[width=62%]
\documentclass[tikz]{standalone}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}

\begin{document}
\begin{tikzpicture}[font=\sffamily]
  % Axes.
  \draw[-{Latex[length=3mm]}, thick] (0,0) -- (15.5,0) node[right] {\small Year};
  \draw[-{Latex[length=3mm]}, thick] (0,0) -- (0,6.8) node[above, align=left] {\small Y};

  % Ticks.
  \foreach \x/\lbl in {0/1950, 4/1970, 8/1990, 12/2010} {
    \draw (\x,0) -- (\x,-0.12);
    \node[below, font=\scriptsize] at (\x,-0.2) {\lbl};
  }

  % Shaded region (qualitative, not measured data).
  \fill[red!8] (4.8,0) rectangle (6.0,6.6);

  % Curve.
  \draw[blue!70!black, very thick, smooth]
    plot coordinates {
      (0,0.3) (1.2,1.0) (2.4,2.4) (3.0,3.4) (3.8,3.0)
      (4.8,0.8) (5.6,0.9) (6.0,1.8) (6.6,3.2) (7.0,3.6)
    };

  \node[font=\scriptsize, align=center, red!60!black] at (5.4,0.35) {Region\\Label};
\end{tikzpicture}
\end{document}
```

### Parameterized Sub-Figure (`\newcommand`)

A reusable sub-figure defined once with `\newcommand`, then instantiated
several times inside a `matrix`:

```raw_latex
\documentclass[tikz]{standalone}
\usepackage{tikz}
\begin{document}

\newcommand{\gridpattern}[2]{
  \begin{tikzpicture}[scale=0.4]
    \foreach \x in {0,...,2}{
      \foreach \y in {0,...,2}{
        \pgfmathsetmacro{\v}{#1[\y*3+\x]}
        \draw[black] (\x,-\y) rectangle ++(1,-1); % draw grid cell
        \ifnum \v=1
          \fill[#2] (\x+0.1,-\y-0.1) rectangle ++(0.8,-0.8); % slightly smaller fill
        \fi
      }
    }
  \end{tikzpicture}
}

\begin{tikzpicture}
  \matrix[row sep=1em] {
    \node{\gridpattern{{1,0,0,1,0,1,0,1,0}}{blue}}; &
    \node{\gridpattern{{1,0,0,0,0,1,1,0,1}}{blue}}; &
    \node{\(f = -1\)}; \\
    \node{\gridpattern{{0,0,1,0,1,0,1,0,0}}{green}}; &
    \node{\gridpattern{{0,1,0,1,0,1,0,1,0}}{green}}; &
    \node{\(f = +1\)}; \\
  };
\end{tikzpicture}
\end{document}
```
