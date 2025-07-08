<documentation>
  <title>Reference Guide: script.py</title>

  <!-- Briefly describe the purpose and function of the script. Do not include this comment in the final output. -->
  <description>
    TODO: Write a short paragraph describing what the script does and its key use cases.
  </description>

  <section name="WhatItDoes">
    <!-- State what this script is designed to do in bullet form. Do not include this comment in the final output. -->
    <objective>
      <bullet>TODO: Explain core objective #1</bullet>
      <bullet>TODO: Explain core objective #2</bullet>
      <bullet>TODO: Explain core objective #3</bullet>
    </objective>

    <sample_behavior>
      <!-- Example use case, LLM should fill with actual logic of the script. Do not include this comment in the final output. -->
      This script performs the following tasks:
      <bullet>Detects fenced code blocks (e.g., PlantUML, Mermaid, TikZ)</bullet>
      <bullet>Renders them using the appropriate tool</bullet>
      <bullet>Comments out original block</bullet>
      <bullet>Inserts an image reference like ![](image.png)</bullet>
    </sample_behavior>
  </section>

  <section name="InputOutput">
    <!-- Describe input/output file types and structure. Do not include this comment in the final output. -->
    <inputs>
      TODO: List accepted input formats (e.g., .md, .tex)
    </inputs>
    <outputs>
      TODO: Describe the output format and content (e.g., modified Markdown file with embedded images)
    </outputs>
  </section>

  <section name="SupportedFileTypes">
    <!-- Provide file extensions or types and how each is processed -->
    <filetype name=".md">TODO: Describe how .md files are handled</filetype>
    <filetype name=".tex">TODO: Describe how .tex files are handled</filetype>

    <use_cases>
      <case description="Render Markdown to new file">
        <command>render_images.py -i ABC.md -o XYZ.md --action render --run_dockerized</command>
      </case>
      <case description="Render in-place Markdown">
        <command>render_images.py -i ABC.md --action render --run_dockerized</command>
      </case>
      <case description="Preview rendered images in browser">
        <command>render_images.py -i ABC.md --action open --run_dockerized</command>
      </case>
    </use_cases>
  </section>

  <section name="FlagOptions">
    <!-- Describe CLI flags, one per tag. Do not include this comment in the final output. -->
    <flag name="-h, --help">Show help message and exit</flag>
    <flag name="-i, --in_file_name">Input file path</flag>
    <flag name="-o, --out_file_name">Output file path</flag>
    <flag name="--action {open,render}">Action to execute</flag>
    <flag name="--skip_action {open,render}">Action to skip</flag>
    <flag name="--all">Run all available actions</flag>
    <flag name="--dry_run">Simulate run (update files but don’t render images)</flag>
    <flag name="--dockerized_force_rebuild">Force Docker container rebuild</flag>
    <flag name="--dockerized_use_sudo">Use sudo inside Docker container</flag>
    <flag name="-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}">Set logging level</flag>
  </section>

  <section name="Examples">
    <!-- Provide clear examples of how to run the script. Do not include this comment in the final output. -->
    <example title="Render to a new Markdown file">
      <command>render_images.py -i lesson.md -o lesson.rendered.md --action render --run_dockerized</command>
    </example>
    <example title="Render in-place">
      <command>render_images.py -i lesson.md --action render --run_dockerized</command>
    </example>
    <example title="HTML preview of rendered images">
      <command>render_images.py -i lesson.md --action open --run_dockerized</command>
    </example>
    <example title="Dry-run for testing only">
      <command>render_images.py -i lesson.md -o /tmp/out.md --dry_run</command>
    </example>
  </section>

  <section name="ErrorsAndFixes">
    <!-- For each error, provide likely cause and fix.Do not include this comment in the final output. -->
    <error>
      <issue>TODO: Describe a common error</issue>
      <cause>TODO: Likely cause of this error</cause>
      <solution>TODO: Suggested fix or workaround</solution>
    </error>
  </section>

  <section name="Dependencies">
    <!-- List libraries or system dependencies. Do not include this comment in the final output. -->
    <dependency>TODO: Python 3.8+</dependency>
    <dependency>TODO: Docker (if using --run_dockerized)</dependency>
    <dependency>TODO: External rendering tools (e.g., Graphviz)</dependency>
  </section>
</documentation>
