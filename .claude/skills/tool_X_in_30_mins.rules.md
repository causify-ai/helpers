- This document contains all the rules for creating a markdown file following the
  "tool_X_in_30_mins" format.

- These are quick-reference guides that introduce a developer tool in
  approximately 30 minutes of reading time, covering its purpose, basic usage,
  and practical examples.

## Format

- Follow the format and conventions in:
  - `@.claude/skills/blog.rules.md`
  - `@.claude/skills/markdown.rules.md`
  - `@.claude/skills/text.rules.bullet_points.md`

## Typical Section Order

1. Front matter
2. TL;DR and `<!-- more -->`
3. Introduction
4. Why [Tool]?
5. Installation
6. Basic Usage
7. Core Features (subsections)
8. Advanced Features
9. Practical Examples
10. Configuration (if applicable)
11. Tips and Tricks
12. Common Gotchas
13. Integration Sections
14. Comparison Tables

## Document Structure

- **Introduction**: Explain why the tool matters and the problem it solves
  - Use bullet points to highlight main benefits
  - Address the tool's core advantages over alternatives
  - Include speed/performance comparisons when relevant

- **Why Tool?**: Dedicated section covering:
  - Key features and strengths
  - Speed benchmarks (comparison table with competitors)
  - Performance metrics compared to similar tools
  - Use bullet points for feature list

- **Installation**: Step-by-step installation instructions
  - Cover multiple platforms (macOS, Linux, Windows) when applicable
  - Include verification commands to confirm successful installation
  - Use code blocks with `bash` language tag
  - Prepend all commands with `>`

- **Basic Usage / Core Features**: Fundamental operations
  - Break into logical subsections using `###` headers
  - Each subsection covers one main use case
  - Include example commands with actual output when helpful
  - Show before/after or input/output patterns

- **Advanced Features / Project Management**: More complex scenarios
  - Use `###` for subsection headers
  - Cover configuration options
  - Include locking mechanisms and dependency management
  - Show integration patterns with other tools

- **Practical Examples / Tips and Tricks**: Real-world scenarios
  - Provide copy-paste ready commands
  - Include common workflows
  - Address edge cases and troubleshooting

- **Common Gotchas**: Potential pitfalls
  - Warn about common mistakes
  - Provide solutions for expected issues
  - Include error messages when relevant

- **Integration Sections** (optional): Tool-specific integrations
  - Docker integration
  - CI/CD integration
  - IDE/Editor support
  - Shell configuration

- **Comparison Tables**: Compare with related tools
  - Always include comparison with direct competitors
  - Use tables to show feature differences
  - Include performance metrics when available
  - Format: `| Feature | Tool Name | Competitor |`

## Writing Style and Formatting

- **Code blocks**: All code blocks must have language tags (e.g., `bash`,
  `python`, `yaml`, `toml`)
  - Commands in bash blocks must be prefixed with `>`
  - Output shown after commands should not have `>`
  - Use `bash` for shell commands, specific language tags for code samples

- **Bullet points**: Organize information in bullet lists
  - Follow rules in `.claude/skills/text.rules.bullet_points.md`
  - Each bullet expresses one atomic idea
  - Use nested bullets for elaboration, examples, or hierarchical information
  - Do not end bullet points with periods

- **Headers**: Structure with proper hierarchy
  - Start with level 1 headers for main sections (`#`)
  - Use level 2 headers for subsections (`##`)
  - Use level 3 headers for sub-subsections (`###`)
  - Capitalize major words in headers
  - Avoid level 4 headers; convert to bold text or bullets instead

- **Bold and emphasis**: Use strategically
  - Bold key tool names and important concepts
  - Bold at the start of list items for labels/headers
  - Use italic for questions or hypothetical scenarios
  - Do not abuse bold throughout explanations

- **Verbatim (backticks)**: Use for technical terms
  - Tool names: `` `tool_name` ``
  - Commands: `` `pip install` ``
  - File names and config files: `` `pyproject.toml` ``
  - Code elements: `` `variable_name` ``

- **Tables**: Use for comparisons
  - Left-aligned columns (`:-------`)
  - Include feature comparisons between tools
  - Show performance metrics side-by-side
  - Always have clear headers

- **Examples and demonstrations**: Show practical usage
  - Include realistic command examples
  - Show actual output when helpful
  - Use ellipsis (`…`) or `...` for truncated output
  - Provide context before code blocks
  - Demonstrate both success and error cases when instructive

## Content Guidelines

- **Word count**: Target 2,000–4,000 words for a comprehensive "in 30 mins" guide
- **Tone**: Professional and informative, suitable for developers
- **Audience**: Developers familiar with basic command line and package management
- **Clarity**: Prioritize clarity and brevity over completeness
- **Examples**: Use concrete, copy-paste ready examples
- **Performance**: Highlight speed and efficiency advantages when relevant
- **Commands**: Show variations and flags that users commonly need
- **Warnings**: Include "Common Gotchas" or "Known Issues" section when applicable

## Output Formatting

- Use only ASCII characters (no emojis or special symbols)
- Avoid decorative formatting like `---` separators
- Use `->` instead of arrows
- Maintain consistent spacing between sections
- Use blank lines to separate different content blocks
