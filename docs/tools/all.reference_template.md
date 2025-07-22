<!-- toc -->

- [What It Does](#what-it-does)
  * [Input And Output](#input-and-output)
  * [Supported File Types](#supported-file-types)
  * [Flag Options](#flag-options)
  * [Examples](#examples)
  * [Errors And Fixes](#errors-and-fixes)
  * [Dependencies](#dependencies)

<!-- tocstop -->

<!--
LLM Instruction:
- Use this XML template to generate structured documentation.
- Wherever CLI examples are required, insert them inside <code_block language="bash"> ... </code_block>.
- Do not use <command> or inline code for full command-line blocks.
- Replace TODO: with actual content based on the script's usage.
- Remove all LLM instruction tags in the final output.
- The final output should be a Markdown file.
- Do not modify any of the heading names or structure or the template.
- In the <examples> section, provide real or illustrative examples that match the script’s use case.
- Information entered should be crisp and concise and accurate based on the script.
- Add appropriate examples based on the script wherever necessary.
-->

<reference_guide>

  <title>Reference Guide: &lt;FileName&gt;</title>

  <description>
    TODO: Write a short paragraph describing what the script does and its key use cases.
  </description>

  <section name="WhatItDoes">

# What It Does

    <objective>
      <bullet>TODO: Explain core objective #1</bullet>
      <bullet>TODO: Explain core objective #2</bullet>
      <bullet>TODO: Explain core objective #3</bullet>
    </objective>

    <sample_behavior>
      This script performs the following:
      <bullet>Detects fenced code blocks (e.g., PlantUML, Mermaid, TikZ)</bullet>
      <bullet>Renders them using the appropriate tool</bullet>
      <bullet>Comments out the original code block</bullet>
      <bullet>Inserts an image reference like <code>![](image.png)</code></bullet>
    </sample_behavior>

  </section>

  <section name="InputAndOutput">

## Input And Output

    <inputs>
      TODO: List accepted input formats (e.g., .md, .tex)
    </inputs>
    <outputs>
      TODO: Describe the output file format and its expected content
    </outputs>

  </section>

  <section name="SupportedFileTypes">

## Supported File Types

    <sample_behavior>
    <filetype name=".md">TODO: Markdown processing logic</filetype>
    <filetype name=".tex">TODO: LaTeX file processing logic</filetype>

    <use_cases>
      <case description="Render Markdown to a new file">
        <code_block language="bash">

render_images.py -i ABC.md -o XYZ.md --action render --run_dockerized
</code_block> </case> <case description="Render in-place Markdown"> <code_block
language="bash"> render_images.py -i ABC.md --action render --run_dockerized
</code_block> </case> <case description="Preview rendered images in browser">
<code_block language="bash"> render_images.py -i ABC.md --action open
--run_dockerized </code_block> </case> </use_cases> </sample_behavior>

  </section>

  <section name="FlagOptions">

## Flag Options

    <sample_behavior>
    <code_block language="bash">
    <flag name="-h, --help">Show help message and exit</flag>
    <flag name="-i, --in_file_name">Input file path</flag>
    <flag name="-o, --out_file_name">Output file path</flag>
    <flag name="--action {open,render}">Action to execute</flag>
    <flag name="--skip_action {open,render}">Action to skip</flag>
    <flag name="--all">Run all available actions</flag>
    <flag name="--dry_run">Simulate run (update files but don't render images)</flag>
    <flag name="--dockerized_force_rebuild">Force Docker container rebuild</flag>
    <flag name="--dockerized_use_sudo">Use sudo inside Docker container</flag>
    <flag name="-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}">Set logging level</flag>
    </code_block>
    </sample_behavior>

  </section>

  <section name="Examples">

## Examples

    <example title="Render to a new Markdown file">
      <code_block language="bash">

render_images.py -i lesson.md -o lesson.rendered.md --action render
--run_dockerized </code_block> </example> <example title="Render in-place">
<code_block language="bash"> render_images.py -i lesson.md --action render
--run_dockerized </code_block> </example>
<example title="HTML preview of rendered images"> <code_block language="bash">
render_images.py -i lesson.md --action open --run_dockerized </code_block>
</example> <example title="Dry-run for testing only"> <code_block
language="bash"> render_images.py -i lesson.md -o /tmp/out.md --dry_run
</code_block> </example>

  </section>

  <section name="ErrorsAndFixes">

## Errors And Fixes

    <error>
      <issue>TODO: Describe a common error</issue>
      <cause>TODO: Likely cause</cause>
      <solution>TODO: Suggested fix or workaround</solution>
    </error>

  </section>

  <section name="Dependencies">

## Dependencies

  <dependency>
    <bullet>TODO: Docker (for --run_dockerized support)</bullet>
    <bullet>TODO: Graphviz, PlantUML, or other rendering tools depending on code block types</bullet>
    <bullet>TODO: Any other external CLI utilities used in subprocess calls</bullet>
  </dependency>
</section>

</reference_guide>
