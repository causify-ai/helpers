---
name: paper.fix_figures
description: Fix figures in a LaTeX paper by ensuring every figure has a label, caption, and is referenced in the text
---

# Check References

- Make sure every picture and table has a label and caption and it's referenced
  in the text
- Captions should only contain a reference to what is done and comments and more
  content should be in the text

# Add Captions and Labels

- For all the figures in the latex files in the passed directory convert the
  figure adding the caption and label to the commented section.

- For instance convert

  ````latex
  %     ```
  % rendered_images:end
  % render_images:begin
  \begin{figure}[!ht]
    \centering
    \includegraphics[width=\linewidth]{figs/02_architecture.1.png}
    \caption{Confounding adjustment in causal inference}
    \label{fig:confounding_adjustment}
  \end{figure}
  % render_images:end
  ````

  to

  ````latex
  %     ```
  % caption=Confounding adjustment in causal inference
  % label=fig:confounding_adjustment
  % rendered_images:end
  % render_images:begin
  \begin{figure}[!ht]
    \centering
    \includegraphics[width=\linewidth]{figs/02_architecture.1.png}
    \caption{Confounding adjustment in causal inference}
    \label{fig:confounding_adjustment}
  \end{figure}
  % render_images:end
  ````

# Create Labels and Captions from Scratch

- If a figure has no caption or label, infer them from the filename and
  surrounding context
  - E.g., `figs/02_architecture.1.png` → `label=fig:architecture`,
    `caption=System architecture overview`
- Choose label names that are short, lowercase, and use underscores

# Add References in the Text

- If a figure has a label but is not cited anywhere in the text, add a
  parenthetical reference near the most relevant paragraph:
  ```latex
  (see Fig.~\ref{fig:confounding_adjustment})
  ```

# Verify No Orphaned References

- Scan the text for `\ref{fig:xxx}` or `\ref{tab:xxx}` that have no matching
  `\label{fig:xxx}` or `\label{tab:xxx}` in any figure or table environment
- Report orphaned references as warnings; do not silently delete them
