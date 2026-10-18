- This file contains the conventions for working with academic papers

# Paper Rating

## Meaning

- The paper rating is an integer from 1 (low) to 5 (best)
- It estimates the authority and impact of a paper from three signals that are
  quick to check: page length, author affiliation, and citations
- It is a mechanical proxy, not the `**Score**` of a paper list entry, which is a
  judgment call (see `# Score` in `.claude/skills/paper_list.rules.md`)
- Follow the template `.claude/templates/paper_rating.template.md`

## Signals

### Page Length

- Count all the pages of the PDF, including references and appendices
- Score the count with this table:

  | Score | Pages         |
  | :---- | :------------ |
  | 5     | 35 or more    |
  | 4     | 20 to 34      |
  | 3     | 10 to 19      |
  | 2     | 5 to 9        |
  | 1     | fewer than 5  |

### Affiliation

- Read the affiliations of all the authors and score the best one
- Score it with this table:

  | Score | Best affiliation of the authors                                         |
  | :---- | :---------------------------------------------------------------------- |
  | 5     | Top 20 university (QS World University Rankings), leading industry research lab (e.g., Google DeepMind, Microsoft Research, Meta FAIR), central bank, or NBER |
  | 4     | University ranked 21 to 100, or an established industry research group  |
  | 3     | Any other university or research institute                              |
  | 2     | Company or organization with no research group                          |
  | 1     | No affiliation listed, or independent author                            |

### Citations

- Use the citation count from Semantic Scholar (`citationCount`) for the DOI or
  the arXiv ID of the paper
  - Use Google Scholar if Semantic Scholar does not have the paper
- Use the same bands as the `**Score**` in `.claude/skills/paper_list.rules.md`:

  | Score | Citations     |
  | :---- | :------------ |
  | 5     | 1000 or more  |
  | 4     | 300 to 999    |
  | 3     | 50 to 299     |
  | 2     | 10 to 49      |
  | 1     | fewer than 10 |

- For a paper under 2 years old, annualize the count before scoring:
  `citations * 2 / age_in_years`
  - `age_in_years` is the current year minus the publication year, at least 0.5
  - Note the adjustment in the rating file

## Rating

- The rating is the mean of the three scores, rounded half up to a whole number
  - Use whole numbers only: no `3.5/5`
  - Weigh the three signals equally
- If a signal cannot be found, write `unknown`, leave it out of the mean, and say
  so in the notes
  - Do not take affiliations or citation counts from memory: read them from the
    paper or from the lookup source
- Record the source and the date of the citation count, since it changes over time
- Example (illustrative values)
  - **Good**: 12 pages (3), a top 20 university (5), and 40 citations after 3
    years (2) give a mean of 3.33 and a rating of `3/5`
  - **Bad**: report the unrounded mean of the same scores as `3.33/5`
