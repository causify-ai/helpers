- **Introduction**  
  - Begin with a short paragraph introducing the topic.  
  - Avoid using bullet points or lists in the introduction.

- **Section Headings**  
  Use level 2 headings for main sections:  
  `## Section Title`  
  Use level 3 headings for subsections:  
  `### Subsection Title`

- **Paragraphs**  
  Write clear, concise paragraphs.  
  Separate paragraphs with a single blank line.

- **Lists**  
  For unordered lists, use `-` or `*`.  
  For ordered lists, use `1.`, `2.`, etc.

- **Code Blocks**  
  Use triple backticks for code examples:  
  ```
  code here
  ```
  For inline code, use single backticks: `inline code`

- **Quotes**
  Use `>` for blockquotes.

- **Links and Images**
  Links: `[text](URL)`
  Images: `![alt text](image URL)`

- **Emphasis**
  Use `_text_` for emphasis and `**text**` for strong emphasis.

- **Math (optional)**
  Inline: `$E = mc^2$`
  Block:
  `$$`
  `E = mc^2`
  `$$`

- **Metadata (optional)**
  At the top, include front matter in YAML format if needed:
  ```markdown
  ---
  title: "Blog Title"
  date: "2025-10-30"
  author: "Author Name"
  tags: ["tag1", "tag2"]
  ---
  ```

- **General Style**
  Maintain consistent spacing and indentation.

- Add a spicy TLDR
  ```bash
  > ccp Create 3 catchy and controversial TLDR of less than 20 words without emdash for blog/docs/posts/Your_data_isnt_as_ready_as_your_slide_says.md
  ```

- llm_cli.py -i ../blog/docs/posts/Data_is_dumb.md -pf docs/ai_coding/ai.gp_blog_prompt.md -o ../blog/docs/posts/Data_is_dumb.md --lint
