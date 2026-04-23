---
description: Reorganize rules in 
model: haiku
---

- Given a file `<topic>.rules.md` passed by the user
  - Read its content
  - Reorganize this file by grouping related topics into logical sections into
    (with header of level 1 #)
    ```
    # <Topic 1>

    ## <Topic 1.1>

    ## <Topic 1.2>

    ...

    # <Topic 2>
    ```
  - Do not change the text but only move it in the file
  - Save the result in the same file
