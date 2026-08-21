This file contains rules and convention on how to format references to books or
papers

# Format for General Text
- When using references in a `txt` or `md` file, the format for any reference is like:
  ```
  <Year>, <Last name of first author> [et al.], "<Title>" (<Link>)
  ```

- Authors are always represented as:
  ```
  <Last name of first author> [et al]
  ```
  using `et al` if there are more than one author

- E.g.,
  ```
  2008, Angrist et al., "Mostly Harmless Econometrics" (https://economics.mit.edu/files/11869)
  2009, Pearl, "Causality: Models, Reasoning, and Inference" (https://bayes.cs.ucla.edu/BOOK-2K)
  ```

- For the link prefer links to Arxiv or to publicly available resources
  - Make sure the links exist, otherwise add a ` ???` after the link

- Keep the references in reverse chronological order (from recent to old), e.g.,
  ```
  # Foundational Causal Inference

  // Books:
  // - 2016, Pearl et al., "Causal Inference in Statistics: A Primer"
  //   (https://ftp.cs.ucla.edu/pub/stat_ser/r481.pdf)
  // - 2009, Pearl, "Causality: Models, Reasoning, and Inference"
  //   (https://bayes.cs.ucla.edu/BOOK-2K)
  // - 2008, Angrist et al., "Mostly Harmless Econometrics"
  //   (https://economics.mit.edu/files/11869)

  // Articles:
  // - 2005, Rotnitzky et al., "Semiparametric regression adjustment to estimate policy effects"
  //   (https://cdn1.sph.harvard.edu/wp-content/uploads/sites/343/2013/03/semiparametric_regression.pdf)
  // - 1974, Rubin, "Estimating causal effects of treatments in randomized and nonrandomized studies"
  //   (https://dash.harvard.edu/bitstream/handle/1/3401028/rubin_estimate.pdf)
  ```

# Format to Use in File Names
- Convert the name of a file (book or paper) into a standard format without
  characters that are unfriendly for Linux (e.g., spaces, . , / \) converting
  them into underscore
- Separate Year, Author and Title with a `.`
  ```
  <Year>.<Last_name_of_first_author>_[et_al].<Title>
  ```
  - If there are more than one author use `et al`
- Remove the link if present
- Keep the extension

- E.g.,
  - **Bad**
    ```
    Ajay Agrawal, Joshua Gans, Avi Goldfarb - Prediction Machines\_ The Simple Economics of Artificial Intelligence (2018, Harvard Business Review Press) - libgen.li.epub
    ```
  - **Good**
    ```
    2018.Agrawal_et_al.Prediction_Machines_The_Simple_Economics_of_Artificial_Intelligence.epub
    ```

# When Searching for References
- Use academic and technical references such as:
  - **Papers**: journal articles and conference papers
    - Search Google Scholar, arXiv, IEEE Xplore, ACM Digital Library, Springer, or
      Elsevier
  - **Books**: textbooks and monographs
    - Search Google Books, publisher sites, or library catalogs
  - **Authoritative articles**: official documentation and major tech research blogs
    - Search the source's official site directly (e.g., OpenAI, Google Research,
      Anthropic)
  - **Technical reports**: lab and industry research reports
    - Search the lab's official publications page or arXiv (e.g., DeepMind, OpenAI,
      Google Research, Microsoft Research)
  - **Whitepapers**: vendor or consortium position papers
    - Search the vendor's official site (e.g., NVIDIA, AWS whitepapers page)
  - **Theses and dissertations**: PhD and Master's theses
    - Search ProQuest Dissertations and Theses, or the university's institutional
      repository
  - **Patents**: filed inventions
    - Search Google Patents or the USPTO database
  - **Standards and specifications**: formal technical standards
    - Search IETF RFCs, ISO, W3C, or the IEEE Standards Association
  - **Preprints**: manuscripts not yet peer-reviewed
    - Search arXiv, bioRxiv, or SSRN
  - **Benchmark and dataset papers**: papers introducing a benchmark or dataset
    - Search Papers With Code, Hugging Face Datasets, or OpenML
  - **Talks and keynotes**: recorded conference presentations
    - Search the conference's official channel (e.g., SlidesLive, YouTube) for venues
      like NeurIPS or ICML
- Add direct arXiv or free-access versions where available
- Include working URLs for each reference when possible
- Prefer recent references over old ones
