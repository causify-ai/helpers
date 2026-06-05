<!-- toc -->

- [Gitleaks](#gitleaks)
  * [Configuration](#configuration)
    + [`allowlists`](#allowlists)
    + [Rule extension](#rule-extension)
    + [`rules`](#rules)
    + [`.gitleaksignore`](#gitleaksignore)
  * [Additional Resource](#additional-resource)

<!-- tocstop -->

# Gitleaks

- Gitleaks is a SAST tool used for detecting and preventing hardcoded secrets
  such as passwords, API keys, and tokens in a directory or git repository
- It detects secrets not only in the codebase but also in the git commit history
- Gitleaks can be integrated into our workflow to prevent secrets from being
  accidentally added to our codebase
- It is integrated into our dev system via:
  - Git hooks (Refer to
    [/docs/tools/git/all.git_hooks.reference.md)](/docs/tools/git/all.git_hooks.reference.md))
  - GitHub actions (Refer to
    [/docs/build_system/all.gitleaks_workflow.explanation.md](/docs/build_system/all.gitleaks_workflow.explanation.md)

## Configuration

- The rules for Gitleaks are specified in `.github/gitleaks-rules.toml`
- To avoid redundancy, the file is symlinked to a common file in `//helpers`
  located at
  [`/dev_scripts_helpers/git/gitleaks/gitleaks-rules.toml`](/dev_scripts_helpers/git/gitleaks/gitleaks-rules.toml)
  that can be shared across all repos

### `allowlists`

- We can use allowlists to make exceptions to certain files or lines of code
  based on paths or regex patterns
- If we want to exclude "specific" commits, lines, or rules, use the inline
  `# gitleaks:allow` comment or the `.gitleaksignore` file instead
  ```toml
  [[allowlists]]
  description = "global allow lists"
  paths = [
    '''.github/gitleaks-rules.toml''',
  ]
  ```

### Rule extension

- We can extend our custom ruleset to include the default ruleset provided by
  Gitleaks with:
  ```toml
  [extend]
  useDefault = true
  ```

### `rules`

- Each rule is defined with:
  - `id` - A unique identifier for each rule
  - `description` - Short human readable description of the rule
  - `regex` - Golang regular expression used to detect secrets
  - `tags` - Array of strings used for metadata and reporting purposes
- For example:
  ```toml
  [[rules]]
    id = "rule2"
    description = '''AWS API Key'''
    regex = '''AKIA[0-9A-Z]{16}'''
    tags = ["secret"]
  ```

### `.gitleaksignore`

- To prevent specific lines of code from being scanned by Gitleaks, we can use
  the `.gitleaksignore` file
- It uses "fingerprints" to define the leaks
- Gitleaks generates these fingerprints when it detects a leak, which can then
  be added to the file
- Examples of fingerprints:
  ```bash
  > ck.infra/infra/terraform/environments/preprod/ap-northeast-1/terraform.tfvars:rule3:429
  > 93f292c3dfa2649ef91f8925b623e79546fa992e:README.md:aws-access-token:121
  ```
- The `.gitleaksignore` file can be placed at the root directory of a repo

## Additional Resource

- The official GitHub page for Gitleaks -
  [https://github.com/gitleaks/gitleaks](https://github.com/gitleaks/gitleaks)
  [https://github.com/gitleaks/gitleaks-action/tree/master](https://github.com/gitleaks/gitleaks-action/tree/master)
- The custom ruleset was based on -
  [https://github.com/mazen160/secrets-patterns-db](https://github.com/mazen160/secrets-patterns-db)
