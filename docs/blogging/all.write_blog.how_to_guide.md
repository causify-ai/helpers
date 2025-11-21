<!-- toc -->

- [How to Write a Blog for Causify](#how-to-write-a-blog-for-causify)
  * [Position of Blogs in Our Documentation Ecosystem](#position-of-blogs-in-our-documentation-ecosystem)
  * [Invariants](#invariants)
  * [Practical Guidelines for Blogs](#practical-guidelines-for-blogs)
  * [Checklist for Preparing a Blog (File in a Github Issue)](#checklist-for-preparing-a-blog-file-in-a-github-issue)
    + [Learn How We Write and Organize Documentation](#learn-how-we-write-and-organize-documentation)
    + [Learn Our Style and Tooling](#learn-our-style-and-tooling)
    + [Learn How We Organize Projects and Tutorials](#learn-how-we-organize-projects-and-tutorials)
    + [Read Examples of Past Blogs](#read-examples-of-past-blogs)
    + [Apply Blog-Specific Best Practices](#apply-blog-specific-best-practices)
  * [Summary](#summary)

<!-- tocstop -->

# How to Write a Blog for Causify

Writing a blog at Causify is about communicating our ideas clearly, while
re-using and connecting with the broader body of internal documentation, white
papers, tutorials, and research notes we already create. This guide explains how
blogs fit into our documentation ecosystem, what principles to follow, and
provides a checklist to get started.

## Position of Blogs in Our Documentation Ecosystem

- There is often overlap between:
  - Internal white papers (aka an internal report)
  - Journal / conference papers
  - Blogs
  - Internal documentation
  - Research Google Docs

## Invariants

- Internal documentation: Contains all the information at maximum detail,
  organized using the Diataxis framework
- Internal white paper: Abstracted version of internal documentation,
  emphasizing architecture and high-level results
- Journal / conference paper: A succinct and highly structured version of a
  white paper
- Blog: Often the union of several documentation pieces. A blog should give a
  high-level view of the work and why it matters.
  - Point to detailed technical resources (internal docs, repos, tutorials)
    instead of duplicating them.
  - Do a comparison with the state-of-the-art (SOTA), and explain why our
    approach is better, different, or more practical.
  - Keep it accessible as blogs are not white papers.
- Research Google Docs: Living documents to store ongoing project information
  before being consolidated.

Note: It is common for a project to start with a blog and then evolve into a
journal/conference paper.

## Practical Guidelines for Blogs

- **Level of detail**
  - Blogs should stay at a high level
  - Only go deep if it is explicitly a tutorial-style blog
- **References**
  - Always link to technical resources (internal docs, repos, code, or white
    papers) for implementation details.
- **Comparisons**
  - Compare against SOTA or industry norms, and clearly explain why our approach
    is novel, impactful, or more effective.
- **Workflow & Tools**
  - Markdown first: When writing technical blogs (that don’t need exec input),
    keep everything in markdown and work directly in GitHub.
    - Easier to manage diffs, PRs, reviews, and formatting.
    - Enables diagrams via Mermaid, and integration with internal rendering
      tools.
  - Google Docs only if needed: Use Google Docs when we need broader
    collaboration (e.g., exec reviews, heavy commenting).
    - Conversion tools exist to move from GDocs → Markdown.
- **Assets and Diagrams**
  - Use `./helpers_root/dev_scripts_helpers/documentation/render_images.py` to
    render images/diagrams.

## Checklist for Preparing a Blog (File in a Github Issue)

When starting a blog on a project, open a GitHub Issue and track the following:

### Learn How We Write and Organize Documentation

- [ ] Read docs in [`//helpers/docs/documentation_meta`]
  - [ ] [`//helpers/docs/documentation_meta/all.diataxis.explanation.md`]
  - [ ] [`//helpers/docs/documentation_meta/all.google_technical_writing.how_to_guide.md`]
  - [ ] [`//helpers/docs/documentation_meta/all.writing_docs.how_to_guide.md]

### Learn Our Style and Tooling

- Read rules enforced by `linter` and `ai_review.py`
  - [ ] Read ./docs/code_guidelines/all.coding_style_guidelines.reference.md

### Learn How We Organize Projects and Tutorials

- [ ] Read [`//tutorials/class_project_instructions/README.md`]
- [ ] Read [`//tutorials/docs/all.learn_X_in_60_minutes.how_to_guide.md`]

### Read Examples of Past Blogs

- [ ] [`//tutorials/blogs`]

### Apply Blog-Specific Best Practices

- [ ] Keep content at a high level (unless it’s a tutorial).
- [ ] Link to internal docs, repos, or white papers for details.
- [ ] Compare against SOTA and articulate why our work is different/better.
- [ ] Decide workflow:
  - [ ] Markdown-first (default)
  - [ ] Google Docs (if executive review required)
- [ ] Use image rendering tools (`render_images.py`) or Mermaid for diagrams.
- [ ] If using GDocs, plan for Markdown conversion before publication.

## Summary

A Causify blog is not just a write-up, it’s a way of:

- Communicating _why_ a project matters,
- Placing our work in the context of SOTA, and
- Connecting readers to deeper resources if they want details.

By following this guide and checklist, contributors can ensure our blogs are
consistent, informative, and impactful.