---
description: Read a set of chapters from a book
---

# Step 1: Read index
- Given a markdown file like $BOOK
  - E.g., /Users/saggese/src/notes1/books/2023.Facure.Causal_Inference.md

- Read the file that has close to it like $BOOK.index.md containing the table of
  content
  - E.g., /Users/saggese/src/notes1/books/2023.Facure.Causal_Inference.md ->
    /Users/saggese/src/notes1/books/2023.Facure.Causal_Inference.index.md

- The table of content stores a mapping from title of chapters to line in the
  file storing the text $BOOK

# Step 2: Read portion of the content
- If the user specifies a chapter to read $CHAPTER, find the chapter in the index
- Read the chapter that corresponds to what the user is asking for
- Report the chapters and sub-chapters read using a nested lists of markdown
  bullets

# Step 3: Summarize content
- Summarize using the same structure of the content read each chapter and
  subchapter with 2-3 bullet points in markdown

# Step 4: Answer questions
