

<!-- toc -->



<!-- tocstop -->

This mainly follows the process described in
//cmamp/docs/coding/all.integrate_repos.how_to_guide.md

- Create a branch in both clients (e.g., `/Users/saggese/src/cmamp1` and
  `/Users/saggese/src/helpers1`)

  ```bash
  > cd /Users/saggese/src/cmamp1
  > git pull
  > i git_branch_create -b CmampTask10048_Integrate_helpers_20240922

  > cd /Users/saggese/src/helpers1
  > git pull
  > i git_branch_create -b CmampTask10048_Integrate_helpers_20240922
  ```

- Diff the dirs
  ```
  > diff_to_vimdiff.py --dir1 /Users/saggese/src/cmamp1/helpers --dir2 ~/src/helpers1/helpers
  > diff_to_vimdiff.py --dir1 /Users/saggese/src/cmamp1/helpers --dir2 /Users/saggese/src/cmamp2/helpers_root/helpers/
  ```
