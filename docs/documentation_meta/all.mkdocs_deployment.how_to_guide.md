<!-- toc -->

- [MkDocs documentation deployment](#mkdocs-documentation-deployment)
  * [Solution overview](#solution-overview)
    + [Private solution specifics](#private-solution-specifics)
  * [Public solution specifics](#public-solution-specifics)
  * [Set-up guide](#set-up-guide)
    + [Private documentation](#private-documentation)
    + [Public documentation](#public-documentation)

<!-- tocstop -->

# Generate and deploy the documentation

## mkdocs
- We choose [MkDocs](https://www.mkdocs.org/) with
  [Material theme](https://squidfunk.github.io/mkdocs-material) 
  to publish the documentation
  - `MkDocs` has native support for markdown files in contrast with `ReadTheDocs`
- The entrypoint for the documentation home page is
  [`/docs/README.md`](/docs/README.md)

// lint_txt.py -i notes.startup_admin_guide/docs/tools.EOS.md --use_dockerized_prettier --use_dockerized_markdown_toc

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

## Generate the `mkdocs` dir

- Set the dir to render:
  ```
  > export SRC_DIR=docs
  > export DST_DIR=dev_scripts_helpers/documentation/mkdocs/tmp.mkdocs
  ```

- To render the docs in the tutorials:
  ```
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

- Go to http://localhost:8001

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

- GitHub renders the documentation at https://causify-ai.github.io/helpers/

# Docu

> export SRC_DIR=notes.startup_admin_guide
> preprocess_mkdocs.py --input $SRC_DIR --output_dir tmp.mkdocs | tee log.txt

(cd ~/src/tutorials1/tmp.mkdocs; mkdocs serve --dev-addr localhost:8001)

saggese@gpmac.local venv:(mkdocs) branch:'master' ~/src/tutorials1
> (cd ~/src/tutorials1/tmp.mkdocs; mkdocs serve --dev-addr localhost:8001)

# Document how the stuff is deployed

- TODO(gp):

- How to publish the blog
Where is it

- How to publish doc for 
notes.programming_with_ai/ notes.startup_admin_guide/

- How to publish documentation
/Users/saggese/src/cmamp1/helpers_root/.github/workflows/publish_mkdocs.yml

- How to publish from gpsaggese GitHub?

# MkDocs documentation deployment

- TODO(gp): Review the rest

## Solution overview

### Private solution specifics

- The internal (private) documentation is served on utility server:
  http://172.30.2.44/docs
- The deployment runs on NGINX proxy on top of MkDocs default development server
  running in a simple docker container

## Public solution specifics

- We serve public documentation via GitHub pages feature
  - We use subdomain `docs.kaizen-tech.ai`
- The documentation website is redeployed upon each commit to `master` via
  GitHub actions

## Set-up guide

### Private documentation

1. Create a GitHub personal access token
2. Log in to the utility server as a root ubuntu user
   ```
   > ssh ubuntu@172.30.2.44
   ```

3. Store the GH PAT token in `/home/ubuntu/github_pat.txt`

4. Create directory for the repo
   ```
   > mkdir /home/ubuntu/mkdocs
   ```

4. Clone the repository here

- Use the credential store helper to only pass the `https` credentials once
  `git config --global credential.helper store`
  `git clone https://github.com/causify-ai/cmamp.git`

5. Run the docker container
  ```bash
  > sudo docker run -d -v /home/ubuntu/mkdocs/cmamp/:/app -w /app -p 8191:8000 --name mkdocs \
    --entrypoint /bin/sh squidfunk/mkdocs-material \
    -c "pip install -e mkdocs/mkdocs-toc-tag-filter && mkdocs serve --dev-addr=0.0.0.0:8000"
  ```

   - Make sure to set the path to volume correctly based on your file system set-up
   - The default entrypoint of the image needs to be overriden because we need to
     install our custom plugin first

6. Confirm the container has been deployed successfully using
   `docker ps | grep mkdocs`, the output should look something like this (other
   container will be running as well):
   ```
   56740982b0e2   squidfunk/mkdocs-material   "/sbin/tini -- mkdoc..."   9 seconds ago   Up 9 seconds   0.0.0.0:8191->8000/tcp, :::8191->8000/tcp   mkdocs
   ```

   - If the output is empty, run `docker ps -a` to get the container ID and debug
     further using `docker logs`

6. Create cronjob to periodically pull the latest master
   - Open the crontab `crontab -e`
   - Add the following line
     `*/10 * * * * cd /home/ubuntu/mkdocs/cmamp && git pull >> /home/ubuntu/mkdocs.log 2>&1`

7. Add NGINX directive in the default page (it's important that it's above S3
   static website related directive)

   `sudo vim /etc/nginx/sites-available/default`
   ```
   location ^~ /docs/ {
           proxy_set_header Host $host;
           proxy_pass http://localhost:8191/;
           proxy_redirect off;
   }
   ```

8. Test the updated configuration `sudo nginx -t` and restart service
   `sudo systemctl restart nginx`

### Public documentation

1. Create branch called `gh-pages`
2. Create a GH action to publish page
   - `.github/workflows/serve_mkdocs.yml`
   - The action code is modified from
     https://squidfunk.github.io/mkdocs-material/publishing-your-site/
3. Set-up GH pages in the repository settings
   - `https://github.com/causify-ai/kaizenflow/settings/pages`
   - Make sure to use `Deploy from branch` and choose `docs/` root directory and
     branch `gh-pages`
4. Inside the `docs/` folder create a plain text file `CNAME` that contains a
   single line equal to the subdomain you want to serve your docs from
   https://www.mkdocs.org/user-guide/deploying-your-docs/#custom-domains
5. Within the domain registrar add CNAME record to point to a desired
   (sub)domain
   https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
6. Enable HTTPS enforcement within the GH pages settings
   - You can test the deployment using a manual run of the actions
