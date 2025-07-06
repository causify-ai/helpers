# How to create and publish a Jekyll blog on GitHub Pages

## Set up Jekyll

https://github.com/jekyll/jekyll

### Install Jekyll locally

- Install Ruby and Bundler:
  ```bash
  > gem install jekyll bundler
  ```

  - Create a new site:
  ```bash
  > jekyll new my-blog
  > cd my-blog
  ```

  - Build and serve locally:
  ```bash
  > bundle exec jekyll serve
  ```

  - Open your browser at http://localhost:4000 to see your site

### Use Docker

- Instructions at https://github.com/envygeeks/jekyll-docker/blob/master/README.md

- Pull docker
  ```
  > docker pull jekyll/jekyll
  ```

- On Mac
  > docker run --platform linux/amd64 -v $(pwd):/site jekyll/jekyll jekyll new blog


export JEKYLL_VERSION=3.8
docker run --rm \
  --platform linux/amd64 \
  --volume="$PWD:/srv/jekyll:Z" \
  -it jekyll/jekyll:$JEKYLL_VERSION \
  jekyll build

## Add blog posts on GitHub
  - Create a `_posts` folder if it doesn't exist
  - Add Markdown files named in the format `YYYY-MM-DD-title.md`, for example:
    ```text
    _posts/2025-07-06-my-first-post.md
    ```

  - Each post needs front matter at the top:
  ```text
    ---
    layout: post
    title: "My First Blog Post"
    date: 2025-07-06
    ---

    This is my first blog post written in Markdown
    ```

## Configure GitHub Pages
  - Push your code to GitHub
  - Go to the repository's Settings > Pages
  - Set the source branch to main and the folder to / (root) or /docs if your
    site is in a docs folder
  - Save your settings. Your site will be published at:
    `https://yourusername.github.io/my-blog/`

- Add a custom domain (optional)
  - Buy a domain name and update your DNS to point to `yourusername.github.io`
  - In your repo, create a file named CNAME with your custom domain name:
    `www.yourdomain.com`

## Configure

- Example `_config.yml` to configure your site:
  ```text
  title: My Blog
  description: A blog powered by Jekyll and GitHub Pages
  baseurl: ""
  url: "https://yourusername.github.io"

  remote_theme: jekyll/minima

  plugins:
    - jekyll-feed
  ```

- Add an `index.md` at the root of your repo:
  ```text
  ---
  layout: home
  ---
  ```

- Folder structure example
  ```text
  ├── _config.yml
  ├── _posts/
  │   └── 2025-07-06-my-first-post.md
  ├── index.md
  └── CNAME  # only if using a custom domain
  ```

- Every time you push changes to GitHub, GitHub Pages will rebuild and publish your site automatically

# Hugo

docker run --rm -it -v $(pwd):/src klakegg/hugo:ext new site blog --force

https://themes.gohugo.io/tags/blog/

Ananke is not compatible with the klakegg version

Download a them from https://github.com/theNewDynamic/gohugo-theme-ananke

unzip blog/gohugo-theme-ananke-main.zip

mv gohugo-theme-ananke-main blog/themes/ananke

Add  

theme = "ananke"
j
config.toml


> docker run --rm -it -v $(pwd):/src klakegg/hugo:ext new posts/my-first-post.md
WARN 2025/07/06 15:41:14 Module "ananke" is not compatible with this Hugo version; run "hugo mod graph" for more information.
Content "/src/content/posts/my-first-post.md" created

vi ./content/posts/my-first-post.md


https://themes.gohugo.io/themes/hugo-book/

https://github.com/alex-shpak/hugo-book#
https://hugo-book-demo.netlify.app/

docker build -t hugo .

hugo mod clean

rm -rf public

docker run --rm -it -p 1313:1313 -v $(pwd):/src hugo hugo server --bind 0.0.0.0
