# Google Technical Writing

<!-- toc -->

- [Google'S Technical Writing: Part 1](#googles-technical-writing-part-1)
  * [Define New or Unfamiliar](#define-new-or-unfamiliar)
  * [Use Terms Consistently](#use-terms-consistently)
  * [Use Acronyms Properly](#use-acronyms-properly)
  * [Use Strong Verbs](#use-strong-verbs)
  * [Use Short Sentences](#use-short-sentences)
  * [Remove Fillers](#remove-fillers)
  * [Focus Each Paragraph on a Single Topic](#focus-each-paragraph-on-a-single-topic)
  * [Avoid Wall-Of-Text](#avoid-wall-of-text)
  * [Answer What, Why, and How](#answer-what-why-and-how)
  * [Know Your Audience](#know-your-audience)
  * [State Document'S Scope](#state-documents-scope)
  * [Summarize the Key Points at the Start](#summarize-the-key-points-at-the-start)
- [Google'S Technical Writing: Part 2](#googles-technical-writing-part-2)
  * [Adopt a Style Guide](#adopt-a-style-guide)
  * [Think Like Your Audience](#think-like-your-audience)
  * [Come Back to It Later](#come-back-to-it-later)
  * [Organizing Large Docs](#organizing-large-docs)
- [Resources](#resources)

<!-- tocstop -->

// From https://developers.google.com/tech-writing/one/

## Google'S Technical Writing: Part 1

### Define New or Unfamiliar

- If your document introduces a term, define the term
- If the term already exists, link to a good existing explanation

### Use Terms Consistently

- Don't change the name of something while talking about it
  - E.g., `Protocol Buffers` vs `protobufs`
- You can do something like:
  ```
  Protocol Buffers (or protobufs for short)
  ```

### Use Acronyms Properly

- On the initial use of an unfamiliar acronym spell out the full term
- E.g., `Telekinetic Tactile Network (TTN) ...`
- Acronyms take attention to be expanded in their full form
- Sometimes acronyms develop their own identity (e.g., HTML)
- An acronym should be significantly shorter than the full term
- Don't define acronyms that will be used only a few times

### Use Strong Verbs

- Choose precise, strong, and specific verbs
  - Weak verbs are "be", "occur", "happen"

**Good**
```
Dividing by zero raises the exception.
```

**Bad**
```
The exception occurs when dividing by zero.
```

### Use Short Sentences

- Each sentence should convey a single idea, thought, concept
  - Break long sentences into single-idea sentences
- Convert long sentences into bulleted list
  - E.g., "and", "or" suggest to refactor into a bulleted list

### Remove Fillers

**Good**
```
This design document describes Project Frambus.
```

**Bad**
```
This design document provides a detailed description of Project Frambus.
```

### Focus Each Paragraph on a Single Topic

- A paragraph is an independent unit of logic
- Ruthlessly delete sentence that doesn't relate to the current topic

### Avoid Wall-Of-Text

- Readers often ignore long paragraphs
- Paragraphs should contain 3 to 5 sentences

### Answer What, Why, and How

- Good paragraphs answer the following questions
  - What: what are you trying to tell your reader?
  - Why: why is it important for the reader to know this?
  - How: how should the reader use this knowledge

- E.g.,
  - [What]: The `garp()` function returns the delta between a dataset's mean and
    median.
  - [Why]: Many people believe unquestioningly that a mean always holds the
    truth. However, a mean is easily influenced by a few very large or very
    small data points.
  - [How]: Call `garp()` to help determine whether a few very large or very
    small data points are influencing the mean too much. A relatively small
    `garp()` value suggests that the mean is more meaningful than when the
    `garp()` value is relatively high.

### Know Your Audience

- Your document needs to provide information that your audience needs but
  doesn't already have
  - Define your audience
    - E.g., software engineers vs program managers
    - E.g., graduate students vs first-year undergraduate students
  - Determine what your audience needs to learn
    - E.g.,
      ```verbatim
      After reading the documentation, the audience will know how to do the
      following tasks
      - Use ...
      - Do ...
      ...
      ```
  - Fit documentation to your audience
    - Avoid the "curse of knowledge": experts forget that novices don't know
      what you already know

### State Document'S Scope

- A good document begins by defining its scope and its non-scope, e.g.,
  ```
  This document describes the design of Project Frambus, but not the related
  technology Froobus.
  ```

### Summarize the Key Points at the Start

- Ensure that the start of your document answers your readers' essential
  questions
- The first page of a document determines if the readers makes it to page two

// From https://developers.google.com/tech-writing/two

## Google'S Technical Writing: Part 2

### Adopt a Style Guide

- Many companies and large open source projects adopt a style guide for
  documentation
  - E.g., https://developers.google.com/style

### Think Like Your Audience

- Step back and try to read your draft from the point of view of your audience

### Come Back to It Later

- After you write your first (or second or third) draft, set it aside
- Come back later and read it with fresh eyes to find things you can improve

### Organizing Large Docs

- You can organize a collection of information into
  - A longer standalone document; or
  - Set of shorter interconnected documents (e.g., website, wiki)
    - Pros: easy to find information searching in the single back

// TODO

## Resources

- [https://developers.google.com/tech-writing/overview]