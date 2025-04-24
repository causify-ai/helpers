# Code Review Tools

<!-- toc -->

- [Review Systems](#review-systems)
  * [Github Copilot Code Review](#github-copilot-code-review)
  * [Graphite.dev](#graphitedev)
  * [CodeRabbit](#coderabbit)
  * [Deepcode (now integrated with Snyk Code)](#deepcode-now-integrated-with-snyk-code)
- [Prices](#prices)
  * [Github Copilot Code Review](#github-copilot-code-review-1)
  * [Grapite.dev](#grapitedev)
  * [CodeRabbit](#coderabbit-1)
- [Takeaways](#takeaways)
  * [Core Needs](#core-needs)
  * [Strengths and Weaknesses](#strengths-and-weaknesses)
    + [Github Copilot](#github-copilot)
    + [Graphite.dev](#graphitedev-1)
    + [CodeRabbit](#coderabbit-2)
- [References](#references)

<!-- tocstop -->

## Review Systems

### Github Copilot Code Review

- Link:
  [https://docs.github.com/en/copilot/using-github-copilot/code-review/using-copilot-code-review](https://docs.github.com/en/copilot/using-github-copilot/code-review/using-copilot-code-review)

- Key Features:
  - AI-generated review comments
  - Suggestions for bug fixes and style improvements
  - Context-aware feedback

- Usage / Integration
  - Seamless integration within GitHub
  - Works directly on PRs in the GitHub ecosystem

- Ease of Use
  - Very easy for teams already on GitHub
  - Minimal setup required

### Graphite.dev

- Link:
  [https://graphite.dev/docs/code-review](https://graphite.dev/docs/code-review)

- Key Features:
  - Automated code review assistance
  - Consistency and style checking
  - Customizable rule sets

- Usage / Integration
  - Integrates into CI/CD pipelines and possibly GitHub workflows
  - Can be configured for team needs

- Ease of Use
  - User-friendly dashboard
  - Requires initial configuration to align with project-specific rules

### CodeRabbit

- Link: [https://docs.coderabbit.ai/](https://docs.coderabbit.ai/)

- Key Features:
  - Advanced AI-driven code review
  - Highly context-aware suggestions
  - Focus on catching subtle issues and recommending optimizations

- Usage / Integration
  - Early stage integrations with popular platforms (GitHub, Bitbucket, etc.)
  - Designed for modern development workflows

- Ease of Use
  - Modern UI and workflow
  - May involve a learning curve as the product matures

### Deepcode (now integrated with Snyk Code)

- Link [https://docs.snyk.io/](https://docs.snyk.io/)

- Key Features:
  - AI-powered static analysis
  - Detects bugs, security issues, and anti-patterns
  - Machine learning-based code analysis

- Usage / Integration
  - Integrates with GitHub and other SCM platforms via Snyk Code
  - Often used as part of a broader security/quality toolchain

- Ease of Use
  - Integration may require initial setup within Snyk ecosystem
  - Familiarity with Snyk platforms can help

## Prices

### Github Copilot Code Review

- Link:
  [https://docs.github.com/en/copilot/about-github-copilot/plans-for-github-copilot](https://docs.github.com/en/copilot/about-github-copilot/plans-for-github-copilot)

- Cost per User:
  - Pro: $10/month
  - Pro+: $39/month
  - Business: $19/month
  - Enterprise: $39/month

- Cost for 10 Users:
  - Pro: $100/month
  - Pro+: $390/month
  - Business: $190/month
  - Enterprise: $390/month

- Cost for 20 Users:
  - Pro: $200/month
  - Pro+: $780/month
  - Business: $380/month
  - Enterprise: $780/month

### Grapite.dev

- Link:
  [https://graphite.dev/docs/graphite-standard](https://graphite.dev/docs/graphite-standard)

- Cost per User:
  - Annual Subscription: $25/month
  - Monthly Subscription: $29/month

- Cost for 10 Users (Annual):
  - Base (3 seats): $900/year
  - Additional 7 seats: $2,100/year
  - Total: $3,000/year (~$250/month)

- Cost for 20 Users (Annual):
  - Base (3 seats): $900/year
  - Additional 17 seats: $5,100/year
  - Total: $6,000/year (~$500/month)

- Note: Graphite is free for personal repositories, teams with 10 or fewer
  GitHub collaborators, open-source projects, and students/educators.

### CodeRabbit

- Link: [https://www.coderabbit.ai/pricing](https://www.coderabbit.ai/pricing)

- Cost per User:
  - Lite: $12/month (billed annually) or $15/month
  - Pro: $24/month (billed annually) or $30/month

- Cost for 10 Users:
  - Lite (Annual): $1,440/year (~$120/month)
  - Pro (Annual): $2,880/year (~$240/month)

- Cost for 20 Users:
  - Lite (Annual): $2,880/year (~$240/month)
  - Pro (Annual): $5,760/year (~$480/month)

- Note: CodeRabbit is free for open-source projects and offers a 14-day free
  trial.

## Takeaways

### Core Needs

1.  Automated Code Review vs. Code Generation
    - **GitHub Copilot** is primarily an AI-assisted code generation tool
      (though it also has a "Code Review" beta). Its strength lies in offering
      real-time suggestions as you code.
    - **Graphite** is focused on PR workflow optimization and automated checks,
      helping streamline how pull requests are created, reviewed, and merged.
    - **Coderabbit** is geared toward AI-based code review and analysis, aiming
      to provide feedback on potential bugs, performance issues, and style
      concerns.

2.  Integration with GitHub
    - **Copilot** integrates directly within GitHub (especially if you're using
      GitHub for everything).
    - **Graphite** integrates well with GitHub but provides its own dashboard
      and workflow enhancements. **Coderabbit** is newer but also targets GitHub
      integration. You'll want to verify how mature their integration is and
      whether it fits your team's workflows.

3.  Budget & Licensing
    - **GitHub Copilot** is priced per user per month. For 30–40 developers, the
      cost scales linearly.
    - **Graphite** and **Coderabbit** typically use a per-seat or tiered pricing
      model as well.
    - If you already have a GitHub Enterprise or Team plan, adding Copilot can
      be straightforward. Graphite and Coderabbit would be additional monthly
      expenses.

### Strengths and Weaknesses

#### Github Copilot

- Strengths
  - Seamless integration if your team is already deeply invested in GitHub.
  - Great for boosting productivity during coding (boilerplate, tests,
    refactors).
  - Provides a familiar in-IDE experience.

- Weaknesses
  - The "Copilot for Code Review" feature is relatively new and may not offer
    deep analysis compared to specialized tools.
  - Can produce "best guess" suggestions that require human oversight.

#### Graphite.dev

- Strengths
  - Focuses on improving the pull request workflow, making it faster and more
    organized.
  - Catches common style or lint issues early, reducing manual review overhead.
  - Ideal for teams seeking to structure their PR process rigorously (e.g.,
    stacked diffs, streamlined merges).

- Weaknesses
  - Not as advanced in AI-based code analysis as some specialized code-review
    tools.
  - May require your team to adapt to a new PR workflow or dashboard.

#### CodeRabbit

- Strengths
  - Billed as an AI-driven code review tool, aiming for deeper analysis of
    logic, bugs, and potential improvements.
  - If effective, it could reduce the time spent on finding edge cases or hidden
    issues.

- Weaknesses
  - A relatively new entrant; maturity and coverage (languages, frameworks) need
    to be confirmed.
  - Integration details might not be as polished or comprehensive yet.

## References

- [https://www.awesomecodereviews.com/tools/ai-code-review-tools](https://www.awesomecodereviews.com/tools/ai-code-review-tools)

- [https://bito.ai/blog/best-automated-ai-code-review-tools/](https://bito.ai/blog/best-automated-ai-code-review-tools/)

- [https://www.codacy.com/](https://www.codacy.com/)

- [https://www.sonarsource.com/](https://www.sonarsource.com/)

- [https://usetrag.com/](https://usetrag.com/)

- [https://medium.com/@anyu6686/use-llm-for-code-review-70385c3f7457](https://medium.com/@anyu6686/use-llm-for-code-review-70385c3f7457)
