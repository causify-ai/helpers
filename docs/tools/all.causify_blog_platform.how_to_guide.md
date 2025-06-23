# Causify Blog Platform Documentation

<!-- toc -->

- [Introduction](#introduction)
  * [Stakeholders](#stakeholders)
- [Accessing the Blog](#accessing-the-blog)
  * [Public Access](#public-access)
  * [Admin Access (Staff Portal)](#admin-access-staff-portal)
- [Getting Started as a Staff User](#getting-started-as-a-staff-user)
  * [Receiving an Invitation](#receiving-an-invitation)
  * [Logging In](#logging-in)
- [Writing & Publishing Content](#writing--publishing-content)
  * [Example](#example)
    + [Step 1: Open the Ghost Admin panel](#step-1-open-the-ghost-admin-panel)
    + [Step 2: Create a new post](#step-2-create-a-new-post)
    + [Step 3: Insert Markdown card](#step-3-insert-markdown-card)
    + [Step 4: Paste the contents to post](#step-4-paste-the-contents-to-post)
    + [Step 5: Perform edits to the content](#step-5-perform-edits-to-the-content)
    + [Step 6: Handle authorship attribution](#step-6-handle-authorship-attribution)
    + [Step 7: Preview post](#step-7-preview-post)
    + [Step 8: Optionally add metadata like excerpt, tags, or scheduled time](#step-8-optionally-add-metadata-like-excerpt-tags-or-scheduled-time)
    + [Step 9: Publish the blog](#step-9-publish-the-blog)
- [Themes & Design](#themes--design)
- [Additional Guides & Tutorials](#additional-guides--tutorials)
  * [Creating and Managing Tags](#creating-and-managing-tags)
  * [Scheduling Posts](#scheduling-posts)
  * [Using Markdown & HTML Blocks](#using-markdown--html-blocks)
  * [Excerpt and Meta Data](#excerpt-and-meta-data)
  * [Integrations & Webhooks](#integrations--webhooks)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
- [Summary & Next Steps](#summary--next-steps)

<!-- tocstop -->

## Introduction

- The blog platform is accessible at [blog.causify.ai](https://blog.causify.ai)
- It enables us to share company updates, thought leadership content, and
  technical insights
- The audience includes both internal and external stakeholders
- The platform is built on **Ghost**, an open-source, modern publishing solution

### Stakeholders

- **Executives**: Gain visibility into platform reach, editorial calendar, and
  content quality
- **Marketing & Communications**: Publish and manage content (blog posts and
  announcements)
- **Technical Team**: Manage and maintain underlying infrastructure, security,
  and updates

## Accessing the Blog

### Public Access

- Navigate to [blog.causify.ai](https://blog.causify.ai). Readers can see
  published posts without logging in

### Admin Access (Staff Portal)

- Go to [blog.causify.ai/ghost](https://blog.causify.ai/ghost)
- Enter your email and password (provided via staff invites)
- After logging in, you can create, edit, or publish content—depending on your
  role

## Getting Started as a Staff User

### Receiving an Invitation

- An admin invites you by entering your email address in the **Staff → Invite
  People** section
- You receive an email link prompting you to create or confirm an account

### Logging In

- Open [blog.causify.ai/ghost](https://blog.causify.ai/ghost)
- Enter your credentials (email and password)
- You'll be taken to the Ghost Admin Dashboard, where you can see recent posts,
  drafts, and announcements

## Writing & Publishing Content

- Create a New Post
  - Click **New post** in the admin panel
  - Enter a title and start writing. Ghost uses a rich text/markdown hybrid
    editor with slash commands (`/`) for quick embeds

- Add Images & Media
  - Drag and drop images directly into the editor, or click the "+" button and
    select **Image**
  - (Optional): We can have S3 or external storage configured, so the files are
    automatically uploaded to that location

- Using Cards & Embeds
  - Type `/` in a new line to see options (e.g., Markdown card, HTML, YouTube
    embed, etc.)

- Preview & Publish
  - Click **Preview** to see how the post will appear to readers
  - When ready, click **Publish → Publish now** or schedule a specific time

- Tags & Organization
  - Add tags to group similar posts (e.g., `Company News`, `Technical`,
    `Research`)

### Example

- Consider the case where we want to push the Markdown file
  `all.invoke_git_branch_copy.how_to_guide.md` to the blog

- After creating an account, follow these steps:

#### Step 1: Open the Ghost Admin panel

- Open [blog.causify.ai/ghost](https://blog.causify.ai/ghost)
- Enter your credentials to login
- Open the Ghost Admin Panel

#### Step 2: Create a new post

- Click **New post** on the top right

#### Step 3: Insert Markdown card

- Use the `/markdown` command to insert a Markdown card

#### Step 4: Paste the contents to post

- Copy and paste the content of `all.invoke_git_branch_copy.how_to_guide.md`
  into the Markdown card

#### Step 5: Perform edits to the content

- Move the level 1 title (e.g., `# The Git Branch Copy Workflow`) into the Ghost
  post title field
- Delete the level 1 header from the Markdown card content

#### Step 6: Handle authorship attribution

- If you are a **Contributor**:
  - Add a temporary `## Authorship` section at the very top of the Markdown card
    content
  - List everyone who contributed (e.g., wrote code, reviewed, edited)

  Example:

  ```markdown
  ## Authorship
  - gpsaggese, aangelo9, Shayawnn, heanhsok
  ```

- If you are an **Author** or higher:
  - Add contributors directly in the **Authors** field using the Ghost sidebar
  - You do not need to include a `## Authorship` section in the content

- If you are reviewing a blog created by a **Contributor**:
  - You need to have **Author** or higher access to do this
  - Check the `## Authorship` section at the top of the Markdown card
  - Manually copy the listed names into the Ghost **Authors** field
  - Delete the `## Authorship` section from the Markdown content before
    publishing

#### Step 7: Preview post

- Click **Preview** on the top right to verify formatting (headings, TOC, code
  blocks)

#### Step 8: Optionally add metadata like excerpt, tags, or scheduled time

- These actions require **Author** access or higher
- **Contributors** cannot modify metadata or scheduling options

#### Step 9: Publish the blog

- Click **Publish → Publish now** (or schedule the post for later) to publish
  the blog
- If you are a **Contributor**, you cannot publish or schedule posts directly
- A staff member with **Author** or higher access must review and approve the
  post before it goes live

## Themes & Design

- Default Theme (Casper)
  - The blog currently uses Ghost's default theme, "Casper", providing a clean
    and responsive layout

- Customizing Design
  - Navigate to **Settings → Design** to upload a new theme or activate an
    existing one
  - Use **Code Injection** (under the same area) for tracking scripts (e.g.,
    Google Analytics) or custom CSS

## Additional Guides & Tutorials

- Below are step-by-step mini-tutorials to help users and contributors
  understand some advanced or less obvious features of Ghost

### Creating and Managing Tags

- What are tags?
  - Tags let you organize content into categories (e.g., `Product Updates`,
    `Engineering`)

- How to add tags
  - When editing a post, find the Tags section on the right panel, type a new
    tag name or select an existing one
  - Posts can have multiple tags (e.g., `Engineering` + `Announcements`)

- Managing tags
  - Go to **Posts → Tags** in the admin panel to rename or delete tags

### Scheduling Posts

- Why schedule posts?
  - Perfect for timing announcements, product releases, or holiday-themed posts

- How to schedule
  - Write your post, click **Publish → Schedule it for later**
  - Pick a date and time (in your local timezone)

- Editing a scheduled post
  - Navigate to **Posts → Scheduled**, then click the post to edit or change the
    scheduled time

### Using Markdown & HTML Blocks

- Markdown basics
  - Ghost's editor supports inline markdown. For advanced formatting, insert a
    Markdown card by typing `/markdown`
  - You can use headings, bold, italics, blockquotes, lists, etc.

- HTML cards
  - Type `/html` to embed raw HTML for custom iframes, custom scripts, or
    specialized formatting

### Excerpt and Meta Data

- Excerpt(Optional)
  - Under **Post settings → Excerpt**, you can define a short preview text for
    your post
  - This snippet appears on the home page or in RSS feeds, depending on your
    theme

- Meta title and description
  - For SEO benefits, set custom meta titles and descriptions under **Post
    settings → Meta data**

### Integrations & Webhooks

- Built-in integrations
  - Under **Settings → Integrations**, you can quickly connect Slack, Zapier, or
    other tools to notify our team when new posts are published

- Custom webhooks
  - You can create webhooks for publish events, letting external systems react
    (e.g., cross-posting to social media)

## Frequently Asked Questions (FAQ)

- How do I reset my password?
  - Click **Forgot Password?** on the login page. Check your inbox for a reset
    link (ensure it's not caught in spam)

- Why isn't my invitation email received?
  - Check your spam folder

- Can we schedule posts for later?
  - Yes, while publishing a new post, choose **Publish → Schedule it for later**

- How do I integrate analytics?
  - Use **Settings → Code Injection** to add your analytics script in the
    site-wide header/footer

- How to reset a staff user's password if they can't access email?
  - Admin can go to **Staff → Select User → Resend Invitation or Change
    Password**. Alternatively, the user can use the **Forgot Password?** link

- I see a "502 Bad Gateway" error when accessing blog.causify.ai. What do I do?
  - Contact the Infra/DevOps team to investigate network issues

- Why can't I see the scheduling option?
  - Make sure you have an Author (or higher) role. Contributors can't schedule
    posts

- Can we add custom pages (e.g., "About," "Contact," "Terms of Service")?
  - Yes. Create a new post and mark it as a page in **Post Settings** and toggle
    "Turn this post into a static page."
  - Adjust your theme's navigation to link these pages

## Summary & Next Steps

- We have successfully deployed a secure, scalable Ghost blog at
  [blog.causify.ai/ghost](https://blog.causify.ai/ghost)
  - Executives and stakeholders can review content for corporate alignment and
    brand consistency
  - Authors can quickly draft and publish posts, while editors ensure quality
  - Technical teams maintain the underlying Kubernetes infrastructure, backups,
    and security posture

- Next Steps:
  - Continue inviting staff members who need author access
  - Customize the theme to fit the Causify brand
  - Review and refine settings as you collect feedback from readers and
    contributors
