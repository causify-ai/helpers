---
description: Read, criticize, and propose improvements for proposed slides
model: opus
---

# Goal
- Criticize a proposed slide deck (or subset of slides) and propose concrete,
  ranked improvements to content, flow, visual clarity, pacing, and audience fit

# Workflow

## Step 1: Read Context
- Read `.claude/skills/slides.rules.md` for the rules that slides follow

- Read the slide deck file
  - Note the deck title, target audience, and stated learning objectives (if any)
  - Read all slides sequentially to understand the narrative arc
  - Note speaker notes, timing cues, or visual descriptions if present

- Read context about the presentation:
  - What is the venue/duration? (lecture, conference talk, workshop, etc.)
  - What is the assumed prior knowledge?
  - Are there adjacent slide decks or prerequisite presentations?

## Step 2: Criticize
- Read `.claude/skills/text.criticize/SKILL.md` to understand general approaches
  to review and criticize text

- Evaluate along these axes, reporting only issues you are confident about:
  - **Slide-level clarity**:
    - Too much text per slide (exceeds visible time + cognitive load)
    - Unclear titles or takeaways
    - Missing or weak visual hierarchy
    - Jargon or concepts assumed without intro
  - **Deck flow & narrative**:
    - Abrupt transitions between ideas
    - Slides in wrong order (should come earlier/later)
    - Orphaned or tangential slides
    - Missing bridge slides to connect concepts
    - Pacing (too slow intro, rushed conclusion, uneven rhythm)
  - **Audience fit**:
    - Level too high or too low for stated audience
    - Unexplained background assumptions
    - Missing motivation or context for why this matters
  - **Structure & consistency**:
    - Inconsistent formatting or visual style
    - Slides that break the template (if one exists)
    - Missing agenda, summary, or chapter breaks
    - Speaker notes missing or incomplete
  - **Timing & scope**:
    - Deck too long or too short for the slot
    - Individual slides that will overrun or underrun their time
    - Candidates to expand, collapse, or split
  - **Engagement & visuals**:
    - Slides that rely only on bullet points (no visuals, examples, or storytelling)
    - Diagrams or images that are unclear or misleading
    - Missing opportunities for interaction or questions

- Rank each issue by severity:
  - **HIGH**: loses attention, undermines a key point, or creates wrong takeaway
  - **MEDIUM**: reduces clarity or engagement
  - **LOW**: minor polish or consistency

- Follow `.claude/skills/text.criticize/SKILL.md` tone and structure

## Step 3: Wait for Approval
- Present the criticism to the user
- Wait for the user to select items to apply by index and give corrections
- Only then edit the slide deck
- Preserve formatting, speaker notes, and visual structure
