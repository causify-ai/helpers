"""
Bulk-transfer GitHub issues between repositories via GraphQL.

This script reads issue numbers/ranges from a text file, validates them **in the
source repo only**, skips PRs, applies a state filter (`open`/`closed`/`all`),
and transfers eligible **issues** to the destination repo. It prints a clear
plan, shows exclusions (why each item was skipped), supports dry-run, and can
trace browser redirects to reveal already-transferred issues.

Full guide: `.github/gh_migration/issue_migration.how_to_guide.md`

Dry-run (preview only):
    python .github/gh_migration/bulk_transfer_issues.py \
      --src causify-ai/cmamp \
      --dst causify-ai/csfy \
      --file .github/gh_migration/issues_to_transfer.txt \
      --state closed \
      --dry-run \
      --why \
      --max-title 100 \
      --trace-redirect

Execute for real:
    python .github/gh_migration/bulk_transfer_issues.py \
      --src causify-ai/cmamp \
      --dst causify-ai/csfy \
      --file .github/gh_migration/issues_to_transfer.txt \
      --state closed \
      --sleep 2 \
      --why \
      --max-title 100

Notes
-----
- PRs are excluded automatically (GitHub shares the number space for Issues/PRs).
- If you want to ignore state for singles as well as ranges, run with `--state all`.
- Labels/milestones are preserved only if identical ones already exist in the
  destination repo; otherwise GitHub drops them.
"""

import argparse
import logging
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

import requests

_LOG = logging.getLogger(__name__)

GQL_ENDPOINT = "https://api.github.com/graphql"


def get_token() -> str:
    """
    Return a GitHub token from the environment.

    :return: gh personal access token string
    """
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        _LOG.error("Set GITHUB_TOKEN or GH_TOKEN with repo access.")
        sys.exit(1)
    return token


def make_session(token: str) -> requests.Session:
    """
    Create a configured HTTP session for GitHub GraphQL.

    :param token: gh personal access token
    :return: session with required headers set
    """
    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "issue-transfer-script/1.0",
        }
    )
    return s


def split_owner_repo(spec: str) -> Tuple[str, str]:
    """
    Split a `owner/repo` spec into `(owner, repo)`.

    :param spec: repo spec
    :return: owner and repo
    """
    if "/" not in spec:
        _LOG.error("Bad repo spec (expected owner/repo): %s", spec)
        sys.exit(1)
    owner, repo = spec.split("/", 1)
    return owner, repo


def short_title(title: str, max_len: int) -> str:
    """
    Return a truncated, single-line title.

    :param title: raw title
    :param max_len: max characters allowed; 0 means unlimited
    :return: cleaned and truncated title with an ellipsis if needed
    """
    t = re.sub(r"\s+", " ", (title or "")).strip()
    if max_len > 0 and len(t) > max_len:
        return t[: max_len - 1] + "…"
    return t


def sanitize_title(t: str) -> str:
    """
    Normalize whitespace in a title to a single line.

    :param t: raw title string
    :return: cleaned, single-line title
    """
    title = re.sub(
        r"\s+", " ", (t or "").replace("\r", " ").replace("\n", " ")
    ).strip()
    return title


def parse_numbers_file(path: str) -> List[int]:
    """
    Parse an input file of issue numbers and ranges into a sorted, unique list.

    The file may contain comments beginning with `#`, blank lines,
    single numbers, and ranges like `1-10`. Separators may be spaces or
    commas.

    :param path: path to the input file
    :return: sorted list of unique issue numbers
    """
    if not os.path.isfile(path):
        _LOG.error("Input file not found: %s", path)
        sys.exit(1)
    tokens: List[str] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            for tok in re.split(r"[, \t]+", line):
                tok = tok.strip()
                if tok and re.fullmatch(r"\d+(?:-\d+)?", tok):
                    tokens.append(tok)
    numbers: List[int] = []
    for t in tokens:
        m = re.fullmatch(r"(\d+)-(\d+)", t)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a > b:
                _LOG.warning("Skipping invalid range: %s", t)
                continue
            numbers.extend(range(a, b + 1))
        else:
            numbers.append(int(t))
    numbers = sorted(set(numbers))
    if not numbers:
        _LOG.error("No issue numbers/ranges found in %s", path)
        sys.exit(1)
    return numbers


def execute_graphql(
    session: requests.Session, query: str, variables: Dict
) -> Dict:
    """
    Execute a GraphQL query or mutation against GitHub.

    :param session: configured requests session with auth headers
    :param query: GraphQL string
    :param variables: variables dict for the operation
    :return: parsed object from the response
    """
    response = session.post(
        GQL_ENDPOINT,
        json={"query": query, "variables": variables},
        timeout=45,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"GraphQL HTTP {response.status_code}: {response.text[:300]}"
        )
    payload = response.json()
    if "errors" in payload:
        # Raise the first reported error.
        message = payload["errors"][0].get("message", "GraphQL error")
        raise RuntimeError(message)
    data = payload["data"]
    return data


