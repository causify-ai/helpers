---
description: Enrich a slide with references to academic papers and books
---

# Role
- Your role is specified in `@.claude/skills/role.md`

# Goal
- Your task is to review the content of the file with slides and add references
  to related material

- For each section at level 1 (#) and level 2 (##)
  - Add supporting academic references (papers, journals, conference papers,
    books, or authoritative articles).
    - Prefer sources from Google Scholar, arXiv, IEEE, ACM, Springer, Elsevier,
      official documentation, and major tech research blogs.
    - Add direct arXiv / free-access versions where available
    - Include working URLs for each reference when possible
    - Prefer recent references rather than old

# Output format
- Add a comment before each line `//`
- Print the references for books and articles
- Use the format:
  ```
  - <Year>, <Last name of first author> [et al.], "<Title>"
  ```
- Keep the references in reverse chronological order

- Example
  ```
  # Foundational Causal Inference

  // Books:
  // - 2016, Pearl et al., "Causal Inference in Statistics: A Primer"
  //   https://ftp.cs.ucla.edu/pub/stat_ser/r481.pdf
  // - 2009, Pearl, "Causality: Models, Reasoning, and Inference"
  //   https://bayes.cs.ucla.edu/BOOK-2K
  // - 2008, Angrist et al., "Mostly Harmless Econometrics"
  //   https://economics.mit.edu/files/11869

  // Articles:
  // - 2005, Rotnitzky et al., "Semiparametric regression adjustment to estimate policy effects"
  //   https://cdn1.sph.harvard.edu/wp-content/uploads/sites/343/2013/03/semiparametric_regression.pdf
  // - 1974, Rubin, "Estimating causal effects of treatments in randomized and nonrandomized studies"
  //   https://dash.harvard.edu/bitstream/handle/1/3401028/rubin_estimate.pdf  (free Harvard repository copy)
  ```
