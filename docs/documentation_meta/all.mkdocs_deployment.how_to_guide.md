<!-- toc -->

- [MkDocs documentation deployment](#mkdocs-documentation-deployment)
  * [Solution overview](#solution-overview)
    + [Private solution specifics](#private-solution-specifics)
  * [Public solution specifics](#public-solution-specifics)
  * [Set-up guide](#set-up-guide)
    + [Private documentation](#private-documentation)
    + [Public documentation](#public-documentation)

<!-- tocstop -->

# Summary
- Describe the tools under `//helpers/docs/mkdocs`

# Generate and deploy the documentation

## mkdocs
- We choose [MkDocs](https://www.mkdocs.org/) with
  [Material theme](https://squidfunk.github.io/mkdocs-material) 
  to publish the documentation
  - `MkDocs` has native support for markdown files in contrast with `ReadTheDocs`
- The entrypoint for the documentation home page is
  [`/docs/README.md`](/docs/README.md)

## Scripts

```bash
> ls -1 docs/mkdocs/docs/
fix_markdown.sh
fix_markdown2.sh
preprocess_mkdocs.py
render_local.sh
set_mkdocs.sh
```

- `fix_markdown.sh`, `fix_markdown2.sh`: fix some small char issues in markdown
- `preprocess_mkdocs.py`: pre-process markdown files from an input directory so
   that they can be rendered by `mkdocs`
- `render_local.sh`: 
- `set_mkdocs.sh`:

## Layout of a publishable dir

- TODO(gp): Finish this and make sure the layout is always the same for all the
  publishing stuff
  ```
  > tree blog --dirsfirst -n -F --charset unicode
  blog/
  |-- docs/
  |   |-- assets/
  |   |   |-- favicon.ico
  |   |   `-- logo.png
  |   |-- posts/
  |   |   |-- blog1.md
  |   |   |-- blog2.md
  |   |   `-- blog3.md
  |   |-- styles/
  |   |   `-- styles.css
  |   `-- index.md
  `-- mkdocs.yml
  ```

## To lint the markdown

- Run the markdown:
  ```bash
  > lint_txt.py -i $FILE --use_dockerized_prettier --use_dockerized_markdown_toc
  ```

- To use `prettier` directly:
  ```bash
  > prettier --write --print-width 80 --prose-wrap always $FILE
  ```

## Generate the `mkdocs` dir

- Set the dir to render:
  ```bash
  > export SRC_DIR=docs
  > export DST_DIR=dev_scripts_helpers/documentation/mkdocs/tmp.mkdocs
  ```

- To render the docs in the tutorials:
  ```bash
  > cd //tutorials1
  > export SRC_DIR=notes.startup_admin_guide
  > export DST_DIR=tmp.mkdocs
  ```

- Create the documentation for `mkdocs` from the `docs` directory
  ```bash
  > preprocess_mkdocs.py --input $SRC_DIR --output_dir $DST_DIR
  ```
- This script:
  - Copies all the files from `docs` to `tmp.mkdocs` so that we can modify the
    files in `tmp.mkdocs`
  - Process each of the markdown files in place in `tmp.mkdocs`, performing
    several transformations, e.g.,
     - Remove the table of content stored between <!-- toc --> and <!-- tocstop -->
     - Render ```python by dedenting so that it is aligned
     - Replace 2 spaces indentation with 4 spaces since this is what `mkdocs` needs

## Debug 

- After running `preprocess_mkdocs.py` you can see how the markdown are
  transformed with:
  ```bash
  > diff -r --brief docs tmp.mkdocs
  > diff_to_vimdiff.py --dir1 docs --dir2 tmp.mkdocs
  ```

- To serve the HTML locally:
  ```bash
  > (cd $DST_DIR; mkdocs serve --dev-addr localhost:8001)
  ```

- Go to [http://localhost:8001](http://localhost:8001)

## Publish the documentation

- `mkdocs` will generate HTML code from the `tmp.mkdocs` dirs

- You need to install `mkdocs` in a virtual env
  ```bash
  > set_mkdocs.sh
  ```

- Then you can activate the environment with:
  ```bash
  > source mkdocs.venv/bin/activate
  ```
  - TODO(gp): Convert this into a dockerized executable

- Publish 
  ```
  > (cd $DST_DIR; mkdocs gh-deploy)
  ```

- GitHub renders the documentation at [https://causify-ai.github.io/helpers/](https://causify-ai.github.io/helpers/)

# Docu

> export SRC_DIR=notes.startup_admin_guide
> preprocess_mkdocs.py --input $SRC_DIR --output_dir tmp.mkdocs | tee log.txt

(cd ~/src/tutorials1/tmp.mkdocs; mkdocs serve --dev-addr localhost:8001)

saggese@gpmac.local venv:(mkdocs) branch:'master' ~/src/tutorials1
> (cd ~/src/tutorials1/tmp.mkdocs; mkdocs serve --dev-addr localhost:8001)

# Document how the stuff is deployed

- TODO(gp):

- How to publish the blog
  - Where is it?

- How to publish `docs` from `//helpers`

- How to publish doc for `notes.` in `//tutorials/
  - notes.programming_with_ai/
  - notes.startup_admin_guide/

- How to publish documentation with GH actions

- How to publish from gpsaggese GitHub?
