---
description: Add, improve text tags using bold and italic
model: haiku
---

# Goal
- Review a chapter (or a set of chapters) in a book to add bold and italic when
  needed

# Workflow

## Gather Context
- Read `.claude/skills/book.rules.md`

## Render Bold and Italic Based on the Type of File
- Render bold depending on the type of file:
  - `#strong[...]` in Typst
  - `\textbb{...}` in Latex
  - `**...**` in markdown
- Render italic depending on the type of file:
  - `#emph[...]` in Typst
  - `\textit{...}` in Latex
  - `_..._` in markdown

## Improve Roadmap and Summary Chapters
- Do not use bold
- Use italic for terms that are introduced and important

### Example of Summary

- Input
  ```
  From there, the discussion turns to the languages available for encoding knowledge,
  spanning natural language, programming languages, propositional logic, and
  first-order logic, each offering a different point in that tradeoff space. Semantics
  then pins down what it means for a knowledge base to be "about" the world: how
  symbols are grounded in referents, what a model is, and what it means for a sentence
  to be satisfied. Reasoning builds on that semantic foundation by defining entailment
  (what follows from what), inference (the mechanical process of deriving new
  sentences), and the twin guarantees of soundness and completeness that connect the
  two. With these pieces in place, the focus shifts to agents that actually use
  represented knowledge: from simple reflex agents, through rule-based systems, to full
  knowledge-based agents that maintain an internal knowledge base and query it before
  acting. Finally, ontologies provide the large-scale organizational scaffolding,
  specifying the categories, relations, and axioms that let knowledge be shared and
  reused across tasks and domains.
  ```

- Output
  ```
  From there, the discussion turns to the #emph[languages] available for encoding
  knowledge, spanning natural language, programming languages, propositional logic, and
  first-order logic, each offering a different point in that tradeoff space.
  #emph[Semantics] then pins down what it means for a knowledge base to be "about" the
   world: how symbols are grounded in referents, what a model is, and what it means for
   a sentence to be satisfied. #emph[Reasoning] builds on that semantic foundation by
   defining #emph[entailment] (what follows from what), #emph[inference] (the
   mechanical process of deriving new sentences), and the twin guarantees of
   #emph[soundness] and #emph[completeness] that connect the two. With these pieces in
   place, the focus shifts to #emph[agents] that actually use represented knowledge:
   from simple reflex agents, through rule-based systems, to full knowledge-based
   agents that maintain an internal knowledge base and query it before acting. Finally,
   #emph[ontologies] provide the large-scale organizational scaffolding, specifying the
  categories, relations, and axioms that let knowledge be shared and reused across
  tasks and domains.
  ```

## Improve Other Chapters
- Use bold for definitions of a term
- Use italic to highlight important concepts

### Example: Apply Bold to Chapter

- Input
  ```
  KR defines two essential aspects of any encoding. Syntax determines
  how knowledge is organized: whether as a flat set of propositions, a hierarchy
  of classes and instances, or a graph of interconnected concepts.
  Semantics determines what the encoded statements actually mean: the
  formal interpretation that lets a reasoner distinguish valid inferences from
  invalid ones. Without clear semantics, a knowledge base is just syntax; without
  clear structure, it becomes unwieldy as the domain grows.
  ```

- Output
  ```
  KR defines two essential aspects of any encoding. #strong[Syntax] determines
  how knowledge is organized: whether as a flat set of propositions, a hierarchy
  of classes and instances, or a graph of interconnected concepts.
  #strong[Semantics] determines what the encoded statements actually mean: the
  formal interpretation that lets a reasoner distinguish valid inferences from
  invalid ones. Without clear semantics, a knowledge base is just syntax; without
  clear structure, it becomes unwieldy as the domain grows.
  ```

### Example: Apply Italic to Chapter

- Input
  ```
  Machines need to reason about the world, not just recognize patterns. A
  medical AI trained on patient data can predict diseases with impressive
  accuracy, but to explain a diagnosis to a doctor, it needs structured
  knowledge that captures relationships between symptoms, conditions, and
  treatments. Without that structure, prediction divorced from reasoning is
  often useless.
  ```

- Output
  ```
  Machines need to #emph[reason] about the world, not just recognize patterns. A
  medical AI trained on patient data can #emph[predict] diseases with impressive
  accuracy, but to #emph[explain] a diagnosis to a doctor, it needs structured
  knowledge that captures relationships between symptoms, conditions, and
  treatments. Without that structure, prediction divorced from reasoning is
  often useless.
  ```

## Write Result
- Update the file with this
