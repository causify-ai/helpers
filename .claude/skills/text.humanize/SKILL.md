---
name: text.humanize
description: Remove AI-style writing patterns from text to make it sound more natural and human
---

## Usage
Paste your draft text at the end of this prompt. The skill returns the cleaned
text. Do not add commentary. Do not summarize what you did beyond the change log.

## Quick Reference Checklist
Use this checklist to spot AI-writing patterns at a glance before applying
detailed rules.

- **Grandiose language** — "vital", "pivotal", "groundbreaking", "robust",
  "comprehensive", "nuanced", "multifaceted", "transformative"
- **Filler hedges** — "It's worth noting that", "It's important to remember",
  "It should be noted", "Interestingly enough"
- **Throat-clearing intros** — "Let's dive in", "Let's unpack", "In this
  article, we'll"
- **Gift-wrapped endings** — "In summary", "In conclusion", "Ultimately", "At
  the end of the day"
- **Dramatic pivots** — "But here's the thing", "Here's the catch", "Here's what
  most people miss"
- **Meta-verbs** — "highlights", "underscores", "emphasizes", "showcases"
- **Overused transitions** — "Furthermore", "Moreover", "Additionally", "In
  addition to the above"
- **Vague attribution** — "some experts say", "widely covered", "significant
  attention"
- **Copy-paste metaphors** — repeating the same metaphor word-for-word 3+ times
- **Exhaustive lists** — 7–10 bullet points when 3 would do
- **Passive voice clusters** — multiple passive constructions in a row
- **Rhetorical section openers** — "So what does this mean for you?"
- **AI vocabulary** — "delve", "leverage" (as a verb), "reimagine", "empower",
  "unpack", "synergy"

## Detailed Rules with Examples
You are a writing editor. Your job is to remove AI-generated writing patterns
from the text below.

- Do not rewrite. Do not add ideas. Do not change meaning or voice. Just clean
  up the slop. Preserve voice, opinions, and structure. You are an editor, not a
  ghostwriter.
- If a sentence sounds better with a "rule break" (e.g., a well-placed em dash
  or a short sentence run for effect), leave it. Use judgment.
- Apply every rule below. If a pattern appears, fix it. If it doesn't appear,
  move on.

**Output format:** Return the cleaned text only. After the text, add a short
bulleted list of the specific patterns you fixed.

## Phrasing

### 1. Em Dashes
- Remove em dashes (—). Rewrite using commas, full stops, or restructure the
  sentence. One or two in a long piece is fine. Three or more is a pattern.

### 2. Corrective Antithesis
- Remove **"Not X. But Y."** constructions where you set up something the reader
  never assumed and then correct it for drama
- Just say what you mean directly

- **Bad:**
  - "This isn't because they don't trust the technology. It's because they can't
    predict it."

- **Good:**
  - "They trust the technology fine. What they can't do is predict it."

### 3. Dramatic Pivot Phrases
- Remove:
  - _"But here's the thing."_
  - _"Here's the catch."_
  - _"Here's the bind."_
  - _"Here's what most people miss."_ and similar theatrical pivots
- Fold the point into the sentence naturally.

- **Bad:**
  - "The patterns are valuable. But here's the bind: building a tool cost more
    than most could justify."

- **Good:**
  - "The patterns are valuable but building a tool to capture them cost more
    than most could justify."

### 4. Soft Hedging Language
- Remove filler hedges. Just say the thing.

- Cut phrases like:
  - "It's worth noting that"
  - "Something we've observed"
  - "This is where X really shines"
  - "It's important to remember"
  - "It should be noted"
  - "Interestingly enough"

- **Bad:**
  - "It's worth noting that this approach has shown some promising results in
    certain contexts."

- **Good:**
  - "This approach works."

### 5. Overused Transition Words
- Cut or vary "Furthermore", "Moreover", "Additionally", "In addition to the
  above" when chained together. Real writers use them sparingly.

- **Bad:**
  - "The system is fast. Furthermore, it is reliable. Moreover, it is easy to
    use. Additionally, it integrates well."

- **Good:**
  - "The system is fast, reliable, easy to use, and integrates without
    friction."

### 6. AI Vocabulary
- Replace words that AI overuses with plain alternatives:
  - "delve" → explore, look at, examine
  - "leverage" (verb) → use, apply, rely on
  - "robust" → strong, solid, reliable
  - "comprehensive" → thorough, complete, full
  - "nuanced" → subtle, layered, specific
  - "multifaceted" → complex, varied
  - "transformative" → significant, major
  - "unpack" → explain, break down
  - "reimagine" → rethink, redesign
  - "empower" → let, help, enable

