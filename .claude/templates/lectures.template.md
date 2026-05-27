// Controlling size:
//
// ![](msml610/lectures_source/figures/Chap7_Binomial_distribution.png){height=50%}
// Bad ![Smile Emoji](assets/emoji/angry_devil.png){width=12px}
// \includegraphics[width=0.6\textwidth]{msml610/lectures_source/figures/Chap7_Binomial_distribution.png}
// ```latex[width=50%]
// ![](data605/lectures_source/images/lecture_1/lec_1_slide_4_image_1.png){ width=1cm }

# Link

[\textcolor{blue}{\underline{Hello}}](www.hello.com)
// [\textcolor{blue}{\underline{}}]()

# Color

* Color text
- Arthur Samuel (1959): Machine learning: field of study that gives computers
  the ability to \textit{learn without being explicitly programmed}
- Tom Mitchell (1998): A computer program is said to learn from experience E
  with respect to some task T and some performance measure P, if P(T) improves
  with experience E
- E.g. a computer can play to learn checkers (by playing against itself)
  memorizing which positions lead to winning a game
- \red{data}

* All colors

- **\red{red}**
- **\orange{orange}**
- **\brown{brown}**
- **\olive{olive}**
//- **\lime{lime}**
- **\green{green}**
- **\teal{teal}**
- **\cyan{cyan}**
- **\blue{blue}**
//- **\purple{purple}**
- **\violet{violet}**
//- **\magenta{magenta}**
//- **\pink{pink}**
- **\darkgray{darkgray}**
- **\gray{gray}**
//- **\lightgray{lightgray}**

* Colors 4

- \red{Red}
- \teal{Teal}
- \blue{Cyan}
- \violet{Violet}

* Colors 5

- \red{Red}
- \teal{Teal}
- \cyan{Cyan}
- \blue{Cyan}
- \violet{Violet}

* Colors 8

- \red{Red}
- \orange{Orange}
- \green{Green}
- \teal{Teal}
- \cyan{Cyan}
- \blue{Blue}
- \violet{Violet}
- \brown{Brown}

//* Colored Latex expression
//  $$ELPD_{LOO-CV} =
//    \red{\sum_i} \log
//    \violet{\int}
//    \teal{p(y_i | \theta)}
//    \blue{(\theta | y_{-i})}
//    \violet{d\theta}$$

# Lists

* Enumerated list
1. Specify models using code
2. Solve models using numerical techniques
   - Compute results, even if there is no analytical closed form
   - Solving the model can be considered a black box

* Emoji
- Applications
- Bad ![Smile Emoji](assets/emoji/angry_devil.png){ width=12px }
- Challenges
- Check mark ![](assets/emoji/check_mark.png){ width=12px }
- Cons
- Counterpoints ![](assets/emoji/balance_scale.png){ width=14px }
- E.g., ![](assets/emoji/backhand_pointing_right.png){ width=14px }
- E.g., ![](assets/emoji/pushpin_tack.png){ width=12px }
- Fail ![](assets/emoji/skull.png){ width=14px }
- Good ![](assets/emoji/emoji_smile.png){ width=12px }
- Idea ![](assets/emoji/lightbulb.png){ width=14px }
- Intuition ![](assets/emoji/lightbulb.png){ width=14px }
- Issues ![](assets/emoji/warning.png){ width=14px }
- Problem ![](assets/emoji/puzzle.png){ width=14px }
- Pros
- Question ![](assets/emoji/question_mark.png){ width=14px }
- Remark ![](assets/emoji/exclamation_mark.png){ width=14px }
- Solution ![](assets/emoji/lightbulb.png){ width=14px }
- Wrong ![](assets/emoji/wrong.png){ width=12px }

* Emoji (Mac)
- Good ![Smile Emoji](mac_emojis/emoji_smile.png){ width=12px }

# Listings

//* Python coding {.fragile}
//
//```{=latex}
//\begin{lstlisting}
//def bootstrap_median(x, n_boot):
//    // Compute n_boot sample statistics.
//    median_boot = [0.0] * n_boot
//    for i in range(n_boot):
//        // Sample with replacement.
//        x_star = sample with replacements from x
//        // Compute median for bootstrapped samples.
//        median_boot[i] = median(x_star)
//    // Compute mean and std err from approximation of sample statistics.
//    m_median = numpy.mean(median_boot)
//    se_median = numpy.std(median_boot)
//    return m_median, se_median
//```


# Formulas

* Sizes

\tiny tiny
\scriptsize scriptsize
\footnotesize footnotesize
\small small
\normalsize normalsize
\large large
\Large Large
\LARGE LARGE
\huge huge
\Huge Huge

