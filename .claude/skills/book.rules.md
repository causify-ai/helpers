This file contains rules and convention on how to format references to books or
papers

# Format of Authors
- List of authors is always represented as
  ```
  <Last name of first author> [et al]
  ```
- If there are more than one author use `et al`

# Format to Use in File Names

- Convert the name of a file (book or paper) into a standard format without
  characters that are unfriendly for Linux (e.g., spaces, `.` `/`, `\`) converting
  them into underscore
- Separate Year, Author and 
  ```
  <Year>.<Last_name_of_first_author>_[et_al].<Title>
  ```
- If there are more than one author use `et al`

- Example
  - **Before**
    - Ajay Agrawal, Joshua Gans, Avi Goldfarb - Prediction Machines_ The Simple Economics of Artificial Intelligence (2018, Harvard Business Review Press) - libgen.li.epub
  - **After**
    2018.Agrawal_et_al.Prediction_Machines_The_Simple_Economics_of_Artificial_Intelligence.epub

# Format for General Text

- When using references in a general file
  ```
  <Year>, <Last name of first author> [et al.], "<Title>"
  ```

- Example
  ```
  2016, Pearl et al., "Causal Inference in Statistics: A Primer"
  2008, Angrist et al., "Mostly Harmless Econometrics"
  ```

# Format in `.txt` and `.md` Files

- When using references inside a `.txt` or a `.md` file use the format:
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
