# Dev Scripts Helpers

Development automation scripts and utilities organized by functionality. Provides tools for Git operations, GitHub workflows, Docker management, testing, documentation generation, and media processing.

## Directory Structure

### Core Development Tools
| Directory         | Purpose                                                                                       |
| ----------------- | --------------------------------------------------------------------------------------------- |
| **git/**          | Git utilities and custom commands (git hooks, submodule management, shrinking repos)          |
| **github/**       | GitHub API interactions and workflow automation                                               |
| **coding_tools/** | Code analysis and development utilities (build call graphs, code statistics, code generation) |
| **lint/**         | Linting and code quality enforcement tools                                                    |
| **testing/**      | Testing framework utilities and test automation                                               |

### Build & Deployment
| Directory      | Purpose                                            |
| -------------- | -------------------------------------------------- |
| **docker/**    | Docker configuration and container management      |
| **dockerize/** | Scripts for Dockerizing applications               |
| **infra/**     | Infrastructure setup and management                |
| **aws/**       | AWS integration and cloud deployment tools         |
| **poetry/**    | Poetry package manager configuration and utilities |

### Content & Documentation
| Directory            | Purpose                                          |
| -------------------- | ------------------------------------------------ |
| **documentation/**   | Documentation generation and processing tools    |
| **notebooks/**       | Jupyter notebook utilities and automation        |
| **academic_papers/** | Academic paper management and download utilities |
| **typst/**           | Typst document processing and template tools     |
| **gdrive/**          | Google Drive integration for content management  |
| **google/**          | Google services utilities (Sheets, Docs, etc.)   |

### Media & Content Generation
| Directory                 | Purpose                                  |
| ------------------------- | ---------------------------------------- |
| **generate_videos/**      | Video generation from slides and content |
| **generate_videos_veo3/** | Video generation using Veo3 AI model     |
| **scraping/**             | Web scraping utilities and tools         |

### System & AI
| Directory           | Purpose                                |
| ------------------- | -------------------------------------- |
| **ai/**             | AI/LLM integration and CLI tools       |
| **llms/**           | LLM utilities and language model tools |
| **system_tools/**   | System-level utilities and helpers     |
| **encrypt_models/** | Model encryption and security tools    |

### Repository Management
| Directory                   | Purpose                                       |
| --------------------------- | --------------------------------------------- |
| **integrate_repos/**        | Scripts for integrating external repositories |
| **release_sorrentum/**      | Release management for Sorrentum projects     |
| **update_devops_packages/** | DevOps package updates and management         |
| **cleanup_scripts/**        | Historical cleanup and migration scripts      |
| **thin_client/**            | Thin client utilities and setup               |

### Maintenance
| Directory        | Purpose                                    |
| ---------------- | ------------------------------------------ |
| **cvxpy_setup/** | CVXPY optimization library setup utilities |
| **misc/**        | Miscellaneous utilities and helpers        |
| **old/**         | Deprecated or archived scripts             |
| **to_clean/**    | Scripts pending cleanup or removal         |
| ****pycache**/** | Python cache (generated)                   |

## Key Files
- **helpers.sh**: Shell helper functions and utilities
- **invoke_completion.sh**: Shell completion for invoke task runner
