#!/usr/bin/env python3
"""Check that every skill and agent named in the dev workflow, and in each project's
CLAUDE.md "## Workflow" section, exists. Exit 1 on any MISSING line.

    check-names.py                 check the workflow and every project's integration branch
    check-names.py PATH...         also check these CLAUDE.md files (a worktree's, before commit)

Each project is read from its integration branch (PROJECTS below);
the working file is used instead when the checkout is on that branch, so uncommitted edits
are checked. A listed project with no Workflow section fails. Any other repo whose
CLAUDE.md mentions dev-workflow.md is found and checked too.

Every SKILL.md you own (~/.claude/skills and ~/.claude/scheduled-tasks) must be under
SKILL_BYTES; move sections into sibling files read at the step that needs them.

Account plugins (enabled on claude.ai, no files on this Mac) print as UNVERIFIED and do not
fail; any other unknown plugin is MISSING. BUILTIN is hand-kept: commands that ship with
Claude Code and have no file to find."""
import json, pathlib, re, shutil, subprocess, sys

HOME = pathlib.Path.home()
WORKFLOW = pathlib.Path(__file__).resolve().with_name("dev-workflow.md")
PROJECTS = {  # path under ~: integration ref. Example:
    # "code/my-app": "main",
    # "code/shared-checkout": "origin/main",  # a checkout whose local main lags
}
DISCOVER = []  # folders under ~ to search for other repos, e.g. ["code"]
BUDGET = 100  # lines in dev-workflow.md; see CHANGELOG.md
SKILL_BYTES = 20000  # compaction re-attaches an invoked skill cut at 20,000 characters (obra/superpowers#2481)
WORDS = 1300  # words, so the line budget cannot be beaten with long lines (table rows can't wrap)
SUBAGENTS = WORKFLOW.with_name("subagents.md")  # optional: a separate dispatch workflow
SUB_BUDGET, SUB_WORDS = 60, 600  # its own, smaller budget
BUILTIN = {"compact", "code-review", "simplify", "security-review", "run", "loop", "schedule"}
ACCOUNT_PLUGINS = {  # claude.ai account plugins: no files on disk, so not checkable here
    "product-management", "productivity", "data", "operations",
}
NAME = re.compile(r"`/?([a-z][A-Za-z0-9_-]*(?::[A-Za-z0-9_-]+)?)`")
SECTION = re.compile(r"^## Workflow[ \t]*\n(.*?)(?=^## |\Z)", re.M | re.S)

def load(path):
    return json.loads(path.read_text()) if path.is_file() else {}


installed = load(HOME / ".claude/plugins/installed_plugins.json").get("plugins", {})
enabled = load(HOME / ".claude/settings.json").get("enabledPlugins", {})
local = {k.split("@")[0]: pathlib.Path(v[0]["installPath"])
         for k, v in installed.items() if enabled.get(k, True)}


def plugin_skill(plugin, skill):
    root = local[plugin]
    if (root / "skills" / skill / "SKILL.md").is_file():
        return True
    top = root / "SKILL.md"  # single-skill plugins keep it at the root
    return top.is_file() and re.search(rf"^name:\s*{re.escape(skill)}\s*$", top.read_text(), re.M) is not None


def exists(name, project=None):
    """True, False, or None (account plugin, not checkable here)."""
    if ":" in name:
        plugin, skill = name.split(":")
        if plugin in local:
            return plugin_skill(plugin, skill)
        return None if plugin in ACCOUNT_PLUGINS else False
    if name in BUILTIN or shutil.which(name):  # a shell command (`date`), not a skill
        return True
    roots = [HOME / ".claude"] + ([project / ".claude"] if project else [])
    return any((r / "skills" / name / "SKILL.md").is_file() or (r / "agents" / f"{name}.md").is_file()
               for r in roots)


def read_project(repo, ref):
    """CLAUDE.md from the integration branch, or the working file when checked out on it."""
    if not repo.is_dir():
        raise FileNotFoundError(f"no such repo {repo}")
    branch = subprocess.run(["git", "-C", repo, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
    if branch == ref:
        return (repo / "CLAUDE.md").read_text()
    shown = subprocess.run(["git", "-C", repo, "show", f"{ref}:CLAUDE.md"],
                           capture_output=True, text=True)
    if shown.returncode:
        raise FileNotFoundError(shown.stderr.strip())
    return shown.stdout


failed = False


def report(kind, name, where):
    global failed
    print(f"{kind:<10} {name}  ({where})")
    failed |= kind == "MISSING"


def check(text, where, project=None):
    for n in sorted(set(NAME.findall(text))):
        ok = exists(n, project)
        if ok is None:
            report("UNVERIFIED", n, f"{where}: account plugin")
        elif not ok:
            report("MISSING", n, where)


def section(text, where):
    m = SECTION.search(text.replace("\r\n", "\n"))
    if not m:
        report("MISSING", "## Workflow section", where)
    return m.group(1) if m else ""


check(WORKFLOW.read_text(), WORKFLOW.name)
lines = len(WORKFLOW.read_text().splitlines())
if lines > BUDGET:
    report("MISSING", f"line budget: {lines} > {BUDGET}; delete or merge a rule first", WORKFLOW.name)
words = len(WORKFLOW.read_text().split())
if words > WORDS:
    report("MISSING", f"word budget: {words} > {WORDS}; delete or merge a rule first", WORKFLOW.name)

if SUBAGENTS.is_file():
    sub = SUBAGENTS.read_text()
    check(sub, SUBAGENTS.name)
    if len(sub.splitlines()) > SUB_BUDGET:
        report("MISSING", f"line budget: {len(sub.splitlines())} > {SUB_BUDGET}; delete or merge a rule first", SUBAGENTS.name)
    if len(sub.split()) > SUB_WORDS:
        report("MISSING", f"word budget: {len(sub.split())} > {SUB_WORDS}; delete or merge a rule first", SUBAGENTS.name)

for md in sorted((HOME / ".claude/skills").glob("*/SKILL.md")) + sorted((HOME / ".claude/scheduled-tasks").glob("*/SKILL.md")):
    if md.stat().st_size >= SKILL_BYTES:
        report("MISSING", f"skill size: {md.stat().st_size} bytes >= {SKILL_BYTES}; move sections into sibling files", str(md))

repos = {HOME / p: ref for p, ref in PROJECTS.items()}
for base in DISCOVER:
    for md in sorted((HOME / base).glob("*/CLAUDE.md")):
        repo = md.parent
        if (repo / ".git").is_dir() and repo not in repos and "dev-workflow.md" in md.read_text():
            repos[repo] = "main"
for repo, ref in repos.items():
    where = f"{repo.name} {ref}"
    try:
        text = read_project(repo, ref)
    except FileNotFoundError as e:
        report("MISSING", "CLAUDE.md", f"{where}: {e}")
        continue
    check(section(text, where), where, repo)

for arg in sys.argv[1:]:
    path = pathlib.Path(arg).expanduser().resolve()
    check(section(path.read_text(), str(path)), str(path), path.parent)

print("FAIL" if failed else "OK")
sys.exit(1 if failed else 0)
