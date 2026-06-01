In /Users/saggese/src/umd_classes1/helpers_root/dev_scripts_helpers/scraping/process_link_gsheet.py

Change the topics as below

# Map article topics to high-level cluster categories for grouping and analysis.
topic_to_cluster = {
    "AI Agents & Tool-Using Systems": "AI",
    # -> AI Agents
    "Automated Theorem Proving": "AI",
    "Causal Inference": "AI",
    "Diffusion Models": "AI",
    "Knowledge Graphs": "AI",
    "LLM Reasoning": "AI",
    "Multi-Agent Systems": "AI",
    "Probabilistic Programming": "AI",
    "Prompt Engineering": "AI",
    "Self-Supervised Learning": "AI",
    "Uncertainty & Belief Modeling": "AI",
    # -> Uncertainty Modeling
    #
    "AI Infrastructure": "Data/Infra",
    "Data Engineering & Pipelines": "Data/Infra",
    # -> Data Engineering
    "High-Performance Computing": "Data/Infra",
    # 
    "Developer Tools": "Dev tools",
    "Git and GitHub": "Dev tools",
    # -> Git
    "Open Source": "Dev tools",
    "Python Ecosystem": "Dev tools",
    "Rust and C++": "Dev tools",
    #
    "Quant Finance": "Finance",
    "Trading Strategies": "Finance",
    #
    "Complex Systems & Network Dynamics": "Math",
    # -> Complex Systems
    "Mathematical Concepts": "Math",
    "Simulation & Agent-Based Modeling": "Math",
    # -> Simulation
    "Time Series": "Math",
    "Unconventional Computing": "Math",
    #
    "Careers & Professional Growth": "Business",
    # -> Careers
    "Marketing and Sales": "Business",
    "Organizational Behavior & Incentives": "Business",
    # -> Organizational Behavior
    "Psychology & Well-Being": "Business",
    # -> Psychology
    #
    "Cybersecurity & Privacy": "CyberSec",
    # -> Cybersecurity
    "Risk Management & Compliance": "CyberSec",
    # -> Risk Management
    #
    "Code Refactoring": "SwEng",
    "Dev Productivity": "SwEng",
    "Software Architecture": "SwEng",
    "Software Project Management": "SwEng",
    "System Reliability & Fault Tolerance": "SwEng",
    # -> System Reliability
}


Step 2
Write a script to download the link_gsheet using --action and from_gsheet.py
similar to 
In /Users/saggese/src/umd_classes1/helpers_root/dev_scripts_helpers/scraping/process_link_gsheet.py

--action download_link_gsheet

Create an --action replace

Replace in the Article_tag the old names to the new ones

Upload the 

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