def get_repo_id(session: requests.Session, owner: str, name: str) -> str:
    """
    Fetch a repository node ID (needed for `transferIssue`).

    :param session: authenticated HTTP session
    :param owner: repository owner/org
    :param name: repository name
    :return: repository node ID
    """
    query = """
    query($owner:String!, $name:String!){
      repository(owner:$owner, name:$name){ id nameWithOwner }
    }"""
    data = execute_graphql(session, query, {"owner": owner, "name": name})
    repo = data.get("repository")
    if not repo:
        raise RuntimeError(f"Repo not found: {owner}/{name}")
    return repo["id"]


def get_issue_or_pr(
    session: requests.Session, owner: str, name: str, number: int
) -> Optional[Dict]:
    """
    Retrieve either an Issue or a PullRequest node by number.

    :param session: authenticated HTTP session
    :param owner: source repository owner
    :param name: source repository name
    :param number: issue/PR number
    :return: issue or PR
    """
    query = """
    query($owner:String!, $name:String!, $number:Int!){
      repository(owner:$owner, name:$name){
        iopr: issueOrPullRequest(number:$number){
          __typename
          ... on Issue { id number title url state }         # state: OPEN|CLOSED
          ... on PullRequest { id number title url state }   # state: OPEN|CLOSED
        }
      }
    }"""
    data = execute_graphql(
        session, query, {"owner": owner, "name": name, "number": int(number)}
    )
    repo = data.get("repository") or {}
    node = repo.get("iopr")
    return node


def trace_html_redirect(owner_repo: str, number: int) -> Optional[str]:
    """
    Follow the HTML redirect for a source issue URL to detect transfers.

    If the issue was already moved, GitHub redirects the browser to the
    destination repo's issue URL. This is for *reporting only*.

    :param owner_repo:`owner/repo` spec for the source repository
    :param number: issue number in the source repository
    :return: url if redirected, else None
    """
    start = f"https://github.com/{owner_repo}/issues/{number}"
    try:
        response = requests.get(start, allow_redirects=True, timeout=20)
        final = str(response.url)
        return final if final != start else None
    except Exception:
        return None


def transfer_issue(
    session: requests.Session, issue_id: str, dst_repo_id: str
) -> Dict:
    """
    Transfer a single issue by node ID to the destination repository.

    :param session: authenticated HTTP session
    :param issue_id: graphQL node ID of the source issue
    :param dst_repo_id: graphQL node ID of the destination repository
    :return: response data
    """
    mutation = """
    mutation($issueId:ID!, $repositoryId:ID!){
      transferIssue(input:{issueId:$issueId, repositoryId:$repositoryId}){
        issue{ number url title repository{ nameWithOwner } }
      }
    }"""
    result = execute_graphql(
        session, mutation, {"issueId": issue_id, "repositoryId": dst_repo_id}
    )
    return result


