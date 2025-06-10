# Gitleaks 

- Gitleaks is a SAST tool used for detecting and preventing hardcoded secrets 
	like passwords, api keys, and tokens in a directory or a git repository
- It detects secrets not only in the codebase, but also in the git commit history
- Gitleaks can be integrated into our workflow to prevent secrets from being 
	accidentally added to our codebase
- It is integrated into our workflow via 
	- Git hooks
	- GitHub actions

## Gitleaks Integration in GitHub Actions

### Features

- **Automatic Scanning**: Gitleaks runs automatically on every pull request to
  the master branch and for every push to the master branch. This ensures that
  new code is checked before merging
- **Scheduled Scans**: Gitleaks scans are scheduled to run once a
  day, ensuring regular codebase checks even without new commits
- **Workflow Dispatch**: Allows for manual triggering of the
  Gitleaks scan, providing flexibility for ad-hoc code analysis

### Setup

- **GitHub Action Workflow**: The Gitleaks integration is set up as a part of
  the GitHub Actions workflow in the
  [`.github/workflows/gitleaks.yml` file in each repo

### Configuration

- The rules for Gitleaks are specified in `.github/gitleaks-rules.toml`
- To avoid redundancy, the file is symlinked to a common file in `//helpers` 
	located `helpers_root/dev_scripts_helpers/git/gitleaks/gitleaks-rules.toml`
	that can be shared across all repos

- Allowlist
 - Used for exceptions on a file level, i.e. to exclude whole files 
 - For a line level exceptions see `.gitleaksignore` section
 ```toml
	[allowlist]
	description = "global allow lists"
	paths = [
		'''.github/gitleaks-rules.toml''',
	]
	```

- Rules extension
  - We can extend our custom ruleset to also include the default ruleset provided by
  Gitleaks.
  - `[extend]` - The flag that extends the custom ruleset. Has to be used with
    `useDefault = true`:
    ```toml
    [extend]
    useDefault = true
    ```

- Rules
	- Each rule is defined with:
	- `id` - A unique identifier for each rule
	- `description` - Short human readable description of the rule
	- `regex` - Golang regular expression used to detect secrets
	- `tags` - Array of strings used for metadata and reporting purposes

- To prevent specific lines of code from being scanned by Gitleaks, we can use the
`.gitleaksignore` file. 
- It uses "fingerprints" to define the leaks. 
- Gitleaks itself generates these fingerprints when it detects a leak. Then it 
  can be simply added to the file. 
- The file can be placed at the root directory of a repo. 

Examples of a fingerprint:
```bash
> ck.infra/infra/terraform/environments/preprod/ap-northeast-1/terraform.tfvars:rule3:429
> 93f292c3dfa2649ef91f8925b623e79546fa992e:README.md:aws-access-token:121
```

