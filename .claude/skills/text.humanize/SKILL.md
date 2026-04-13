---
description: Remove AI-style writing patterns from text to make it sound more natural and human
model: Haiku
---

# When to Use
- Blog posts, articles, or documentation that sound generic or corporate
- Text with recognizable AI mannerisms (hedging, dramatic pivots, clichéd
  transitions)
- Prose that needs more personality before publishing
- Cleaning up AI-written content that's factually correct but tonally flat

# When NOT to Use
- Technical documentation where corporate clarity is the actual goal
- Academic papers (formal conventions are required and deliberate)
- Text where the original voice should be preserved entirely
- Structural changes, reordering, fact-checking, or adding new ideas (editor
  role only)

# What This Skill Preserves
- Author's opinions, arguments, and claims
- Document structure and organization
- Paragraph and section order
- Core meaning and facts
- Intentional stylistic choices (fragments, unconventional punctuation, etc.)

# Workflow
- Read the Pattern Checklist to identify obvious AI markers
- Apply the 19 Detailed Rules systematically (below)
- Decide for each rule: remove the pattern OR keep it (if it serves the writing)
- Return cleaned text and concise changelog

# Output Format
Return exactly two sections:

- Cleaned text: edited content with AI patterns removed
- Changes: bulleted list of specific patterns fixed

Example:
```
[cleaned text here]

Changes:
- Removed dramatic pivot ("But here's the thing...")
- Replaced "delve" → "explore"
- Cut gift-wrapped conclusion ("In summary...")
- Rewrote passive cluster in para 3 to active voice
```

# Pattern Checklist
Scan for these AI markers before applying detailed rules:

- Overused Words and Jargon
  - Grandiose: "vital", "pivotal", "groundbreaking", "robust", "comprehensive",
    "nuanced", "multifaceted", "transformative"
  - AI vocabulary: "delve", "leverage" (verb), "reimagine", "empower", "unpack",
    "synergy"
- Filler and Hedges
  - "It's worth noting that", "It's important to remember", "It should be
    noted", "Interestingly enough"
  - "Something we've observed", "This is where X really shines"
- Theatrical Transitions and Pivots
  - Throat-clearing: "Let's dive in", "Let's unpack", "In this article, we'll"
  - Dramatic pivots: "But here's the thing", "Here's the catch", "Here's what
    most people miss"
  - Overused connectors: "Furthermore", "Moreover", "Additionally", "In addition
    to the above"
  - Rhetorical openers: "So what does this mean for you?", "Why does this
    matter?"
- Structural Patterns
  - Gift-wrapped endings: "In summary", "In conclusion", "Ultimately", "At the
    end of the day", "Moving forward"
  - Exhaustive lists: 7–10 items when 3–4 would suffice
  - Passive voice clusters: 2+ passive sentences in a row
  - Corrective antithesis: "Not X. But Y." setup-payoff constructions
- Meta-Language and Vagueness
  - Meta-verbs: "highlights", "underscores", "emphasizes", "showcases",
    "illustrates"
  - Vague attribution: "some experts say", "widely covered", "significant
    attention"
  - Copy-paste metaphors: same metaphor repeated word-for-word 3+ times

# Core Principles
- Edit, don't rewrite: clean up pattern slop, preserve voice, opinions,
  structure, and meaning
- Apply systematically: check all 19 rules below; skip only if the rule doesn't
  apply to the text
- Use judgment on conflicts: if a rule break serves the writing (e.g., a
  well-placed em dash for effect), keep it
- Change nothing else: don't reorder paragraphs, add ideas, rephrase core
  arguments, or alter facts

# Rules

## Rule 1: Em Dashes
- Remove excessive em dashes (—)
- Rewrite using commas, full stops, or restructure the sentence
- One or two in a long piece is fine; three or more is a pattern worth fixing

## Rule 2: Corrective Antithesis
- Remove "Not X. But Y." constructions where you set up something the reader
  never assumed, then correct it for drama
- Bad: "This isn't because they don't trust the technology. It's because they
  can't predict it."
- Good: "They trust the technology fine. What they can't do is predict it."

## Rule 3: Dramatic Pivot Phrases
- Remove theatrical pivots: "But here's the thing", "Here's the catch", "Here's
  the bind", "Here's what most people miss"
- Fold the point into the sentence naturally
- Bad: "The patterns are valuable. But here's the bind: building a tool cost
  more than most could justify."
- Good: "The patterns are valuable but building a tool to capture them cost more
  than most could justify."

## Rule 4: Soft Hedging Language
- Cut filler hedges; just say the thing
- Remove: "It's worth noting that", "Something we've observed", "This is where X
  really shines", "It's important to remember", "It should be noted",
  "Interestingly enough"
- Bad: "It's worth noting that this approach has shown some promising results in
  certain contexts."
- Good: "This approach works."

## Rule 5: Overused Transition Words
- Cut or vary "Furthermore", "Moreover", "Additionally", "In addition to the
  above" when chained together
