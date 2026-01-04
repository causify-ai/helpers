#!/usr/bin/env python

"""Compare batch vs non-batch processing costs."""

import subprocess
import json
import re

# Long system prompt
SYSTEM_PROMPT = """You are an expert computer science educator with 20 years of teaching experience at top universities. Your specialty is explaining complex technical concepts in a clear, accessible way that beginners can understand while remaining technically accurate. When answering questions, provide concise explanations that focus on the core concept, use simple analogies where appropriate, and avoid unnecessary jargon unless it's essential to the explanation. Keep your answers to 2-3 sentences maximum for clarity and brevity."""

# Sample prompts to test
PROMPTS = [
    "Explain recursion in programming",
    "What are the benefits of functional programming",
    "How does garbage collection work",
]

def run_individual_queries():
    """Run queries individually and calculate total cost."""
    print("=" * 80)
    print("RUNNING INDIVIDUAL QUERIES (NON-BATCH)")
    print("=" * 80)
    total_cost = 0.0

    for i, prompt in enumerate(PROMPTS, 1):
        print(f"\nQuery {i}/{len(PROMPTS)}: {prompt}")
        cmd = [
            "./helpers_root/dev_scripts_helpers/compute_llm_query_cost.py",
            "--prompt", prompt,
            "--system_prompt", SYSTEM_PROMPT,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Extract cost from output
        match = re.search(r"Total cost: \$(\d+\.\d+)", result.stdout)
        if match:
            cost = float(match.group(1))
            total_cost += cost
            print(f"  Cost: ${cost:.6f}")

    print(f"\n{'=' * 80}")
    print(f"TOTAL COST (INDIVIDUAL): ${total_cost:.6f}")
    print(f"{'=' * 80}\n")
    return total_cost

def run_batch_query():
    """Run batch query and extract cost."""
    print("=" * 80)
    print("RUNNING BATCH PROCESSING")
    print("=" * 80)

    # Create temp file with prompts
    with open("tmp.batch_test.txt", "w") as f:
        f.write("\n".join(PROMPTS))

    cmd = [
        "./helpers_root/dev_scripts_helpers/compute_llm_query_cost.py",
        "--prompts_file", "tmp.batch_test.txt",
        "--system_prompt", SYSTEM_PROMPT,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Extract costs from output
    total_match = re.search(r"Total cost: \$(\d+\.\d+)", result.stdout)
    savings_match = re.search(r"Savings: \$(\d+\.\d+) \((\d+\.\d+)%\)", result.stdout)

    if total_match:
        batch_cost = float(total_match.group(1))
        print(f"\nTOTAL COST (BATCH): ${batch_cost:.6f}")

        if savings_match:
            savings = float(savings_match.group(1))
            savings_pct = float(savings_match.group(2))
            print(f"SAVINGS: ${savings:.6f} ({savings_pct:.2f}%)")

        print(f"{'=' * 80}\n")
        return batch_cost

    return 0.0

if __name__ == "__main__":
    print("\nCOST COMPARISON: BATCH vs NON-BATCH PROCESSING\n")

    # Run individual queries
    individual_cost = run_individual_queries()

    # Run batch query
    batch_cost = run_batch_query()

    # Calculate and display comparison
    print("=" * 80)
    print("FINAL COMPARISON")
    print("=" * 80)
    print(f"Individual queries total: ${individual_cost:.6f}")
    print(f"Batch processing total:   ${batch_cost:.6f}")
    print(f"Savings:                  ${individual_cost - batch_cost:.6f}")
    print(f"Savings percentage:       {((individual_cost - batch_cost) / individual_cost * 100):.2f}%")
    print("=" * 80)