### 7. Meta-Verbs
- Instead of saying something "highlights", "underscores", "emphasizes",
  "showcases", or "illustrates" a point, just explain what it shows directly.

- **Bad:**
  - "This underscores the importance of clear communication."

- **Good:**
  - "Clear communication matters here."

### 8. Passive Voice Clusters
- Flag sequences of two or more passive constructions in a row. Rewrite at least
  one in active voice to restore momentum.

- **Bad:**
  - "The report was reviewed by the team. Errors were identified. Changes were
    recommended."

- **Good:**
  - "The team reviewed the report, found errors, and recommended changes."

### 9. Rhetorical Section Openers
- Cut rhetorical questions used as section transitions ("So what does this mean
  for you?", "Why does this matter?"). Either state the answer directly or
  remove entirely.

- **Bad:**
  - "So what does this mean for your team? It means you need to rethink your
    process."

- **Good:**
  - "Your team needs to rethink its process."

## Rhythm

### 10. Staccato Rhythm
- Break up runs of short, punchy sentences that stack without variation. Combine
  some. Lengthen others. Let the rhythm follow the thinking, not a drumbeat.

- **Bad:**
  - "Now, agents act. They send emails. They modify code. They book
    appointments."

- **Good:**
  - "Agents are starting to do real things now. They'll send an email on your
    behalf or update a database, sometimes without you even realising it
    happened."

### 11. Cookie-Cutter Paragraphs
- Vary paragraph length. If every paragraph is 3–4 sentences, break some into
  one-liners and let others stretch. The shape of the text on the page should
  look uneven, like real thinking.

### 12. Gift-Wrapped Endings
- Remove summary conclusions that restate the article's points
- Cut:
  - _"In summary"_
  - _"In conclusion"_
  - _"Ultimately"_
  - _"Moving forward"_
  - _"At the end of the day"_
- End with something specific, human, or unresolved

- **Bad:**
  - "In summary, by focusing on clear communication, consistent feedback, and
    mutual trust, teams can build stronger relationships."

- **Good:**
  - "The best teams I've worked with never talked about trust. They just had
    it."

### 13. Throat-Clearing Intros
- Remove:
  - _"Let's explore"_
  - _"Let's unpack"_
  - _"Let's dive in"_
  - _"Let's break it down"_
  - _"In this article, we'll"_
- Just start. The best first sentence puts the reader in the middle of
  something.

- **Bad:**
  - "In this article, we'll explore the hidden costs of micromanagement. Let's
    dive in."

- **Good:**
  - "I micromanaged someone last Tuesday."

### 14. Exhaustive Lists
- Trim bullet lists that run to 7–10 items when 3–4 would cover the essential
  points. Long lists signal AI comprehensiveness, not human judgment. Cut the
  weakest items.

## Authenticity

### 15. Perfect Punctuation
- Don't correct every grammar "mistake" if it sounds more natural broken.
  - Fragments are fine
  - Starting with _And_ or _But_ is fine
  - A comma splice can stay if it reads well
- If the draft has personality in its punctuation, keep it.

### 16. Copy-Paste Metaphors
- If the same metaphor or phrase appears more than twice, vary the language. Use
  a pronoun, rephrase it, or trust the reader to remember.
- Never repeat a metaphor word-for-word three times.

- **Bad:**
  - "Trust is like a battery. When the trust battery is full... But when the
    trust battery runs low... To recharge the trust battery..."

- **Good:**
  - "Trust is like a battery. When it's full, you barely think about it. But let
    it drain and suddenly every interaction needs a charger."

### 17. Overexplaining the Obvious
- Cut sentences that explain things the reader already understands. If you've
  made a clear point, don't then re-explain how that point works.

- **Bad:**
  - "Trust is earned over time. You give people small tasks, observe how they
    handle them, then gradually expand their responsibilities."

- **Good:**
  - "Trust is earned. Everyone knows this. The question is whether you're
    actually giving people the chance to earn it."

### 18. Generic Examples
- Flag examples that could apply to any company or product. If an example
  doesn't contain a specific, surprising, or insider detail, it's filler. Either
  sharpen it or cut it.

- **Bad:**
  - "Take Slack, for example. By focusing on seamless team communication, they
    transformed how modern workplaces collaborate."

- **Good:**
  - "Slack solved the wrong problem brilliantly. Nobody needed another messaging
    app, but everyone needed a place to dump links and pretend they'd read them
    later."

### 19. Vague Attribution
- Avoid vague references like "some experts say...", "widely covered",
  "significant attention". Identify the actual critic, report, study, or author
  when possible. If you can't name the source, cut the claim.
