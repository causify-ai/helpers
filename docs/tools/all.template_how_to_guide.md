<!-- toc -->

- [What It Does](#what-it-does)
- [Assumptions / Requirements](#assumptions--requirements)
- [Instructions](#instructions)
  * [Step 1: Fetch Input](#step-1-fetch-input)
  * [Example: Download Markdown input file](#example-download-markdown-input-file)
  * [Step 2: Describe Action](#step-2-describe-action)
  * [Step 3: Review Output](#step-3-review-output)
  * [Preview the output file](#preview-the-output-file)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

<!-- tocstop -->

<!--
LLM Instruction:
- Use this XML template to generate structured documentation.
- Wherever CLI examples are required, insert them inside <code_block language="bash"> ... </code_block>.
- Do not use <command> or inline code for full command-line blocks.
- Replace TODO: with actual content based on the script's usage.
- Remove all LLM instruction tags in the final output.
- The final output should be a Markdown file.
- In the <examples> section, provide real or illustrative examples that match the script's use case.
- Do not modify any of the heading names or structure or the template.
- Information entered should be crisp and concise and accurate based on the script.
- Add appropriate examples based on the script wherever necessary.
-->

<howto_guide>

  <title>How-To Guide: script.py</title>

  <section name="WhatItDoes">

# What It Does

    <bullet>TODO: Explain the purpose of this script or workflow</bullet>
    <bullet>TODO: Describe what outcome or goal this achieves</bullet>

    <example>
      Automatically render images from fenced code blocks in Markdown using a custom Python script.
    </example>

  </section>

  <section name="AssumptionsRequirements">

## Assumptions / Requirements

    <bullet>Docker installed and running</bullet>
    <bullet>Basic command-line familiarity</bullet>
    <bullet>TODO: List any additional dependencies or permissions</bullet>

  </section>

  <section name="Instructions">

## Instructions

    <step name="Step1" title="Fetch Input">

### Step 1: Fetch Input

      <description>TODO: Describe the input file(s) and how to prepare or provide them.</description>

      <code_block language="bash">

### Example: Download Markdown input file

wget [https://example.com/input.md](https://example.com/input.md) -O input.md
</code_block> </step>

    <step name="Step2" title="Describe Action">

### Step 2: Describe Action

      <description>TODO: Describe the main script command to execute the action.</description>

      <code_block language="bash">

python render_images.py -i input.md -o output.md --action render </code_block>
</step>

    <step name="Step3" title="Review Output">

### Step 3: Review Output

      <description>TODO: Explain how to verify the results of the script run.</description>

      <code_block language="bash">

### Preview the output file

cat output.md | less </code_block> </step>

  </section>

  <section name="Examples">

## Examples

    <examples>
      <example title="Basic Render">
        <description>Render all diagrams in a Markdown file to embedded images.</description>
        <code_block language="bash">

python render_images.py -i diagrams.md -o diagrams.output.md --action render
</code_block> </example>

      <example title="Render + Open in Browser">
        <description>Render diagrams and open the rendered file in browser preview.</description>
        <code_block language="bash">

python render_images.py -i diagrams.md --action render --run_dockerized
</code_block> </example>

      <example title="Dry Run for Debugging">
        <description>Check what will be processed without rendering the output.</description>
        <code_block language="bash">

python render_images.py -i diagrams.md -o /tmp/preview.md --dry_run
</code_block> </example> </examples>

  </section>

  <section name="Troubleshooting">

## Troubleshooting

    <issue_block>
      <issue>TODO: Describe a common issue</issue>
      <cause>TODO: Likely cause</cause>
      <solution>TODO: Suggested fix or workaround</solution>
    </issue_block>

    <issue_block>
      <issue>TODO: Another possible issue</issue>
      <cause>TODO: Likely cause</cause>
      <solution>TODO: How to resolve it</solution>
    </issue_block>

  </section>
</howto_guide>
