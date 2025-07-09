# Tutorial Guide: script.py

<!-- toc -->

- [Introduction](#introduction)
- [What You'll Build](#what-youll-build)
- [Before You Begin](#before-you-begin)
- [Using the Script](#using-the-script)
- [Output](#output)

<!-- tocstop -->

<!--
LLM Instruction:
- Use this XML template to generate structured documentation.
- Wherever CLI examples are required, insert them inside <code_block language="bash"> ... </code_block>.
- Do not use <command> or inline code for full command-line blocks.
- Replace TODO: with actual content based on the script’s usage.
- Do not any of the LLM instruction tags in the final output.
- Do not include any of the TODO comments in the final output.
-->

<tutorial_guide>
  <title>Tutorial Guide: script.py</title>

  <section name="Introduction">
    
  ## Introduction

    Provide a brief description of the task and what the script does.

    <bullet>TODO: Define the task at a high level</bullet>
    <bullet>TODO: Identify the key motivation or use case</bullet>
  </section>

  <section name="WhatYoullBuild">

  ## What You'll Build

    Describe what the script produces or automates.

    <bullet>A Markdown file with diagram code blocks</bullet>
    <bullet>A script that processes and renders those diagrams</bullet>
    <bullet>A new output file with embedded images</bullet>
  </section>

  <section name="BeforeYouBegin">
  
  ## Before You Begin

    Describe all prerequisites or setup conditions required.

    <bullet>Docker installed and running</bullet>
    <bullet>Linter up and running</bullet>
    <bullet>TODO: Any required environment variables or permissions</bullet>
  </section>

  <section name="UsingTheScript">
  
  ## Using the Script

    Describe how to execute the script with examples.

    <code_block language="bash">
python render_images.py -i input.md -o output.md
    </code_block>

    <bullet>TODO: Explain the different flags</bullet>
    <bullet>TODO: Mention optional flags or parameters</bullet>
  </section>

  <section name="Output">
    
  ## Output

    Explain what output is expected and how to validate it.

    <bullet>TODO: Describe where the output file is saved</bullet>
    <bullet>TODO: Mention format of embedded images or changes in the file</bullet>

    <code_block language="bash">
cat output.md | less
    </code_block>
  </section>
</tutorial_guide>