* Aligned equation

- Hello

\begin{align*}
  a &= b + c \\
  d &= e + f
\end{align*}

\begin{align*}
\end{align*}

- World

* Formula with cases

$$
f(x) =
\begin{cases}
  x^2 & \text{if } x > 0 \\
  0 & \text{otherwise}
\end{cases}
$$
  
* System of equations

\begin{equation*}
  \begin{cases}
    3x + 5y + z = 3 \\
    7x - 2y + 4z = 4 \\
    -6x + 3y + 2z = 2
  \end{cases}
\end{equation*}

* Aligned stacked equation
- We can use PPIE and independence:
  \begin{align*}
  &\Pr(A=6 \cup B=6) \\
  &\hspace{1cm} = \Pr(A=6) + \Pr(B=6) - \Pr(A=6 \cap B=6) \\
  &\hspace{1cm} = \Pr(6) + \Pr(6) - \Pr(A=6) \cdot \Pr(B=6) \\
  \end{align*}

//* Matrix
//
//\begin{pmatrix}
//0.7 & 0.3 \\
//0.3 & 0.7
//\end{pmatrix}

* Equation

\begin{equation}
\begin{aligned}
  a &= b + c \\
  d &= e + f
\end{aligned}
\end{equation}

* Different font size

\begingroup \scriptsize
\endgroup

\begingroup
\small
... small ...
\endgroup

Normal

* Table

\begingroup \scriptsize

| Level | Symbol         | Typical Activity      |
|------------------------|----------------------|
| 1. Association | $P(y|x)$      | Seeing       |
| 2. Intervention | $P(y|do(x), z)$  | Doing, Intervening   |
| 3. Counterfactuals | $P(y_x | x', y')$  | Imagining, Retrospection |

\endgroup

\begingroup \scriptsize
\endgroup

* Align on multiple columns
\small
\begin{alignat*}{2}
& \red{\text{Divide up the evidence}}
&\quad
&= \Pr(X_{t+1} | \red{e_{1:t}, e_{t+1}})
\\
& \green{\text{Bayes rule given }} \green{e_{1:t}}
&\quad
&= \alpha \Pr(e_{t+1}|X_{t+1},\green{e_{1:t}}) \Pr(X_{t+1}|\green{e_{1:t}})
\\
& \text{\cyan{Markov sensor assumption}}
&\quad
&= \alpha \Pr(e_{t+1}|X_{t+1}) \Pr(X_{t+1}|e_{1:t})
\\
& \text{\blue{Condition on current state}}
&\quad
&= \alpha \Pr(e_{t+1}|X_{t+1}) \sum_{x_t} \Pr(X_{t+1}|\blue{x_t},\violet{e_{1:t}}) \Pr(\blue{x_t} | e_{1:t})
\\
& \text{\violet{Markov assumption}}
&\quad
&= \alpha \Pr(e_{t+1}|X_{t+1}) \sum_{x_t} \Pr(X_{t+1}|x_t) \Pr(x_t | e_{1:t})
\\
&
&\quad
&= \text{Sensor model} \times \text{Transition model} \times \text{Recursive state}
\\
\end{alignat*}

# Images

* Width
\begin{center}
  \includegraphics[width=0.6\textwidth]{msml610/lectures_source/figures/Chap7_Binomial_distribution.png}
\end{center}

![](msml610/lectures_source/figures/Chap7_Binomial_distribution.png){height=50%}

```latex[width=50%]
...
```

* Figure in the center
\vspace{-1cm}

\begin{align*}
  X & \sim Binomial(n, p) \\
  \Pr(k) & = \frac{n!}{k! (n - k)!} p^k (1 - p)^{n-k} \\
\end{align*}

\vspace{-1cm}

//![](msml610/lectures_source/figures/Chap7_Binomial_distribution.png){ height=50%}
\begin{center}
  \includegraphics[width=0.6\textwidth]{msml610/lectures_source/figures/Chap7_Binomial_distribution.png}
\end{center}

* Figure scaled down
![](msml610/lectures_source/figures/Chap7_Binomial_distribution.png){ height=50%}
![](msml610/lectures_source/figures/Chap7_Binomial_distribution.png)

# Page formatting

* Two columns (template)

::: columns
:::: {.column width=55%}

::::
:::: {.column width=40%}

::::
:::

* Two columns of equal width (example)

::: columns
:::: column
  - What should we do?
- Simulation / optimization
  - What's the best we can do?
::::
:::: column
- Item 1.
- Item 2.
- Item 3.
![Analytical sophistication](msml610/lectures_source/figures/Chap7_Chemical_shift_pymc_solution1.png)
::::
:::

