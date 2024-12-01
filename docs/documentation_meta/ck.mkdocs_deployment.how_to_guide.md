

<!-- toc -->

- [MkDocs documentation deployment](#mkdocs-documentation-deployment)
  * [Solution overview](#solution-overview)
    + [Private solution specifics](#private-solution-specifics)
  * [Public solution specifics](#public-solution-specifics)
  * [Set-up guide](#set-up-guide)
    + [Private documentation](#private-documentation)
    + [Public documentation](#public-documentation)

<!-- tocstop -->

# MkDocs documentation deployment

## Solution overview

- [MkDocs](https://www.mkdocs.org/) with
  [Material theme](https://squidfunk.github.io/mkdocs-material) was chosen as a
  tool for serving documentation with
  - The choice was made based on native support for markdown files (in contrast
    with ReadTheDocs)
- The entrypoint for the documentation home page is `docs/README.md`
- Since MkDocs generates its own (prettier) TOC we filter out the markdown TOC
  before rendering the page to avoid duplicate content
  - For this we have custom python code `mkdocs/mkdocs-toc-tag-filter`

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
   - TODO(Juraj): provide details once fine grained tokens for cmamp are enabled
2. Log in to the utility server as a root ubuntu user (GP, Juraj, Shayan, Pavol
   have access)

`ssh ubuntu@172.30.2.44`

3. Store the GH PAT token in `/home/ubuntu/github_pat.txt`

4. Create directory for the repo

`mkdir /home/ubuntu/mkdocs`

4. Clone the repository here

- Use the credential store helper to only pass the `https` credentials once
  `git config --global credential.helper store`
  `git clone https://github.com/causify-ai/cmamp.git`

_Use username `jsmerix` and the token generated above as password_

5. Run the docker container
```
sudo docker run -d -v /home/ubuntu/mkdocs/cmamp/:/app -w /app -p 8191:8000 --name mkdocs \
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
56740982b0e2   squidfunk/mkdocs-material   "/sbin/tini -- mkdoc…"   9 seconds ago   Up 9 seconds   0.0.0.0:8191->8000/tcp, :::8191->8000/tcp   mkdocs
```

_Note if the output is empty, run `docker ps -a` to get the container ID and
debug further using `docker logs`_

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

8. Test validity of the updated configuration `sudo nginx -t` and restart
   service `sudo systemctl restart nginx`

### Public documentation

1. Create branch called `gh-pages`
2. Create a GH action to publish page
   - `.github/workflows/serve_mkdocs.yml`
   - The action code is modified from
     https://squidfunk.github.io/mkdocs-material/publishing-your-site/
3. Set-up GH pages in the repository settings
   - Https://github.com/kaizen-ai/kaizenflow/settings/pages
   - Make sure to use `Deploy from branch` and choose `docs/` root directory and
     branch `gh-pages`
4. Inside the `docs/` folder create a plain text file `CNAME` that contains a
   single line equal to the subdomain you want to serve your docs from
   - Https://www.mkdocs.org/user-guide/deploying-your-docs/#custom-domains
5. Within the domain registrar add CNAME record to point to a desired
   (sub)domain
   - Https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
6. Enable HTTPS enforcement within the GH pages settings
   - You can test the deployment using a manual run of the actions