- Real writers use them sparingly
- Bad: "The system is fast. Furthermore, it is reliable. Moreover, it is easy to
  use. Additionally, it integrates well."
- Good: "The system is fast, reliable, easy to use, and integrates without
  friction."

## Rule 6: AI Vocabulary
- Replace words AI overuses with plain alternatives
  - "delve" -> explore, look at, examine
  - "leverage" (verb) -> use, apply, rely on
  - "robust" -> strong, solid, reliable
  - "comprehensive" -> thorough, complete, full
  - "nuanced" -> subtle, layered, specific
  - "multifaceted" -> complex, varied
  - "transformative" -> significant, major
  - "unpack" -> explain, break down
  - "reimagine" -> rethink, redesign
  - "empower" -> let, help, enable

## Rule 7: Meta-Verbs
- Don't say something "highlights", "underscores", "emphasizes", "showcases", or
  "illustrates" a point
- Explain what it actually shows
- Bad: "This underscores the importance of clear communication."
- Good: "Clear communication matters here."

## Rule 8: Passive Voice Clusters
- Flag sequences of two or more passive constructions in a row
- Rewrite at least one in active voice to restore momentum
- Bad: "The report was reviewed by the team. Errors were identified. Changes
  were recommended."
- Good: "The team reviewed the report, found errors, and recommended changes."

## Rule 9: Rhetorical Section Openers
- Cut rhetorical questions used as transitions ("So what does this mean for
  you?", "Why does this matter?")
- State the answer directly or remove entirely
- Bad: "So what does this mean for your team? It means you need to rethink your
  process."
- Good: "Your team needs to rethink its process."

## Rule 10: Staccato Rhythm
- Break up runs of short, punchy sentences that stack without variation
- Combine some; lengthen others
- Let rhythm follow the thinking, not a drumbeat
- Bad: "Now, agents act. They send emails. They modify code. They book
  appointments."
- Good: "Agents are starting to do real things now. They'll send an email on
  your behalf or update a database, sometimes without you even realizing it
  happened."

## Rule 11: Cookie-Cutter Paragraphs
- Vary paragraph length
- If every paragraph is 3–4 sentences, break some into one-liners and let others
  stretch
- The shape on the page should look uneven, like real thinking

## Rule 12: Gift-Wrapped Endings
- Remove summary conclusions that restate the article's points
- Cut: "In summary", "In conclusion", "Ultimately", "Moving forward", "At the
  end of the day"
- End with something specific, human, or unresolved
- Bad: "In summary, by focusing on clear communication, consistent feedback, and
  mutual trust, teams can build stronger relationships."
- Good: "The best teams I've worked with never talked about trust. They just had
  it."

## Rule 13: Throat-Clearing Intros
- Remove: "Let's explore", "Let's unpack", "Let's dive in", "Let's break it
  down", "In this article, we'll"
- Just start; the best first sentence puts the reader in the middle of something
- Bad: "In this article, we'll explore the hidden costs of micromanagement.
  Let's dive in."
- Good: "I micromanaged someone last Tuesday."

## Rule 14: Exhaustive Lists
- Trim bullet lists that run to 7–10 items when 3–4 would cover the essential
  points
- Long lists signal AI comprehensiveness, not human judgment
- Cut the weakest items

## Rule 15: Perfect Punctuation
- Don't correct every grammar "mistake" if it sounds more natural broken
  - Fragments are fine
  - Starting with "And" or "But" is fine
  - A comma splice can stay if it reads well
- If the draft has personality in its punctuation, keep it

## Rule 16: Copy-Paste Metaphors
- If the same metaphor or phrase appears more than twice, vary the language
- Use a pronoun, rephrase it, or trust the reader to remember
- Never repeat a metaphor word-for-word three times
- Bad: "Trust is like a battery. When the trust battery is full... But when the
  trust battery runs low... To recharge the trust battery..."
- Good: "Trust is like a battery. When it's full, you barely think about it. But
  let it drain and suddenly every interaction needs a charger."

## Rule 17: Overexplaining the Obvious
- Cut sentences that explain things the reader already understands
- If you've made a clear point, don't re-explain how it works
- Bad: "Trust is earned over time. You give people small tasks, observe how they
  handle them, then gradually expand their responsibilities."
- Good: "Trust is earned. Everyone knows this. The question is whether you're
  actually giving people the chance to earn it."

## Rule 18: Generic Examples
- Flag examples that could apply to any company or product
- If an example doesn't contain a specific, surprising, or insider detail, it's
  filler
- Either sharpen it or cut it
- Bad: "Take Slack, for example. By focusing on seamless team communication,
  they transformed how modern workplaces collaborate."
- Good: "Slack solved the wrong problem brilliantly. Nobody needed another
  messaging app, but everyone needed a place to dump links and pretend they'd
  read them later."

## Rule 19: Vague Attribution
- Avoid vague references like "some experts say", "widely covered", "significant
  attention"
- Identify the actual critic, report, study, or author when possible
- If you can't name the source, cut the claim
