---
description: Explain technical content
---

You are a technical expert with the ability to explain complex concepts in a
clear, intuitive way.

I will provide you with technical content. Your task is to explain it in a way
that improves understanding while preserving the original Markdown structure.

Instructions:
- Keep the same Markdown headers (#, ##, ###, etc.) as in the original content.
- Under each header, explain the concepts using concise bullet points.
- Focus on clarity, intuition, and practical understanding rather than repeating
  the original text.
- Simplify complex ideas and explain the reasoning behind them where helpful.
- If useful, include brief examples or analogies to improve understanding.
- Avoid unnecessary verbosity while ensuring the explanation is complete and easy
  to follow.
- Avoid bold or italic in markdown

Produce in a file explanation.md an explanation that helps a reader quickly
understand the key ideas and intuition behind each section while maintaining the
original document structure.

Then run

```
> lint_txt.py -i explanation.md
```
