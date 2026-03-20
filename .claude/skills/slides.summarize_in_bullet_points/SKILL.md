---
description: Summarize the text into markdown bullet points
---

Convert the following textbook passage into structured markdown bullet points following these rules:

- Use a * for top-level topic headers (e.g., * Chains)
- Use - for first-level bullets and indented - for sub-bullets
- Replace mathematical relationships with LaTeX notation inline
- Extract concrete examples
- Be concise: remove narrative prose, keep only key facts and relationships
- Organize sub-bullets hierarchically: general rule first, then example, then
  mathematical formulation

## Example 1
<input1>
Chains
First, look at this very simple graph. It’s called a chain. Here T causes M, which causes
Y. You can sometimes refer to the intermediary node as a mediator, because it medi‐
ates the relationship between T and Y:
In this first graph, although causation only flows in the direction of the arrows, asso‐
ciation flows both ways. To give a more concrete example, let’s say that knowing
about causal inference improves your problem-solving skills, and problem solving
increases your chances of getting a promotion. So causal knowledge causes your
problem-solving skills to increase, which in turn causes you to get a job promotion.
You can say here that job promotion is dependent on causal knowledge. The greater
the causal expertise, the greater your chances of getting a promotion. Also, the greater
your chances of promotion, the greater your chance of having causal knowledge.
Otherwise, it would be difficult to get a promotion. In other words, job promotion is
associated with causal inference expertise the same way that causal inference expertise
is associated with job promotion, even though only one of the directions is causal.
When two variables are associated with each other, you can say they are dependent or
not independent:
T ⊥̸ Y
Now, let’s hold the intermediary variable fixed. You could do that by looking only at
people with the same M, or problem-solving skills in our example. Formally, you can
say you are conditioning on M. In this case, the dependence is blocked. So, T and Y
are independent given M. You can write this mathematically as:
T ⊥Y M
To indicate that we are conditioning on a node, I’ll shade it:
Crash Course in Graphical Models
|
67

![Figure 53](facure.figs/figure_053.png)

![Figure 54](facure.figs/figure_054.png)

To see what this means in our example, think about conditioning on people’s
problem-solving skills. If you look at a bunch of people with the same problem-
solving skills, knowing which ones are good at causal inference doesn’t give any fur‐
ther information about their chances of getting a job promotion. In mathematical
terms:
E Promotion Solve problems, Causal knowledge = E Promotion Solve problems
The inverse is also true; once I know how good you are at solving problems, knowing
about your job promotion status gives me no further information about how likely
you are to know causal inference.
As a general rule, if you have a chain like in the preceding graph, association flowing
in the path from T to Y is blocked when you condition on an intermediary variable
M. Or:
T ⊥̸ Y
but
T ⊥Y M
Forks
Moving on, let’s consider a fork structure. In this structure, you have a common
cause: the same variable causes two other variables down the graph. In forks, associa‐
tion flows backward through the arrows:
For example, let’s say your knowledge of statistics causes you to know more about
causal inference and about machine learning. However, knowing causal inference
doesn’t help you with machine learning and vice versa, so there is no edge between
those variables.
This graph is telling you that if you don’t know someone’s level of statistical knowl‐
edge, then knowing that they are good at causal inference makes it more likely that
they are also good at machine learning, even if causal inference doesn’t help you with
machine learning. That is because even if you don’t know someone’s level of statistical
</input1>

<output1>
* Chains
- In case of $T \to M \to Y$:
  - $M$ is "mediator" since it mediates the relationship between $T$ and $Y$
  - Causation flows only in the direction of the arrows
  - Association flows both ways

- E.g., $Study \to SolveProblems \to JobPromotion$
  - Job promotion is causally dependent on studying
  - The association goes both ways
    - The more you study, the more likely to get a promotion
    - The greater the chances of promotion, the greater your chance of having
      studied (otherwise it would be difficult to get a promotion)
  - So $Study$ and $JobPromotion$ are
    - Dependent or
    - Not independent $Study \cancel \perp JobPromotion$

- If you hold the intermediary variable fixed (i.e., conditioning on $M$, looking
  for only people with the same skills at problem solving), the dependency is
  blocked
  - $T$ and $Y$ are independent given $M$, i.e., $(T \perp Y) | M$
  - $\EE[Y | T, M] = \EE[Y | M]$ and also the inverse $\EE[T | Y, M] = \EE[T | M]$
</output1>
