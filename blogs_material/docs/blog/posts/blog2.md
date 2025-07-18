---
title: Cracking the Long Tail
authors: [gpsaggese]
date: 2025-08-15
description: 
categories:
  - Causal_AI
---

For the past decade, the AI and data science industry has been shaped by the dominant narrative of **big data**. From ad-tech to recommendation systems, the idea has been simple: more data leads to better models, so companies should focus on big data, scaling their infrastructure, deep learning, and tooling. 

But here’s the truth: big data problems are extremely rare. Furthermore, big data problems are "easy" problems, in the sense when data is abundant and clean, most machine learning models perform well. The problem with big data is on the tools and compute.

In the real world outside Google, Facebook, Amazon, Netflix, especially for enterprises operating in industrial, supply chain, or risk-heavy environments — the hardest and most valuable problems don’t come with terabytes of clean, labeled data. They fall into what we call the **“long tail of small data problems”**. We claim that, contrary to common belief, small data problems are more difficult to solve than big data problems.

## The Long Tail Problem

The "small data problems" are problems that:

- Can’t be solved with general-purpose data science tools  
- Were historically too expensive to solve with custom solutions  
- Were the domain of consultants building ad-hoc, one-off scripts, Excel spreadsheets  
- Don't come with clean and abundant amounts of data, rather with low signal-to-noise and tiny datasets

Examples include:

- Forecasting supply chain disruptions due to obscure or localized events  
- Detecting fraud that changes by customer segment and evolves over time  
- Optimizing maintenance for niche industrial machinery with complex failure patterns  
- Predicting rare but catastrophic failures in equipment

Traditional AI platforms don’t touch these — not because they aren’t important, but because they don’t scale with cookie-cutter tools.

At **Causify**, we’ve built a platform that does.

## From Consulting to Scalable AI

Causify’s breakthrough is a system that takes what used to be **custom consulting work** and turns it into **scalable, repeatable AI pipelines**. We achieve this by:

- Focusing on **causal and structural understanding**, not just pattern matching  
- Building **modular pipelines** that adapt quickly to new domains  
- Designing for **small, noisy, and irregular data**, not assuming clean data lakes

This allows us to tackle the long tail of use cases, cost-effectively, and without months and high-costs of customization.

## Why "Small Data" Is the Real Hard Problem

There’s a persistent misconception in the field: that big data is where the complexity lies.

Big Data Problems:

- Represent **less than 1%** of real-world enterprise challenges  
- Are **computationally heavy**, but **algorithmically simple**  
- Can often be solved with off-the-shelf tools if you throw enough data at them

It has been shown several times that in many machine learning tasks, having more data can be more valuable than improving the model architecture or algorithm. Simple models trained on massive datasets often outperform sophisticated models trained on smaller datasets \[1\] \[2\].  
When you have massive data, traditional correlation-based machine learning works, almost regardless of the algorithm.

Small Data Problems

- Are the **default** in most enterprise settings  
- Feature **low signal-to-noise**, limited labels, and high stakes  
- Require **causal reasoning**, domain knowledge, and robust validation

These are the real frontier of ML — and where most tools fail.

Causify specializes in solving **small-data problems with weak signals**, where robust inference matters most.

If your company faces edge-case problems, ones that consultants said were “too custom” or ML vendors said were “out of scope”, that’s our sweet spot.  
**Causify turns long tail problems into scalable AI solutions.** We believe the future of AI isn’t just big models on big data. It’s **smart models on hard problems**.

## References

Halevy, A., Norvig, P., & Pereira, F. (2009). *The unreasonable effectiveness of data*. Google Research. Retrieved from [https://research.google/pubs/archive/35179.pdf](https://research.google/pubs/archive/35179.pdf)

Sutton, R. S. (2019). *The bitter lesson*. Retrieved from https://www.incompleteideas.net/IncIdeas/BitterLesson.html
