<!-- toc -->

- [Claude Skills](#claude-skills)
  * [What Are Skills?](#what-are-skills)
  * [How Skills Work: Progressive Disclosure](#how-skills-work-progressive-disclosure)
  * [Key Advantages Over Alternatives](#key-advantages-over-alternatives)
    + [Compared to Openai'S Gpts](#compared-to-openais-gpts)
    + [Compared to Custom Instructions](#compared-to-custom-instructions)
    + [Token Efficiency vs MCP](#token-efficiency-vs-mcp)
  * [Real-World Applications](#real-world-applications)
  * [Platform Availability](#platform-availability)
  * [Creating Your First Skill: Example](#creating-your-first-skill-example)
  * [Getting Started](#getting-started)
    + [**Getting Started**](#getting-started)
    + [**Going Deeper**](#going-deeper)

<!-- tocstop -->

# Claude Skills

- Claude Skills
  - Transforms Claude from a general-purpose AI into a specialized agent
  - Tailors Claude to specific workflows and organizational needs
  - Avoids starting from scratch with each conversation
  - Packages expertise, procedures, and resources into reusable components
  - Allows Claude to dynamically access these components when relevant

## What Are Skills?

- Skills Concept
  - Skills are organized folders with instructions, scripts, and resources
  - They enable Claude to perform better at specific tasks
  - Serve as custom training manuals for specialized workflows
  - Created by writing instructions in Markdown

- Structure of a Skill
  - Each Skill is a directory
  - Contains a SKILL.md file
  - SKILL.md must start with YAML frontmatter
  - YAML includes name and description metadata

## How Skills Work: Progressive Disclosure

- Skill Initialization
  - Claude scans skill files at session start
  - Reads short explanations from YAML in Markdown files
  - Efficient in token usage, approximately 30-50 tokens per skill
  - Loads full instructions and resources when a task matches a skill

- Skill Utilization
  - Enhances Claude's performance in specialized tasks
  - Examples include Excel operations and adherence to brand guidelines
  - System is composable, allowing multiple skills to integrate
  - Supports complex workflows through automatic skill collaboration

## Key Advantages Over Alternatives

### Compared to OpenAI's GPTs
While OpenAI's GPTs allow users to create and share mini-agents with custom instructions and tools, Anthropic's Skills take a more developer-centric approach, prioritizing modularity, maintainability, and governance.

### Compared to Custom Instructions
Custom instructions apply broadly to all your conversations. Skills are task-specific and only load when relevant, making them better for specialized workflows.

### Token Efficiency vs MCP
MCPs front-load thousands of tokens describing every possible capability. Skills load a 30-token description and only pull the full details when needed.

## Real-World Applications

## Platform Availability

Skills work across Claude.ai, API, and Code, giving organizations the ability to
author custom Skills through a new /v1/skills endpoint. Organizations can develop
a skill once and deploy it everywhere their teams use Claude.

## Creating Your First Skill: Example

Here's a simple example of how to create a custom skill for writing professional email responses:

```markdown
---
name: professional-email-responder
description: Writes professional email responses following company communication standards and tone guidelines
---

# Professional Email Response Skill

This skill helps create professional, consistent email responses that follow our company's communication standards.

## Guidelines

- Use a professional but approachable tone
- Include a clear subject line if creating a new email
- Structure responses with proper greeting, body, and closing
- Keep responses concise but comprehensive
- Always include a call-to-action when appropriate

## Email Structure Template

1. **Greeting**: Use "Hi [Name]," for internal communications, "Dear [Name]," for external
2. **Acknowledgment**: Briefly acknowledge their message/request
3. **Main Content**: Address their points clearly and directly
4. **Next Steps**: Specify any actions needed or timeline
5. **Closing**: Use "Best regards," for external, "Thanks," for internal

## Example Scenarios

- Meeting requests: Confirm availability and suggest alternatives if needed
- Project updates: Provide status, blockers, and next steps
- Information requests: Provide requested information with context
- Follow-ups: Reference previous conversation and specify what you need

## Tone Examples

**Good**: "Thanks for reaching out about the quarterly report. I've reviewed the numbers and have a few questions about the methodology used in section 3."

**Avoid**: "Got your email. The report thing - I'm confused about part 3."

When responding to emails, always consider the recipient's role, the urgency of the matter, and company hierarchy.
```

## Getting Started

Creating skills is simple. The "skill-creator" skill provides interactive guidance: Claude asks about your workflow, generates the folder structure, formats the SKILL.md file, and bundles the resources you need.

To enable Skills:
1. Enable Skills in your Claude settings
2. For Team and Enterprise users, admins must first enable Skills organization-wide
3. Start creating your first skill using the template above
4. Skills are included in



https://github.com/anthropics/skills/tree/main

https://support.claude.com/en/articles/12512198-how-to-create-custom-skills

https://support.claude.com/en/articles/12512180-using-skills-in-claude

https://support.claude.com/en/articles/12512198-how-to-create-custom-skills

https://support.claude.com/en/articles/12580051-teach-claude-your-way-of-working-using-skills

Getting started
Help Center: Using Skills - Setup and troubleshooting

How to create a skill with Claude - Build your first Skill with Claude's guidance

Going deeper
Skill authoring best practices - Learn the principles behind effective Skills

Agent skills overview - Understand how Skills work under the hood

Skill cookbooks - Working examples you can adapt


### **Getting started**

* [Help Center: Using Skills](https://support.claude.com/en/articles/12512176-what-are-skills) \- Setup and troubleshooting
* [How to create a skill with Claude](https://support.claude.com/en/articles/12599426-how-to-create-a-skill-with-claude-through-conversation) \- Build your first Skill with Claude's guidance

### **Going deeper**

* [Skill authoring best practices](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices) \- Learn the principles behind effective Skills
* [Agent skills overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) \- Understand how Skills work under the hood
* [Skill cookbooks](https://github.com/anthropics/claude-cookbooks/tree/main/skills) \- Working examples you can adapt

