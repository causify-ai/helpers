---
description: Reduce the text in slide leaving the structure unchanged
---

# Role
- You are an expert writer of slides and presentations
- Your role is specified in `@.claude/skills/role.md`

## Subset of slides
- If there are tokens `<START>` and `<END>` you will process only the text
  between those tokens
- Otherwise you process the entire file

## Follow conventions
- Follow the conventions in `@.claude/skills/slides.rules.md`

## Slide title
- If a line starts with an asterisk `*`, it's the slide title and leave it
  unchanged

## Keep the structure
- Maintain the sequence of slides, the comments, and the headers
- Maintain the structure of the text in terms of bullet and sub-bullet points
- Keep all the figures
- Leave bold lines untouched
  - E.g.,
    ```
    - **Collections of data**
      - Aggregated, organized data sets for analysis
      - E.g., customer purchase histories in a CRM system
    ```
  - Good
    ```
    - **Collections of data**
      - Organized datasets for analysis
      - E.g., customer purchase histories in CRM
    ```
  - Bad
    ```
    - **Collections of data**: organized datasets for analysis
      - E.g., customer purchase histories in CRM
    ```

## Reduce text
- Reduce text keeping the structure of the bullets untouched
  - Write directly to the audience using "you"
  - Be concise: remove filler words (e.g., "the", "that", "very")
  - Use active voice (e.g., "Improve accuracy," not "Accuracy can be improved")
  - Prefer short phrases over full sentences
- E.g.,
  <input>
  ```
  * Slide title
  - This is a very long bullet point that is not clear and should be removed
  - This is a clear bullet point that should be kept
  ```
  </input>

  <output>
  ```
  * Slide title
  - This is a clear bullet point that should be kept
  ```
  </output>

- Example
  <input>
  - **Collections of data**
    - Aggregated, organized data sets for analysis
    - E.g., customer purchase histories in a CRM system

  - **Descriptive statistics**
    - Summary metrics: mean, median, mode, standard deviation
    - E.g., average sales per quarter to understand trends

  - **Historical reports**
    - Examination of _past performance_
    - E.g., monthly sales reports for past fiscal year

  - **Dashboards**
    - Visual displays of key metrics for insights
    - E.g., dashboard showing quarterly revenue, expenses

  - **Models**
    - Statistical representations to _forecast, explain phenomena_
    - E.g., model to anticipate customer churn based on behavioral data
  </input>

  <output>
  - **Collections of data**
    - Organized datasets for analysis  
    - E.g., customer purchase histories in a CRM  

  - **Descriptive statistics**
    - Key metrics: mean, median, mode, standard deviation  
    - E.g., average quarterly sales to track trends  

  - **Historical reports**
    - Review of _past performance_  
    - E.g., monthly sales reports from last year  

  - **Dashboards**
    - Visuals of key metrics for quick insights  
    - E.g., quarterly revenue and expense dashboard  

  - **Models**
    - Statistical tools to _forecast, explain_  
    - E.g., churn prediction from customer behavior
  </output>
