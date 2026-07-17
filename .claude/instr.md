Create a script get_catalog.py --target manning
to scrape the content of the pages
using https://www.manning.com/catalog?page=1

The output is a CSV like

Title, Author, Year, Link
"Retrieval Augmented Generation, The Seminal Papers", "Ben Auffarth", "2026", "https://www.manning.com/books/retrieval-augmented-generation-the-seminal-papers"

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
