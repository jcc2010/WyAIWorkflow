#!/usr/bin/env python3
"""Daily audit: file one GitHub issue per commit that skipped the workflow, in that project's repo.
A script logs skips, not the agent: an agent that skipped the workflow won't reliably report itself.

    skip_audit.py                  dry run: print what would be filed; writes nothing to GitHub
    skip_audit.py --dry-run        the same, said out loud
    skip_audit.py --file           file the issues

Reads non-merge commits authored since START on each integration ref in check-names.py's PROJECTS, as
pushed (origin/<branch>), since an unpushed commit can still be amended and GitHub can't show it.
Flags a commit with no valid `Workflow:` trailer; a `full` trailer whose plan is missing at that
commit or has no plan-reality-check line in ~/.claude/review-verdicts.jsonl; a `Fixes #N` naming
no issue. The failing-run grep stays report-only in scorecard.py: it is too rough to file from.

Files only on a private GitHub repo with issues on; anything else is skipped and said so. A
commit already named by any issue, open or closed, is not filed: its SHA in the title or the body,
so a removed label or an edited title doesn't file it again, though removing both SHAs would.
Closing an issue is how a skip is accepted. A repo over MAX_PER_RUN new offences files nothing,
every run, until someone looks: that many at once means a bad START or a broken check, not that
many skips. A dry run says so. A git or gh failure skips the repo with its reason, never reads as clean.

Limits, recorded and not solved: stages 4-9 show only where they leave evidence; a feature
declared `shrunk` passes; a `Bug: none` can't be checked against what the commit did."""
import argparse, datetime as dt, json, pathlib, re, subprocess, sys, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scorecard as sc

START = "2026-11-03T00:52:00+00:00"  # set this to when your gate went live. Older commits had nothing asking for a trailer
LABEL = "workflow-skip"
MAX_PER_RUN = 25
FIXES = re.compile(r"^Fixes #(\d+)\s*$", re.M)


class GitError(Exception):
    """git couldn't answer: never to be read as "nothing found"."""


def checked_git(repo, *args):
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, errors="replace")
    if run.returncode:
        raise GitError(f"git {args[0]} failed: {run.stderr.strip()[:80]}")
    return run.stdout


def run_gh(*args):
    try:
        return subprocess.run(["gh", *args], capture_output=True, text=True, errors="replace", timeout=60)
    except (subprocess.TimeoutExpired, OSError) as e:
        return types.SimpleNamespace(returncode=1, stdout="", stderr=str(e))


def reasons_for(repo, sha, body, plans, issue_exists):
    m = sc.TRAILER.search(body)
    if not m:
        return ["no valid Workflow: trailer"]
    out = []
    plan = m.group(2)
    if plan:  # only `full` carries a plan
        if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}:{plan}"], capture_output=True).returncode:
            checked_git(repo, "cat-file", "-e", f"{sha}^{{commit}}")  # a commit git can't read isn't a missing plan
            out.append(f"full, but its plan {plan} is not at this commit")
        if sc.plan_key(plan) not in plans:
            out.append(f"full, but no plan-reality-check line names {plan}")
    out += [f"Fixes #{n}, but that issue does not exist" for n in FIXES.findall(body) if issue_exists(n) is False]
    return out


def offences(repo, ref, plans, issue_exists):
    """[(sha, subject, [reason, ...])] for commits on ref since START, oldest first."""
    log = checked_git(repo, "log", ref, "--no-merges", "--reverse", "--format=%H%x00%at%x00%B%x1e", f"--since={START}")
    out = []
    for entry in filter(str.strip, log.split("\x1e")):
        sha, authored, body = entry.strip().split("\0", 2)
        # --since reads the committer date, which a rebase resets; work written before START stays exempt
        if int(authored) < dt.datetime.fromisoformat(START).timestamp():
            continue
        reasons = reasons_for(repo, sha, body, plans, issue_exists)
        if reasons:
            out.append((sha, (body.splitlines() or [""])[0], reasons))
    return out


def issue_exists(slug, unknown):
    """True, False, or None when GitHub didn't say (noted in unknown): only a real 404 is a finding."""
    def check(n):
        r = run_gh("api", f"repos/{slug}/issues/{n}", "--silent")
        if r.returncode == 0:
            return True
        if "404" in r.stderr:
            return False
        unknown.append(n)
        return None
    return check