* Two columns commenting a figure

::: columns
:::: {.column width=60%}
![](msml610/lectures_source/figures/Chap7_Savage_Dickey.png)
::::
:::: column
- E.g., posterior / prior = 0.76
::::
:::

* Four pieces

- Create model

::: columns
:::: {.column width=50%}
Figure 1
::::
:::: {.column width=50%}
Figure 2
::::
:::

- Solve model

::: columns
:::: {.column width=50%}
Figure 3
::::
:::: {.column width=50%}
Figure 4
::::
:::

* Tables and comments on two columns
::: columns
:::: column

\begingroup \scriptsize
| **Alarm (A)** | **P(JohnCalls\| .)** | **P(-JohnCalls \| .)** |
|-----------|--------------------|---------------------|
| True | 0.90 | 0.10 |
| False | 0.05 | 0.95 |
\endgroup

\begingroup \scriptsize
| **Alarm (A)** | **P(JohnCalls\| .)** |
|-----------|--------------------|
| True | 0.90 |
| False| 0.05 |
\endgroup

\begingroup \scriptsize
| **P(Burglary)** |
|---|
| .001 |
\endgroup

\begingroup \scriptsize
| **Burglary** | **Earthquake** | **P(Alarm \| .)** |
|---|---|---|
| T | T | .95 |
| T | F | .94 |
| ... | ... | ... |
\endgroup

::::
:::: column

// TODO: Format better

- The sum of probabilities of the actions must be 1

\vspace{1em}

- Removing the redundancy<br><br>

\vspace{1em}

- A node without parents has an unconditional probability<br><br>

\vspace{1em}

- A node with $k$ parents has $2^k$ possible rows in the table<br><br>
::::
:::

# Pictures

* Multiple images with captions

::: columns
:::: {.column width=70%}
Hello
::::
:::: {.column width=25%}
// save_screenshot.py --dst_dir lectures_source/figures --filename Lesson12_4x3_environment.png

![](msml610/lectures_source/figures/Lesson12_4x3_environment1.png)

\vspace{0.5cm}

\begin{center}
\includegraphics[width=0.5\textwidth]{msml610/lectures_source/figures/Lesson12_4x3_environment2.png}
{\scriptsize\text{Valid actions}}
\end{center}

\vspace{0.5cm}

\begin{center}
\includegraphics[width=1.0\textwidth]{msml610/lectures_source/figures/Lesson12_4x3_environment3.png}
{\scriptsize\text{Example of optimal policy}}
\end{center}
::::
:::

* Mermaid1

```mermaid
classDef roundedBox fill:#fff,stroke:#333,stroke-width:2px,rx:10,ry:10;

flowchart LR
  U["Confounder (U)"] --> X["Cause (X)"]
  U["Confounder (U)"] --> Y["Effect (Y)"]
  X["Cause (X)"] --> Y["Effect (Y)"]
```

* Styled graphviz
```graphviz
digraph BayesianFlow {
    rankdir=TB;
    splines=true;
    nodesep=1.0;
    ranksep=0.75;

    node [shape=box, style="rounded,filled", fillcolor=white, fontname="Helvetica", fontsize=12, penwidth=1.4];

    // Node styles
    Cloudy        [label="Cloudy",        fillcolor="#b3cde3"];
    Sprinkler     [label="Sprinkler",     fillcolor="#ccebc5"];
    Rain          [label="Rain",          fillcolor="#ccebc5"];
    WetGrass      [label="Wet Grass",     fillcolor="#decbe4"];
    GreenerGrass  [label="Greener Grass", fillcolor="#fed9a6"];

    // Force ranks
    { rank=same; Sprinkler; Rain; }

    // Edges
    Cloudy -> Sprinkler;
    Cloudy -> Rain;
    Sprinkler -> WetGrass;
    Rain -> WetGrass;
    WetGrass -> GreenerGrass;
}
```

* Graphviz1

```graphviz
digraph Viterbi {
    rankdir=LR;
    node [shape=ellipse, style=filled, fillcolor=lightgrey];

    // Nodes for each day and state
    S1 [label="Sunny\n0.06"];
    R1 [label="Rainy\n0.32"];
    S2 [label="Sunny\n0.0128"];
    R2 [label="Rainy\n0.1536"];
    S3 [label="Sunny\n0.0553"];
    R3 [label="Rainy\n0.0184"];

    // Transitions Day 1 → Day 2
    S1 -> S2 [label="×0.7"];
    S1 -> R2 [label="×0.3"];
    R1 -> S2 [label="×0.4"];
    R1 -> R2 [label="×0.6"];

    // Transitions Day 2 → Day 3
    S2 -> S3 [label="×0.7"];
    S2 -> R3 [label="×0.3"];
    R2 -> S3 [label="×0.4"];
    R2 -> R3 [label="×0.6"];

    // Highlight most likely path
    edge [color=blue, penwidth=1.4];
    R1 -> R2;
    R2 -> S3;
}
```

