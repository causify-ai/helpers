<!-- toc -->

- [How to Publish Causify Blogs](#how-to-publish-causify-blogs)
  * [Overview](#overview)
  * [How to Publish a Blog](#how-to-publish-a-blog)
  * [How to Preview Locally](#how-to-preview-locally)
    + [Prerequisites](#prerequisites)
    + [Steps to Preview](#steps-to-preview)
  * [Changes in Website Structure](#changes-in-website-structure)
    + [Adding or Editing Categories](#adding-or-editing-categories)
    + [Adding or Editing Authors](#adding-or-editing-authors)
  * [Blog Post Structure and Conventions](#blog-post-structure-and-conventions)
    + [Required Frontmatter](#required-frontmatter)
    + [Blog Post Template](#blog-post-template)
    + [Naming Convention](#naming-convention)
    + [Using the Excerpt Separator](#using-the-excerpt-separator)
  * [Working with Assets and Images](#working-with-assets-and-images)
    + [Image Location](#image-location)
    + [Using Diagrams (Graphviz, Mermaid, Plantuml)](#using-diagrams-graphviz-mermaid-plantuml)
  * [Available Categories](#available-categories)
  * [Publishing Workflow Details](#publishing-workflow-details)
    + [Automatic Deployment](#automatic-deployment)
    + [What Gets Published](#what-gets-published)
    + [Preprocessing Step](#preprocessing-step)
  * [Examples and References](#examples-and-references)

<!-- tocstop -->

# How to Publish Causify Blogs

## Overview

The Causify blog is hosted at
[https://blog.causify.ai/](https://blog.causify.ai/) and is built using MkDocs
Material with the blog plugin. All blog content is managed through the csfy
repository, and changes are automatically deployed via GitHub Actions.

The blog uses a **preprocessing step** that:

- Validates required frontmatter fields (title, authors, date, description,
  categories)
- Renders diagrams (Graphviz, Mermaid, PlantUML) to PNG images
- Copies all necessary files including hidden files like `.authors.yml` to `tmp`
  dir (needed while deploying)

## How to Publish a Blog

Publishing a blog post is straightforward:

1. **Create your blog post** as a Markdown file following the conventions below
2. **Add the file** to `//csfy/blog/docs/posts/` directory
3. **Commit and merge** your changes to the `master` branch

That's it! The
[publish_blog.yml](https://github.com/causify-ai/csfy/blob/master/.github/workflows/publish_blog.yml)
GitHub Action will automatically:

- Detect changes in the `blog/**` directory
- Run preprocessing to validate frontmatter and render diagrams
- Build the MkDocs site
- Deploy it to S3 at `s3://causify-blog`
- Your blog will be live at [https://blog.causify.ai/](https://blog.causify.ai/)

**Note:** The GitHub Action publishes ANY changes made in the `//csfy/blog/`
directory, including:

- New blog posts
- Updates to existing posts
- Changes to styling (`styles/`)
- New or updated assets/images
- Configuration changes (`mkdocs.yml`)
- Author information (`.authors.yml`)

## How to Preview Locally

Before publishing, you should preview your blog post locally to ensure it
renders correctly.

### Prerequisites

Activate the MkDocs virtual environment before serving/ building:

```bash
source "$HOME/src/venv/mkdocs/bin/activate"
```

This environment already has all the necessary dependencies (`mkdocs`,
`mkdocs-material`, etc.) installed.

### Steps to Preview

1. **Navigate to the repository root:**

```bash
   cd ~/src/csfy1
```

2. **Run the preprocessing script:**

```bash
   python helpers_root/docs/mkdocs/preprocess_mkdocs.py \
     --blog \
     --input_dir blog \
     --output_dir tmp.mkblogs \
     --render_images \
     --force_rebuild \
     -v INFO
```

**What this does:**

- Validates frontmatter in all blog posts
- Renders Graphviz/Mermaid/PlantUML diagrams to PNG images
- Copies all files from `blog/` to `tmp.mkblogs/`
- Includes hidden files like `.authors.yml`
- Moves generated images to correct location

**Flags:**

- `--blog`: Process as blog (enables frontmatter validation)
- `--render_images`: Render diagrams to images
- `--force_rebuild`: Ignore cache and regenerate all images
- `-v INFO`: Verbose logging

3. **Navigate to the blog directory:**

```bash
   cd blog
```

4. **Activate the mkdocs env**

```bash
  source "$HOME/src/venv/mkdocs/bin/activate"
```

5. **Start the local server:**

```bash
   mkdocs serve
```

**Note:** The `mkdocs.yml` is configured with `docs_dir: tmp.docs`, so MkDocs
will serve from the preprocessed content. One might need to `unset PYTHONPATH`
if encountering env errors.

6. **Open the local site:**
   - The terminal will display the local URL (typically `http://127.0.0.1:8000`)
   - Open this URL in your browser to preview your blog

7. **Make changes:**
   - Edit files in `blog/docs/posts/`
   - Re-run the preprocessing script (step 2) to see changes
   - The mkdocs server will auto-reload after preprocessing

8. **Stop the server:**
   - Press `Ctrl+C` in the terminal when done

## Changes in Website Structure

### Adding or Editing Categories

Categories are defined in the `mkdocs.yml` configuration file. To add or modify
categories:

1. **Edit the configuration:**

```bash
   vim blog/mkdocs.yml
```

2. **Locate the `categories_allowed` section:**

```yaml
plugins:
  - blog:
      categories_allowed:
        - "Causal News"
        - "Causal ELI5"
        - Business
        - DevOps
        - Startup
```

3. **Add or modify categories:**
   - Add new categories to this list
   - Remove categories that are no longer needed
   - Categories with spaces must be quoted (e.g., `"Causal News"`)

4. **Note on case sensitivity:**
   - The blog plugin is configured with `case: preserve`
   - Category names are case-sensitive
   - Use consistent capitalization across all blog posts

### Adding or Editing Authors

Author information is centrally managed in a YAML file:

1. **Edit the authors file:**

```bash
   vim blog/docs/.authors.yml
```

2. **Add a new author:**

```yaml
author_id:
  name: Full Name
  description: Author bio or role
  avatar: https://github.com/username.png # Or path to local image.
```

3. **Example author entry:**

```yaml
gpsaggese:
  name: GP Saggese
  description: CEO & Co-founder at Causify
  avatar: https://github.com/gpsaggese.png
```

4. **Using the author in blog posts:**
   - Reference the author by their `author_id` in the blog post frontmatter
   - Multiple authors can be listed for a single post

## Blog Post Structure and Conventions

### Required Frontmatter

Every blog post must include YAML frontmatter at the beginning of the file. Here
are the required fields:

```yaml
title: Your Blog Post Title
authors:
  - author_id_1
  - author_id_2 # Optional: multiple authors.
date: YYYY-MM-DD
description: Brief description of the blog post
categories:
  - Category1
  - Category2 # Optional: multiple categories.
```

**Field descriptions:**

- **`title`**: The main title of your blog post (required)
- **`authors`**: List of author IDs from `.authors.yml` (required)
- **`date`**: Publication date in YYYY-MM-DD format (required)
- **`description`**: Short summary that appears in previews (required)
- **`categories`**: List of categories from the allowed categories (required)

**Important:** The preprocessing script will **validate** these fields and
**fail** if any are missing. This ensures all blog posts have complete metadata
before publishing.

### Blog Post Template

Here's a complete template for a new blog post:

```markdown
title: Your Compelling Blog Title authors:

- your_author_id date: 2025-01-15 description: A brief, engaging description
  that will appear in blog previews and search results categories:
- Business
- Startup

Your opening paragraph goes here. This should hook the reader and provide
context for what they're about to read.

This introduction text will appear in blog list previews.

<!-- more -->

## Main Content Starts Here

After the `<!-- more -->` separator, you can include the full content of your
blog post.

## Conclusion
```

### Naming Convention

Blog post files should follow this naming convention:

**Format:** `Title_of_the_Blog.md`

**Examples:**

- `AI_for_Optimal_Decision-Making.md`
- `Understanding_Causal_Inference.md`
- `A_Causal_Analysis_of_Vaccine_Kills_Claim.md`

**Guidelines:**

- Use title case for the filename
- Use underscores instead of spaces for better compatibility
- Keep names descriptive but concise
- The `.md` extension is required

### Using the Excerpt Separator

The `<!-- more -->` separator is crucial for blog post previews:

**Purpose:**

- Content **before** `<!-- more -->` appears in the blog list/index page
- Content **after** `<!-- more -->` only appears when clicking into the full
  post
- This creates a clean preview without showing the entire post

**Best practices:**

- Place `<!-- more -->` after 1-2 introductory paragraphs
- Ensure the preview content is compelling enough to make readers want to click
- Don't place it too early (at least one paragraph) or too late (not more than
  3-4 paragraphs)

## Working with Assets and Images

### Image Location

All blog images and assets should be stored in:

```text
//csfy/blog/docs/assets/
```

**Directory structure:**

```text
blog/
├── docs/
│   ├── assets/
│   │   ├── logo.png
│   │   ├── favicon.ico
│   │   ├── ETA_analogy.png
│   │   └── your_image.png
│   └── posts/
│       └── Your_Blog_Post.md
└── mkdocs.yml
```

**Image best practices:**

- Always include descriptive alt text in square brackets
- Use descriptive filenames for images
- Optimize images for web (compress large files)
- Supported formats: PNG, JPG, SVG, GIF
- Use SVG for diagrams and logos when possible

### Using Diagrams (Graphviz, Mermaid, Plantuml)

You can include diagrams directly in your blog posts using code blocks. The
preprocessing script will automatically render them to PNG images.

**Supported diagram types:**

- **Graphviz**: For flowcharts, decision trees, and graph diagrams
- **Mermaid**: For sequence diagrams, flowcharts, and Gantt charts
- **PlantUML**: For UML diagrams

**How it works:**

1. Write your diagram code in a fenced code block with the diagram type
   (graphviz, mermaid, plantuml)
2. The preprocessing script detects these blocks
3. It renders them to PNG images using Docker containers
4. The images are saved to `blog/tmp.docs/posts/figs/`
5. The markdown is updated to reference the generated images

**Important notes:**

- The preprocessing script must be run with `--render_images` flag
- Generated images are automatically named based on the blog post filename
- Images are cached to avoid regenerating unchanged diagrams (use
  `--force_rebuild` to regenerate)

## Available Categories

The blog currently supports the following categories (defined in `mkdocs.yml`):

- **"Causal News"** - News and updates related to causal AI and the field
- **"Causal ELI5"** - Simplified explanations of causal concepts
- **Business** - Business strategy, insights, and case studies
- **DevOps** - Development operations, infrastructure, and tooling
- **Startup** - Startup journey, lessons learned, and entrepreneurship

**Note:** Categories with spaces must be quoted in the frontmatter:

```yaml
categories:
  - "Causal News" # Quoted because it contains a space.
  - Business # No quotes needed for single words.
```

To add new categories, edit the `categories_allowed` list in `blog/mkdocs.yml`.

## Publishing Workflow Details

### Automatic Deployment

The blog uses a GitHub Action
([publish_blog.yml](https://github.com/causify-ai/csfy/blob/master/.github/workflows/publish_blog.yml))
that:

**Triggers on:**

- Push to `master` branch with changes in `blog/**` path
- Manual workflow dispatch

**Steps performed:**

1. Checks out the repository with submodules
2. Configures Git credentials
3. Sets up Python 3.x
4. Installs MkDocs and MkDocs Material
5. Updates PYTHONPATH to include helpers
6. **Runs preprocessing** to validate frontmatter and render diagrams
7. Builds the static site (`mkdocs build` in `./blog` directory)
8. Configures AWS credentials via OIDC
9. Syncs the built site to S3: `s3://causify-blog` with `--delete` flag

**Deployment time:**

- Typically 2-5 minutes from merge to live
- CloudFront caching may add a few additional minutes for global propagation

### What Gets Published

Any changes in the `blog/` directory will trigger a deployment:

- **Blog posts** (`blog/docs/posts/*.md`)
- **Assets** (`blog/docs/assets/*`)
- **Styling** (`blog/styles/*`)
- **Configuration** (`blog/mkdocs.yml`)
- **Author info** (`blog/docs/.authors.yml`)

### Preprocessing Step

The preprocessing step is crucial for blog publishing:

**What it does:**

1. **Validates frontmatter**: Checks that all required fields (title, authors,
   date, description, categories) are present
2. **Renders diagrams**: Converts Graphviz/Mermaid/PlantUML code blocks to PNG
   images
3. **Copies files**: Copies all content from `blog/docs/` to `blog/tmp.docs/`
   (including hidden files)
4. **Moves images**: Ensures generated images are in the correct location
   (`blog/tmp.docs/posts/figs/`)

**Command:**

```bash
python helpers_root/docs/mkdocs/preprocess_mkdocs.py \
  --blog \
  --input_dir blog \
  --output_dir tmp.mkblogs \
  --render_images \
  --force_rebuild \
  -v INFO
```

**If preprocessing fails:**

- The GitHub Action will fail and the blog won't be deployed
- Check the Action logs for validation errors (e.g., missing frontmatter fields)
- Fix the errors in your blog post and push again

**Why `blog/tmp.docs/`?**

- The `mkdocs.yml` configuration has `docs_dir: tmp.docs`
- This tells MkDocs to build from the preprocessed content
- The preprocessed content includes rendered diagrams and validated frontmatter
- The `blog/tmp.docs/` directory is gitignored and regenerated on each build

## Examples and References

**For detailed blog writing conventions:**

- Refer to:
  [`/docs/blogging/all.write_blog.how_to_guide.md`](/docs/blogging/all.write_blog.how_to_guide.md)

**Example blog posts:**

- Browse all published blogs:
  [https://github.com/causify-ai/csfy/tree/master/blog/docs/posts](https://github.com/causify-ai/csfy/tree/master/blog/docs/posts)
- Pick any `.md` file to see real examples of:
  - Frontmatter structure
  - Content organization
  - Image usage
  - Excerpt placement
  - Diagram usage (see `A_Causal_Analysis_of_Vaccine_Kills_Claim.md` for
    Graphviz examples)

**Study these examples to understand:**

- How to structure compelling introductions
- Where to place the `<!-- more -->` separator
- How to organize content with headers
- Effective use of images and formatting
- How to create diagrams with Graphviz, Mermaid, or PlantUML
