# Check References

- Make sure every picture and table has a label and caption and it's referenced
  in the text
- Captions should only contain a reference to what is done and comments and more
  content should be in the text

# Add Captions and Labels

- For all the figures in the latex files in the passed directory convert the
  figure adding the caption and label to the commented section.

- For instance convert
  ```latex
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
  ```

  to

  ```latex
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
  ```