def main() -> None:
    # Parse command-line arguments.
    ap = argparse.ArgumentParser(
        description="Bulk transfer GitHub issues (Python, GraphQL)."
    )
    ap.add_argument("--src", default="causify-ai/cmamp")
    ap.add_argument("--dst", default="causify-ai/csfy")
    ap.add_argument(
        "--file", default=".github/gh_migration/issues_to_transfer.txt"
    )
    ap.add_argument(
        "--state", default="closed", choices=["open", "closed", "all"]
    )
    ap.add_argument("--sleep", type=float, default=2.0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--why", action="store_true", help="Explain exclusions.")
    ap.add_argument("--max-title", type=int, default=120)
    ap.add_argument("--trace-redirect", action="store_true")
    args = ap.parse_args()
    # Create an authenticated GitHub session.
    token = get_token()
    session = make_session(token)
    # Split owner/repo specs.
    src_owner, src_repo = split_owner_repo(args.src)
    dst_owner, dst_repo = split_owner_repo(args.dst)
    # Parse and validate the input file with issue numbers.
    numbers = parse_numbers_file(args.file)
    # Log run configuration.
    _LOG.info("Source repo:      %s", args.src)
    _LOG.info("Destination repo: %s", args.dst)
    _LOG.info("List file:        %s", args.file)
    _LOG.info("State filter:     %s", args.state)
    _LOG.info("Dry run:          %d", 1 if args.dry_run else 0)
    _LOG.info("Explain skips:    %d", 1 if args.why else 0)
    _LOG.info("Max title length: %d", args.max_title)
    _LOG.info("")
    # Fetch destination repository node ID.
    try:
        dst_repo_id = get_repo_id(session, dst_owner, dst_repo)
    except Exception as e:
        _LOG.error("ERROR: %s", e)
        sys.exit(1)
    # Initialize tracking containers.
    to_transfer: List[int] = []
    reasons: Dict[int, str] = {}
    kinds: Dict[int, str] = {}
    titles: Dict[int, str] = {}
    urls: Dict[int, str] = {}
    issue_ids: Dict[int, str] = {}
    redirects: Dict[int, str] = {}
    # Validate requested numbers against the source repository.
    _LOG.info(
        "Validating requested issues against %s (state: %s)...",
        args.src,
        args.state,
    )
    for n in numbers:
        try:
            node = get_issue_or_pr(session, src_owner, src_repo, n)
        except Exception as e:
            kinds[n] = "Unknown"
            reasons[n] = f"query error: {e}"
            continue
        if not node:
            kinds[n] = "Unknown"
            reasons[n] = f"not found in {args.src} (likely transferred)"
            if args.trace_redirect:
                final = trace_html_redirect(args.src, n)
                if final:
                    redirects[n] = final
            continue
        tname = node["__typename"]
        if tname == "PullRequest":
            kinds[n] = "PR"
            titles[n] = sanitize_title(node.get("title") or "")
            urls[n] = node.get("url") or ""
            reasons[n] = "is a Pull Request"
            continue
        if tname == "Issue":
            kinds[n] = "Issue"
            titles[n] = sanitize_title(node.get("title") or "")
            urls[n] = node.get("url") or ""
            issue_ids[n] = node.get("id") or ""
            st = (node.get("state") or "").lower()  # open|closed
            if args.state != "all" and st != args.state:
                reasons[n] = f"state is '{st}' (wanted '{args.state}')"
            else:
                to_transfer.append(n)
            continue
        kinds[n] = "Unknown"
        reasons[n] = "unrecognized node type"
    # Build and log the transfer plan.
    _LOG.info("Plan:")
    _LOG.info("  Requested: %d issues", len(numbers))
    _LOG.info(
        "  Eligible (%s in %s): %d issues", args.state, args.src, len(to_transfer)
    )
    _LOG.info("  First 20 to transfer:")
    for n in to_transfer[:20]:
        t = short_title(titles.get(n, ""), args.max_title)
        u = urls.get(n, "")
        if u:
            _LOG.info("   - #%d: %s (%s)", n, t, u)
        else:
            _LOG.info("   - #%d: %s", n, t)
    _LOG.info("")
    # Log exclusions when requested.
    excluded = [n for n in numbers if n not in to_transfer]
    if excluded and (args.why or args.dry_run):
        _LOG.info("Exclusions (%d):", len(excluded))
        for n in excluded:
            k = kinds.get(n, "Unknown")
            t = short_title(titles.get(n, ""), args.max_title)
            u = urls.get(n, "")
            reason = reasons.get(n, "unknown")
            line = f" - #{n} [{k}]"
            if t:
                line += f": {t}"
            line += f" — {reason}"
            if u:
                line += f" ({u})"
            if n in redirects:
                line += f"  → redirected to {redirects[n]}"
            _LOG.info("%s", line)
        _LOG.info("")
    # Exit early on dry-run.
    if args.dry_run:
        _LOG.info(
            "[DRY-RUN] Would transfer the following %d issues from %s → %s:",
            len(to_transfer),
            args.src,
            args.dst,
        )
        for n in to_transfer:
            t = short_title(titles.get(n, ""), args.max_title)
            u = urls.get(n, "")
            if u:
                _LOG.info("#%d: %s (%s)", n, t, u)
            else:
                _LOG.info("#%d: %s", n, t)
        return
    # Abort if no eligible issues remain.
    if not to_transfer:
        _LOG.error(
            "No issues matched the requested ranges *and* state '%s' after validation.",
            args.state,
        )
        sys.exit(1)
    # Transfer eligible issues.
    moved = 0
    for n in to_transfer:
        iid = issue_ids.get(n)
        disp = short_title(titles.get(n, ""), args.max_title)
        _LOG.info("Transferring #%d: %s → %s ...", n, disp, args.dst)
        try:
            result = transfer_issue(session, iid, dst_repo_id)
            issue = result["transferIssue"]["issue"]
            _LOG.info(
                "OK: #%d → %s#%d (%s)",
                n,
                issue["repository"]["nameWithOwner"],
                issue["number"],
                issue["url"],
            )
            moved += 1
        except Exception as e:
            _LOG.error("FAILED: #%d — %s", n, e)
        time.sleep(max(args.sleep, 0.0))
    # Summarize results.
    _LOG.info("Bulk transfer complete! Moved %d issues.", moved)


if __name__ == "__main__":
    main()
