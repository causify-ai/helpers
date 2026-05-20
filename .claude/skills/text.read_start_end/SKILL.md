---
description: Read a text between <start> and <end>
---

Given
- a file passed from the user `<file>`
- a number of slides passed from the user `<num_slides>`

# Step 1: Extract the Text
- In the file `<file>` read the chunk between `<start>` and `<end>`
  - Make sure there is a single chunk of text

- Do not write anything, besides the name of the file and the num of lines read

# Step 2:
- Call the skill `/slides.write` to create `<num_slides>`
  and save them to `summary.md`

# Step 3:
- `cat summary.md`