def fetch(repo, branch):
    """Bring origin/<branch> up to date. False leaves the last known ref, which only delays a finding."""
    try:
        return subprocess.run(["git", "-C", str(repo), "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
                               "fetch", "-q", "origin", branch], capture_output=True, timeout=60).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def audit_project(repo, ref, slug, do_file, plans=None):
    """{"skipped": why} or {"new": [...], "filed_before": n, "filed": n, "errors": [...], "unknown": [...], "over_cap": bool}."""
    meta = run_gh("api", f"repos/{slug}")
    if meta.returncode:
        return dict(skipped=f"can't read the repo: {meta.stderr.strip()[:80]}")
    meta = json.loads(meta.stdout)
    if meta.get("visibility") != "private":
        return dict(skipped=f"{meta.get('visibility', 'unknown')} repo: nothing is filed on one unless the owner says so")
    if not meta.get("has_issues"):
        return dict(skipped="issues are off on this repo")
    if sc.git(repo, "rev-parse", "--verify", "-q", ref).strip() == "":
        return dict(skipped=f"no ref {ref}")
    listed = run_gh("issue", "list", "-R", slug, "--state", "all", "--limit", str(sc.ISSUE_LIMIT), "--json", "title,body")
    if listed.returncode:
        return dict(skipped=f"can't read the issue list: {listed.stderr.strip()[:80]}")
    rows = json.loads(listed.stdout)
    if len(rows) >= sc.ISSUE_LIMIT:  # the list may be cut short, and a commit could be filed twice
        return dict(skipped=f"can't read the whole issue list: it stops at {sc.ISSUE_LIMIT}")
    plans = sc.checked_plans(repo.name) if plans is None else plans
    unknown = []
    try:
        found = offences(repo, ref, plans, issue_exists(slug, unknown))
    except GitError as e:
        return dict(skipped=str(e))
    new = [o for o in found if not any(o[0][:12] in r["title"] or o[0] in (r.get("body") or "") for r in rows)]
    over_cap = len(new) > MAX_PER_RUN
    result = dict(new=new, filed_before=len(found) - len(new), filed=0, errors=[], unknown=unknown, over_cap=over_cap)
    if not do_file or not new:
        return result
    if over_cap:
        return dict(skipped=f"{len(new)} new offences is over the cap of {MAX_PER_RUN}; filed none, check START")
    made = run_gh("label", "create", LABEL, "-R", slug, "--force", "--color", "BFD4F2",
                  "--description", "A commit that skipped the workflow; filed by skip_audit.py")
    if made.returncode:
        return dict(skipped=f"can't create the label: {made.stderr.strip()[:80]}")
    for sha, subject, reasons in new:
        body = (f"Commit {sha} on the integration branch skipped the workflow:\n\n" + "".join(f"- {r}\n" for r in reasons)
                + "\nFiled by `skip_audit.py` in the workflow repo. Close this with a note once it's dealt with; "
                  "a commit named by a closed issue is not filed again.")
        r = run_gh("issue", "create", "-R", slug, "--label", LABEL, "--title", title(sha, subject), "--body", body)
        if r.returncode:
            result["errors"].append(f"{sha[:12]}: {r.stderr.strip()[:80]}")
        else:
            result["filed"] += 1
    return result


def title(sha, subject):
    return f"Workflow skip: {sha[:12]} {subject[:70]}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="the default")
    mode.add_argument("--file", action="store_true", help="file the issues")
    args = ap.parse_args()
    print(f"{'Filing' if args.file else 'Dry run'}: commits since {START}")
    failed = False
    for path, ref in sc.projects().items():
        repo, name = sc.HOME / path, path.split("/")[-1]
        if not repo.is_dir():
            print(f"{name}: skipped: no checkout")
            continue
        slug = sc.github_slug(repo)
        if not slug:
            print(f"{name}: skipped: no GitHub remote")
            continue
        branch = ref.removeprefix("origin/")
        stale = "" if fetch(repo, branch) else " (fetch failed: read the last known origin ref)"
        result = audit_project(repo, f"origin/{branch}", slug, args.file)
        if "skipped" in result:
            print(f"{name}: skipped: {result['skipped']}")
            continue
        verb = f"filed {result['filed']} of" if args.file else "would file"
        print(f"{name}: {verb} {len(result['new'])}, {result['filed_before']} filed before{stale}")
        for sha, subject, reasons in result["new"]:
            print(f"  {title(sha, subject)}\n    " + "; ".join(reasons))
        if result["over_cap"]:
            print(f"  OVER THE CAP of {MAX_PER_RUN}: --file would file none of these; check START")
        if result["unknown"]:
            print("  GitHub didn't say whether these exist: " + ", ".join(f"#{n}" for n in result["unknown"]))
        for e in result["errors"]:
            print(f"  ERROR {e}")
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
