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
    + [Referencing Images](#referencing-images)
  * [Available Categories](#available-categories)
  * [Publishing Workflow Details](#publishing-workflow-details)
    + [Automatic Deployment](#automatic-deployment)
    + [What Gets Published](#what-gets-published)
  * [Examples and References](#examples-and-references)

<!-- tocstop -->

# How to Publish Causify Blogs

## Overview

The Causify blog is hosted at
[https://blog.causify.ai/](https://blog.causify.ai/) and is built using MkDocs
Material with the blog plugin. All blog content is managed through the csfy
repository, and changes are automatically deployed via GitHub Actions.

## How to Publish a Blog

Publishing a blog post is straightforward:

1. **Create your blog post** as a Markdown file following the conventions below
2. **Add the file** to `//csfy/blog/docs/posts/` directory
3. **Commit and merge** your changes to the `master` branch

That's it! The
[publish_blog.yml](https://github.com/causify-ai/csfy/blob/master/.github/workflows/publish_blog.yml)
GitHub Action will automatically:

- Detect changes in the `blog/**` directory
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

## How to Preview Locally

Before publishing, you should preview your blog post locally to ensure it
renders correctly.

### Prerequisites

Activate the MkDocs virtual environment:

```bash
source "$HOME/src/venv/mkdocs/bin/activate"
```

This environment already has all the necessary dependencies (`mkdocs`,
`mkdocs-material`, etc.) installed.

### Steps to Preview

1. **Navigate to the blog directory:**

   ```bash
   cd ~/src/csfy1/blog
   ```

2. **Start the local server:**

   ```bash
   mkdocs serve
   ```

3. **Open the local site:**
   - The terminal will display the local URL (typically `http://127.0.0.1:8000`)
   - Open this URL in your browser to preview your blog

4. **Make changes:**
   - The server supports live reload
   - Any changes you make to blog posts or configuration will automatically
     refresh in your browser
   - This allows you to iterate quickly on your content

5. **Stop the server:**
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
     avatar: https://github.com/username.png # Or path to local image
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
---
title: Your Blog Post Title
authors:
  - author_id_1
  - author_id_2 # Optional: multiple authors.
date: YYYY-MM-DD
description: Brief description of the blog post (optional but recommended)
categories:
  - Category1
  - Category2 # Optional: multiple categories.
---
```

**Field descriptions:**

- **`title`**: The main title of your blog post (required)
- **`authors`**: List of author IDs from `.authors.yml` (required)
- **`date`**: Publication date in YYYY-MM-DD format (required)
- **`description`**: Short summary that appears in previews (optional but
  recommended)
- **`categories`**: List of categories from the allowed categories (optional)

### Blog Post Template

Here's a complete template for a new blog post:

```markdown
---
title: Your Compelling Blog Title
authors:
  - your_author_id
date: 2025-01-15
description:
  A brief, engaging description that will appear in blog previews and search
  results
categories:
  - Business
  - Startup
---

Your opening paragraph goes here. This should hook the reader and provide
context for what they're about to read.

This introduction text will appear in blog list previews.

<!-- more -->

## Main Content Starts Here

After the `<!-- more -->` separator, you can include the full content of your
blog post.

## Conclusion

Wrap up your thoughts and provide a call to action if appropriate.
```

### Naming Convention

Blog post files should follow this naming convention:

**Format:** `Title of the Blog.md`

**Examples:**

- `AI for Optimal Decision-Making.md`
- `Understanding Causal Inference.md`
- `How We Built Our Data Pipeline.md`

**Guidelines:**

- Use title case for the filename
- Spaces are allowed in filenames
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

**Example:**

```markdown
---
title: Why Causal AI Matters
authors:
  - gpsaggese
date: 2025-01-15
categories:
  - Business
---

Traditional AI can predict outcomes, but it can't explain why those outcomes
occur. This fundamental limitation means businesses are making decisions based
on correlations, not causation.

At Causify, we're changing that with Causal AI that understands the "why" behind
every prediction.

<!-- more -->

## The Problem with Correlation

Traditional machine learning models are exceptional at finding patterns...

[Rest of the detailed post]
```

## Working with Assets and Images

### Image Location

All blog images and assets should be stored in:
```
//csfy/blog/docs/assets/
```

**Directory structure:**
```
blog/
├── docs/
│   ├── assets/
│   │   ├── logo.png
│   │   ├── favicon.ico
│   │   ├── ETA_analogy.png
│   │   └── your_image.png
│   └── posts/
│       └── Your Blog Post.md
└── mkdocs.yml
```

### Referencing Images

From a blog post in `docs/posts/`, reference images using a relative path:

```markdown
![Image description](../assets/your_image.png)
```

**Examples:**

```markdown
![ETA analogy](../assets/ETA_analogy.png) ![Causify logo](../assets/logo.png)
![Architecture diagram](../assets/architecture_diagram.svg)
```

**Image best practices:**

- Always include descriptive alt text in square brackets
- Use descriptive filenames for images
- Optimize images for web (compress large files)
- Supported formats: PNG, JPG, SVG, GIF
- Use SVG for diagrams and logos when possible

## Available Categories

The blog currently supports the following categories (defined in `mkdocs.yml`):

- **"Causal News"** - News and updates related to causal AI and the field
- **"Causal ELI5"** - Explain Like I'm 5 - simplified explanations of causal
  concepts
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

1. Checks out the repository
2. Sets up Python 3.x
3. Installs MkDocs and MkDocs Material
4. Builds the static site (`mkdocs build` in `./blog` directory)
5. Configures AWS credentials via OIDC
6. Syncs the built site to S3: `s3://causify-blog` with `--delete` flag
7. (Optional) Invalidates CloudFront cache if configured

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

## Examples and References

**For detailed blog writing conventions:**

- Refer to:
  [`/docs/blogging/all.blog.how_to_guide.md`](/docs/blogging/all.blog.how_to_guide.md)

**Example blog posts:**

- Browse all published blogs:
  [https://github.com/causify-ai/csfy/tree/master/blog/docs/posts](https://github.com/causify-ai/csfy/tree/master/blog/docs/posts)
- Pick any `.md` file to see real examples of:
  - Frontmatter structure
  - Content organization
  - Image usage
  - Excerpt placement

**Study these examples to understand:**

- How to structure compelling introductions
- Where to place the `<!-- more -->` separator
- How to organize content with headers
- Effective use of images and formatting