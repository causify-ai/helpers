<!-- toc -->

- [llm_transform.py - Architecture & Flow Explanation](#llm_transformpy---architecture--flow-explanation)
  * [High Level Flow](#high-level-flow)
  * [Architecture Diagrams (C4)](#architecture-diagrams-c4)
    + [System Context](#system-context)
    + [Container](#container)
    + [Component](#component)

<!-- tocstop -->

# llm_transform.py - Architecture & Flow Explanation

## High Level Flow

- **Argument parsing** – uses [`/helpers/hparser.py`](/helpers/hparser.py) to
  normalise CLI flags.
- **Input acquisition** – [`/helpers/hio.py`](/helpers/hio.py) resolves `‑i` or
  stdin and reads bytes.
- **Prompt selection** – `llm_prompts.py` maps the `‑p/--prompt-tag` value to a
  concrete system/assistant prompt.
- **LLM invocation** – the request is handed to the generic client in
  [`/helpers/hserver.py`](/helpers/hserver.py) through `llm_prompts.py`.
- **Post‑processing** – raw LLM text may be re‑formatted by
  [`/helpers/hmarkdown.py`](/helpers/hmarkdown.py) (e.g. bold top‑level
  bullets).
- **Output emission** – [`/helpers/hio.py`](/helpers/hio.py) writes to stdout or
  the `‑o` file.
- **Optional Dockerisation** – if `‑‑dockerize` is set, control reroutes via
  `dockerized_llm_transform.py`, which uses
  [`/helpers/hdocker.py`](/helpers/hdocker.py) to spin up a container and
  re‑invoke the script inside it.

## Architecture Diagrams (C4)

### System Context

```mermaid
C4Context
  title LLM Transform – System Context
  Person(dev, "Developer", "Invokes CLI to transform code/text")
  System_Boundary(causify, "Causify CLI Tools") {
    Container(llm_cli, "llm_transform.py", "Python CLI", "Coordinates LLM transformations")
  }
  System_Ext(openai, "LLM Provider", "REST API", "e.g. OpenAI")
  Rel(dev, llm_cli, "Runs", "CLI")
  Rel(llm_cli, openai, "Sends prompt & receives completion", "HTTPS")
```

### Container

```plantuml
@startuml
  title LLM Transform – Containers

  ' Components
  component [LLM API] as openai_api
  note top of openai_api : HTTPS – External large-language-model

  ' Databases
  database "Local FS" as filesystem
  note top of filesystem : Text/Code files\nInput & output artefacts

  ' Containers
  node "llm_transform.py\n(Python – Core orchestration CLI)" as llm_transform
  node "dockerized_llm_transform.py\n(Python – Optional container bootstrapper)" as docker_wrapper

  ' Relationships
  llm_transform --> openai_api    : Calls
  llm_transform --> filesystem     : Reads/Writes
  docker_wrapper --> llm_transform : Executes inside container
@enduml
```

### Component

```plantuml
@startuml
  title llm_transform.py – Internal Components

  ' Components
  component [OpenAI API] as OpenAI_API
  note top of OpenAI_API : REST-based LLM provider.

  ' Containers
  node "llm_transform.py\n(Python CLI)" as llm_transform_container {
    [llm_transform.py] as llm_main
    note left of llm_main: Main entrypoint / Coordinator

    [helpers/hparser.py] as hparser
    note left of hparser: Argument parsing

    [helpers/hio.py] as hio
    note left of hio: File / STDIN I/O

    [llm_prompts.py] as llm_prompts
    note left of llm_prompts: Prompt templates & dispatch

    [helpers/hmarkdown.py] as hmarkdown
    note left of hmarkdown: Markdown post-processing

    [helpers/hgit.py] as hgit
    note left of hgit: Git diff utilities

    [helpers/hdocker.py] as hdocker
    note left of hdocker: Docker helpers
  }

  ' Edge labels
  llm_main --> hparser       : Parses flags → supplies prompt-tag
  llm_main --> hio           : Reads/Writes files or STDIN/STDOUT
  llm_main --> llm_prompts   : Selects prompt template
  llm_prompts --> OpenAI_API : Calls LLM provider
  llm_main --> hmarkdown     : Formats output as Markdown
  llm_main --> hgit          : Optionally computes Git diff
  llm_main --> hdocker       : Spawns container run (when --dockerize)
@enduml
```