* Graphviz2

```graphviz
digraph BayesianNetwork {
    node [shape=ellipse, style=filled, fillcolor=lightblue];
    Burglary -> Alarm [label="1"];
    Earthquake -> Alarm [label="1"];
    Alarm -> JohnCalls [label="4"];
    Alarm -> MaryCalls [label="4"];
}
```

```tikz
% Define the sets as circles with transparency
\draw[thick, fill=blue!20, opacity=0.6] (0,0) circle (1.5cm);
\node at (0,0) {$A$};

\draw[thick, fill=red!20, opacity=0.6] (4,0) circle (1.5cm);
\node at (4,0) {$B$};

\draw[thick, fill=green!20, opacity=0.6] (2,3.5) circle (1.5cm);
\node at (2,3.5) {$C$};

% Add a title
\node[font=\bfseries] at (2,-2.5) {Pairwise Exclusive Sets};
\node[align=center] at (2,-3.3) {No overlap between any pair of sets};
```

* Latex

```latex[width=50%]
\begin{tabular}{lcr}
\toprule
Name & Age & Score \\
\midrule
Alice & 24 & 88 \\
Bob   & 27 & 75 \\
Carol & 22 & 93 \\
\bottomrule
\end{tabular}
```

* Latex figure

```latex
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

%\begin{center}
\begin{tikzpicture}
  \matrix[row sep=1em] {
    \node{\gridpattern{{1,0,0,0,1,0,1,0,1}}{blue}}; &
    \node{\gridpattern{{1,1,0,0,1,0,0,1,1}}{blue}}; &
    \node{\gridpattern{{1,1,0,1,0,0,0,0,0}}{blue}}; &
    \node{\(f = -1\)}; \\
    \node{\gridpattern{{0,1,1,1,0,0,0,1,0}}{green}}; &
    \node{\gridpattern{{1,0,1,0,1,0,1,0,1}}{green}}; &
    \node{\gridpattern{{1,1,0,1,0,0,0,0,1}}{green}}; &
    \node{\(f = +1\)}; \\
  };
  \node at (-0.6,-3.0) {\gridpattern{{1,0,1,0,1,0,0,0,1}}{red}};
  \node at (1.4,-3.0) {\(f = ?\)};
\end{tikzpicture}
%\end{center}
\end{document}
```

* Table

\begingroup \scriptsize
\begin{tabular}{|c|c|c|c|}
\hline
  \textbf{Definition} &
  \textbf{Univariate (Bayesian)} &
  \textbf{Univariate (Kalman)} &
  \textbf{Multivariate (Kalman)} \\
\hline
\hline
  State update &
  $\overline{\mu} = \mu + \mu_{f}$ &
  $\overline{x} = x + dx$ &
  $\overline{\vx} = \mF \vx + \mB \vu$ \\

\hline
  State uncertainty &
  $\overline{\sigma}^2 = \sigma^2 + \sigma_f^2$ &
  $\overline{P} = P + Q$ &
  $\overline{\mP} = \mF \mP \mF^T + \mQ$ \\

\hline
  Residual &
  &
  $y = z - \overline{x}$ &
  $\vy = \vz - \mH \overline{\vx}$ \\

\hline
  Kalman gain &
  &
  $K = \frac{\overline{P}}{\overline{P} + R}$ &
  $\mK = \overline{\mP} \mH^T (\mH \overline{\mP} \mH^T + \mR)^{-1}$ \\

\hline
  Updated state &
  $\hat{\mu}
  = \frac{\overline{\sigma}^2 \mu_z + \sigma_z^2 \overline{\mu}}
    {\overline{\sigma}^2 + \sigma_z^2}$ &
  $x = \overline{x} + K y$ &
  $\vx = \overline{\vx} + \mK \vy$ \\

\hline
  Upd. state uncertainty &
  $\sigma^2
  = \frac{\overline{\sigma}^2 \sigma_z^2}{\overline{\sigma}^2 + \sigma_z^2}$ &
  $P = (1 - K) \overline{P}$ &
  $\mP = (\mI - \mK \mH) \overline{\mP}$ \\
\hline
\end{tabular}
\endgroup
