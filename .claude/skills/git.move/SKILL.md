---
description: Move a file in git and use 
---

Given a file or a directory in the current repo, as a source and a destination

- Make sure the enclosing directory exists

- Make sure that the destination doesn't exist already

- Move it to the destination using `git mv`

- Find and replace all the references to that file in the repo and update the
  references to the destination
