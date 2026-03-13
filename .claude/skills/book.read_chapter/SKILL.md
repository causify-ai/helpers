---
description: Extract and summarize specific chapters from a book
---

# Purpose

Extract chapters from a markdown-based book file, summarize their content, and answer questions about the material.

# When to Use

- User specifies one or more chapter names or numbers to read
- User asks questions about content from a specific book
- User wants a summary of book chapters for review or reference

# When NOT to Use

- Reading entire books without specific chapter selection
- Working with non-markdown book formats (PDF, EPUB, etc.)
- Books without a corresponding `.index.md` file

# How It Works

## Step 1: Locate the Index File

Given a book markdown file (e.g., `/Users/saggese/src/notes1/books/2023.Facure.Causal_Inference.md`), find the corresponding index file by appending `.index.md` to the book filename.

- Expected index file: `/Users/saggese/src/notes1/books/2023.Facure.Causal_Inference.index.md`
- The index file contains a table of contents that maps chapter titles to line numbers in the book markdown file

## Step 2: Identify Requested Chapters

Search the index for chapters matching the user's request by:
- Exact chapter name match (case-insensitive)
- Chapter number if applicable
- Partial name matching if exact match not found

Report which chapters will be read using nested markdown bullets showing the
chapter hierarchy (chapters and subchapters).

## Step 3: Extract Chapter Content

Use the line numbers from the index to extract the requested chapter text from the book markdown file.

Return the content to the user for context.

## Step 4: Summarize Content

Write a summary using the same structure of the chapter and subchapter in
markdown headers
- Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)
- Use the chapter numbers that come from the book

For each chapter and subchapter read:
- Create 2-3 bullet points capturing the main ideas
- Use nested markdown bullets with maximal clarity and fewer words
- Use Latex notation for formulas
- Avoid non-ASCII symbols

## Step 5: Answer Follow-up Questions

Answer any questions the user asks about the content just read, referencing
specific sections or concepts from the chapter summary.

# Example

- Input
```
User: "Read Chapter 3 from the Facure Causal Inference book"
```

- Output
```
# Chapters to read:
- Chapter 3: Graphical Models
  - 3.1 Directed Acyclic Graphs (DAGs)
  - 3.2 d-separation and Conditional Independence

# Summary:

- **Chapter 3: Graphical Models**: DAGs represent causal relationships through
  nodes and directed edges; d-separation criterion determines conditional
  independence from graph structure
  - **3.1 DAGs**: Nodes represent variables, edges represent direct causal
    effects, acyclicity prevents circular reasoning
  - **3.2 d-separation**: Variables are d-separated if no open path exists;
    d-separation implies conditional independence under causal model assumptions
```
