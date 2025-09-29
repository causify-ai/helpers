<!-- toc -->

- [Tool Evaluation Guide](#tool-evaluation-guide)
  * [1. Define Comparison Attributes](#1-define-comparison-attributes)
  * [2. Track in a Shared Google Sheet](#2-track-in-a-shared-google-sheet)
  * [3. Pick Top 5 Tools to Investigate Further](#3-pick-top-5-tools-to-investigate-further)
  * [4. Try 2–3 Tools Hands-On](#4-try-2%E2%80%933-tools-hands-on)
    + [Example Tool Categories](#example-tool-categories)
  * [5. Review and Demo](#5-review-and-demo)
  * [Notes](#notes)

<!-- tocstop -->

# Tool Evaluation Guide

This guide outlines how to consistently evaluate third-party tools (e.g.,
coverage reporting, code review, CI add-ons) across our repositories such as
`cmamp`, `helpers`, `tutorials`, etc.

## 1. Define Comparison Attributes

Use the following attributes to evaluate and compare tools:

| Attribute          | Description                                                    |
| ------------------ | -------------------------------------------------------------- |
| Tool Name          | Name of the tool                                               |
| Website            | Official website link                                          |
| Integration Method | GitHub Action, CLI, manual, automatic pull, etc.               |
| Deployment Model   | SaaS only, Local only, or Both                                 |
| Open Source        | Yes / No                                                       |
| Free for OSS       | Yes / No                                                       |
| Pricing            | Cost per month, usage tiers, or credits                        |
| Pricing Page       | Link to official pricing documentation                         |
| Setup Effort       | Point to repo / Needs config / Requires signup or subscription |
| Use Cases          | Coverage, code review, security, dependency management, etc.   |
| Reference Link     | Blog post, GitHub repo, YouTube demo, testimonial, etc.        |
| Pros               | Key strengths or features                                      |
| Cons               | Known limitations or pain points                               |

## 2. Track in a Shared Google Sheet

- Use a shared Google Sheet to create a comparison matrix with the attributes
  above
- Each row represents one tool
- Columns can include notes, ratings, or checkboxes
- Assign owners for research if needed

## 3. Pick Top 5 Tools to Investigate Further

- Based on research, select the top 5 tools that appear promising
- Prioritize tools with:
  - Minimal setup requirements
  - Strong community or support
  - Transparent pricing

## 4. Try 2–3 Tools Hands-On

Choose 2–3 tools to test directly in one of the repositories.

### Example Tool Categories

- **Tools requiring minimal setup**

  These tools can be tested with little to no configuration. You often just sign
  in with GitHub and point them to a repository.
  - **Codecov** – Add their GitHub App and upload a coverage file from CI. No
    manual config needed for basic use. Works out of the box with popular test
    runners like `pytest` (Python) and `jest` (JavaScript)
  - **Coveralls** – GitHub integration and CI upload. Just set the
    `COVERALLS_REPO_TOKEN` secret and push coverage results
  - **Code Climate** – GitHub integration with default support for several
    languages. Free for open source but may need a `.codeclimate.yml` file for
    customization

- **Tools requiring moderate setup**

  These tools require sign-up, access configuration, or CLI installation. Setup
  is still manageable but not zero-effort.
  - **SonarCloud** – Requires GitHub login, project import, and token setup in
    CI. Needs a `sonar-project.properties` file. Provides static analysis and
    coverage reporting
  - **DeepSource** – GitHub login and permission to scan repos. Auto-detects
    config, but may need a `.deepsource.toml` to fine-tune rules or exclusions

- **Tools that may require subscription or approval**

  These tools focus on enterprise or compliance use cases. Setup may require
  contacting sales, credit card details, or legal approval.
  - **Snyk** – Security scanning for dependencies. Free for public repos but
    requires signup and CLI setup. Some features (e.g., PR gating, private repo
    scanning) require a paid plan
  - **FOSSA** – License compliance scanning. Requires signup, and although an
    open-source tier exists, full access may require approval or paid plans

## 5. Review and Demo

- After testing, note impressions and any issues
- Schedule a 30-minute demo to share findings with the team
- Decide as a group whether to adopt, postpone, or reject each tool

## Notes

- Not all tools can be judged fairly from documentation alone
- Actual usage is necessary to evaluate UX, speed, noise, and integration pain
  points
