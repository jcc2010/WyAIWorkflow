#!/usr/bin/env python3
"""PreToolUse gate for ~/.claude/workflow/dev-workflow.md, in repos whose CLAUDE.md names it.

Bash `workflow-declare ...`: validate the declaration and record it for this session (and
    subagent, when agent_id is present), keyed by the repo's git common dir.
Bash `git commit`: refuse a message with no `Workflow:` trailer; refuse `none` on a file `none`
    does not cover, and `full` or `shrunk` with no declaration of that kind.
Bash `git stash`, `git add -A`, `git add .`, `git commit -a` from a subagent (agent_id present), in any repo:
    refuse (~/.claude/workflow/subagents.md).
Edit / Write / NotebookEdit: refuse until the session has declared; refuse full and shrunk on
    the integration branch (stage 2); under none, allow only the project's data paths.
Markdown, docs/, ~/.claude and files outside a workflow repo are never gated.

Limit: edits made through Bash (sed -i, heredocs) are not seen; the trailer and
the scorecard are the check on those, and the commit
gate checks the trailer against the files the commit takes. Fails open: any error here allows the call."""
import ast, fcntl, functools, json, os, pathlib, re, shlex, subprocess, sys, tempfile, time

HOME = pathlib.Path.home()
STATE = HOME / ".claude/hooks/state/workflow"
VERDICTS = HOME / ".claude/review-verdicts.jsonl"
CHECK_NAMES = HOME / ".claude/workflow/check-names.py"
TRAILER = re.compile(r"^Workflow: (full \(plan: \S+\)|shrunk [1-3](?:-[1-3])?(?:,[1-3](?:-[1-3])?)* \(.+\)|none \(.+\))\s*$", re.M)
STAGES = re.compile(r"^[1-3](-[1-3])?(,[1-3](-[1-3])?)*$")
FORMS = ("workflow-declare full --plan <repo-relative plan path>   (plan checked by plan-reality-check, its verdict logged with \"plan\")\n"
         "workflow-declare shrunk 1-3 \"known fix: <one phrase>\"\n"
         "workflow-declare none \"<docs | data | archive | revert | merge>\"")


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def git(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, errors="replace")
    return r.stdout.strip() if r.returncode == 0 else None


def existing_dir(path):
    p = pathlib.Path(path)
    p = p if p.is_dir() else p.parent
    while not p.exists() and p != p.parent:
        p = p.parent
    return p


class Repo:
    """The checkout holding `path`, or None outside a workflow repo."""

    def __init__(self, top, common):
        self.top, self.common = pathlib.Path(top).resolve(), pathlib.Path(common).resolve()
        self.name = self.common.parent.name  # the main checkout's directory: the verdict log's project

    @classmethod
    def of(cls, path):
        d = existing_dir(path)
        top = git(d, "rev-parse", "--show-toplevel")
        common = git(d, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if not top or not common:
            return None
        repo = cls(top, common)
        if repo.listed_ref():  # listed in PROJECTS, even when this checkout's CLAUDE.md is stale
            return repo
        try:
            return repo if "dev-workflow.md" in (repo.top / "CLAUDE.md").read_text(errors="replace") else None
        except OSError:
            return None

    def listed_ref(self):
        """The integration ref check-names.py's PROJECTS gives this repo, or None."""
        return projects().get(self.common.parent)

    def integration_ref(self):
        return self.listed_ref() or "main"

    def on_integration(self):
        ref = self.integration_ref()
        branch = git(self.top, "branch", "--show-current")
        if not branch:  # mid-rebase HEAD is detached at the onto commit; the branch is in head-name
            gitdir = pathlib.Path(git(self.top, "rev-parse", "--path-format=absolute", "--git-dir") or "")
            for d in ("rebase-merge", "rebase-apply"):
                try:
                    branch = (gitdir / d / "head-name").read_text().strip().removeprefix("refs/heads/")
                    break
                except OSError:
                    pass
        if branch:
            return branch == ref.split("/", 1)[-1] if ref.startswith("origin/") else branch == ref
        head, tip = git(self.top, "rev-parse", "HEAD"), git(self.top, "rev-parse", ref)
        return head is not None and head == tip  # detached at the integration tip

    def data_paths(self):
        """Backticked paths on a `Data paths` line of the Workflow section."""
        try:
            text = (self.top / "CLAUDE.md").read_text(errors="replace")
        except OSError:
            return []
        m = re.search(r"^## Workflow[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        line = re.search(r"^\s*-?\s*Data paths[^\n]*", m.group(1), re.M) if m else None
        return [p.strip("/") for p in re.findall(r"`([^`]+)`", line.group(0))] if line else []


@functools.lru_cache(maxsize=None)
def projects():
    """check-names.py's PROJECTS as {resolved main checkout: integration ref}."""
    try:
        for node in ast.parse(CHECK_NAMES.read_text()).body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PROJECTS":
                return {(HOME / path).resolve(): ref for path, ref in ast.literal_eval(node.value).items()}
    except (OSError, SyntaxError, ValueError):
        pass
    return {}


def state_file(session, agent=None):
    safe = lambda s: re.sub(r"[^A-Za-z0-9_-]", "_", s)
    return STATE / (safe(session) + (f"__{safe(agent)}" if agent else "") + ".json")


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def declaration(data, repo):
    """This agent's declaration for the repo, else its parent session's."""
    session, agent = data.get("session_id", ""), data.get("agent_id")
    for f in ([state_file(session, agent)] if agent else []) + [state_file(session)]:
        d = load(f).get(str(repo.common))
        if d:
            return d
    return None


HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def strip_heredocs(command):
    """The command with heredoc bodies removed, so text inside them is never run as a command."""
    out, lines, i = [], command.split("\n"), 0
    while i < len(lines):
        out.append(lines[i])
        words = [m.group(2) for m in HEREDOC.finditer(lines[i])]
        i += 1
        for word in words:
            while i < len(lines) and lines[i].strip() != word:
                i += 1
            if i < len(lines):
                out.append(lines[i])  # keep the terminator line: it may carry `)"` and more
                i += 1
    return "\n".join(out)


def segments(command, cwd0):
    """(tokens, cwd) for each simple command, following `cd` between them."""
    cwd = cwd0
    for raw in re.split(r"&&|\|\||;|\||\n", strip_heredocs(command)):
        try:
            tokens = shlex.split(raw)
        except ValueError:  # e.g. the first line of -m "$(cat <<'EOF' ... EOF)"
            tokens = raw.split()
        tokens = [t for t in tokens if t not in ("(", "{")]
        if tokens and tokens[0][:1] in "({":  # (cd x && ...) or { cd x; ... }
            tokens[0] = tokens[0].lstrip("({")
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):  # FOO=bar cmd
            tokens = tokens[1:]
        if not tokens or not tokens[0]:
            continue
        if tokens[0] == "cd" and len(tokens) > 1:
            cwd = resolve(cwd, tokens[1])
            continue
        yield tokens, cwd


def git_subcommand(tokens):
    """('commit', cwd_override, rest) for `git [-C dir] [-c k=v] commit ...`, else None."""
    if os.path.basename(tokens[0]) != "git":
        return None
    i, cdir = 1, None
    while i < len(tokens) and tokens[i].startswith("-"):
        if tokens[i] in ("-C", "-c", "--git-dir", "--work-tree") and i + 1 < len(tokens):
            if tokens[i] == "-C":
                cdir = resolve(cdir, tokens[i + 1]) if cdir else tokens[i + 1]
            i += 2
        else:
            i += 1
    return (tokens[i], cdir, tokens[i + 1:]) if i < len(tokens) else None


def resolve(base, sub):
    if sub is None:
        return base
    sub = os.path.expanduser(sub)
    return sub if os.path.isabs(sub) else os.path.join(base, sub)


def on_bash(data):
    command = data.get("tool_input", {}).get("command", "")
    cwd0 = data.get("cwd") or os.getcwd()
    for tokens, here in segments(command, cwd0):
        if os.path.basename(tokens[0]) == "workflow-declare":
            declare(data, tokens[1:], here)
        sub = git_subcommand(tokens)
        if sub and sub[0] == "commit":
            check_commit(data, command, sub[2], resolve(here, sub[1]))
        if sub and data.get("agent_id"):
            subagent_git(*sub)


def subagent_git(name, cdir, rest):
    """A subagent never stashes (shared across worktrees) or sweeps the tree into a commit."""
    if name == "stash" and not (rest and rest[0] in ("list", "show")):
        deny("Subagents never run git stash: the stash is shared across worktrees, and a pop "
             "can apply a peer's stash. Commit your work, or report it as a blocker.")
    if name == "add" and any(a in ("-A", "--all", ".", "./") for a in rest):
        deny("Subagents never run git add -A or git add .: in a shared checkout they sweep in a "
             "peer's files. Name your paths: git commit <paths>.")
    if name == "commit" and commit_all(rest):
        deny("Subagents never run git commit -a: it stages every modified tracked file, a "
             "peer's too. Name your paths: git commit <paths>.")


COMMIT_VALUE_SHORT = set("mFcCt")  # -m msg, -F file, ...: the rest of the cluster, or the next word, is the value
COMMIT_VALUE_LONG = {"--message", "--file", "--author", "--date", "--template", "--reuse-message",
                     "--reedit-message", "--fixup", "--squash", "--cleanup", "--trailer",
                     "--pathspec-from-file"}


def commit_all(args):
    """True for git commit -a / --all, alone or in a short cluster (-am); never --amend or --author."""
    i = 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            return False
        if a == "--all":
            return True
        if a in COMMIT_VALUE_LONG:
            i += 1
        elif a.startswith("-") and not a.startswith("--"):
            for j, c in enumerate(a[1:], 1):
                if c == "a":
                    return True
                if c in COMMIT_VALUE_SHORT:
                    if j == len(a) - 1:
                        i += 1  # value is the next word
                    break
                if c in "uS":  # optional value, attached only
                    break
    return False


def declare(data, args, cwd):
    repo = Repo.of(cwd)
    if repo is None:
        return  # outside a workflow repo the script just prints
    kind = args[0] if args else ""
    if kind == "full":
        if len(args) < 3 or args[1] != "--plan":
            deny("Refused: " + FORMS)
        plan = args[2]
        if plan.startswith("/") or re.search(r"\s", plan):
            deny("Refused: the plan path must be repo-relative, with no spaces.")
        if not (repo.top / plan).is_file():
            deny(f"Refused: no plan at {plan} in {repo.top}. Write it first (stage 3); Markdown is never gated.")
        key = os.path.normpath(plan)
        checked = False
        for line in VERDICTS.read_text().splitlines() if VERDICTS.exists() else []:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if ("plan-reality-check" in str(row.get("agent", "")) and row.get("project") in (repo.name, repo.top.name)
                    and os.path.normpath(str(row.get("plan", ""))) == key):
                checked = True
        if not checked:
            deny(f"Refused: no plan-reality-check verdict for {plan} in {VERDICTS}. Dispatch "
                 f"plan-reality-check (stage 3), then log one line with \"agent\": \"plan-reality-check\", "
                 f"\"project\": \"{repo.name}\", \"plan\": \"{plan}\". For a known fix, declare shrunk 1-3 instead.")
        decl = {"kind": "full", "plan": plan}
    elif kind == "shrunk":
        if len(args) < 3 or not STAGES.match(args[1]) or not args[2].strip():
            deny("Refused: stages 4-9 don't shrink; shrunk takes stages 1-3 and a reason.\n" + FORMS)
        decl = {"kind": "shrunk", "stages": args[1], "why": args[2]}
    elif kind == "none":
        if len(args) < 2 or not args[1].strip():
            deny("Refused: none needs a reason.\n" + FORMS)
        decl = {"kind": "none", "why": args[1]}
    else:
        deny("Refused: " + FORMS)
    f = state_file(data.get("session_id", ""), data.get("agent_id"))
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / ".lock", "w") as lock:  # parallel declares in one session must not lose one
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load(f)
        state[str(repo.common)] = dict(decl, repo=str(repo.common.parent),
                                       at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        with tempfile.NamedTemporaryFile("w", dir=STATE, suffix=".tmp", delete=False) as tmp:
            tmp.write(json.dumps(state, indent=1))
        os.replace(tmp.name, f)


def commit_paths(args):
    """The pathspecs a git commit names, or None if --pathspec-from-file hides them."""
    paths, i = [], 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            return paths + args[i:]
        if a == "--pathspec-from-file" or a.startswith("--pathspec-from-file="):
            return None
        if a in COMMIT_VALUE_LONG:
            i += 1
        elif a.startswith("-") and not a.startswith("--") and len(a) > 1:
            for j, c in enumerate(a[1:], 1):
                if c in COMMIT_VALUE_SHORT:
                    if j == len(a) - 1:
                        i += 1
                    break
                if c in "uS":
                    break
        elif not a.startswith("-"):
            paths.append(a)
    return paths


def whole_commit_args(command):
    """The args of the one git commit in command, parsed whole: a quoted multi-line -m spans the
    segments segments() splits on, and a pathspec after it would be lost. None if not exactly one."""
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return None
    found, run = [], []
    for t in tokens + [";"]:
        if t and set(t) <= set("();<>|&"):  # an operator or redirection ends the simple command
            sub = git_subcommand(run) if run else None
            if sub and sub[0] == "commit":
                found.append(sub[2])
            run = []
        else:
            run.append(t)
    return found[0] if len(found) == 1 else None


def committed_files(args, cwd):
    """Repo-relative files the commit takes, or None when git can't say (fail open)."""
    paths = commit_paths(args)
    if paths is None:
        return None
    if paths:
        out = git(cwd, "diff", "--name-only", "--no-relative", "HEAD", "--", *paths)
        if out is not None and any(a in ("-i", "--include") for a in args):
            staged = git(cwd, "diff", "--cached", "--name-only", "--no-relative")
            out = None if staged is None else out + "\n" + staged
    elif commit_all(args):
        out = git(cwd, "diff", "--name-only", "--no-relative", "HEAD")
    else:
        out = git(cwd, "diff", "--cached", "--name-only", "--no-relative")
    return None if out is None else sorted({f for f in out.splitlines() if f})


def none_covers(repo, rel, data=True):
    """True if a `none` declaration covers rel: Markdown, docs/, gitignored, and (data=True) the
    project's data paths. on_edit() uses data=False for the files that need no declaration."""
    rel = rel.replace(os.sep, "/")
    if rel.lower().endswith((".md", ".markdown")) or rel.split("/")[0] == "docs":
        return True
    if git(repo.top, "check-ignore", "-q", "--", rel) is not None:  # .env, local config: not repo work
        return True
    return data and any(rel == p or rel.startswith(p + "/") for p in repo.data_paths())


def trailer_for(decl):
    """The trailer workflow-declare printed for decl."""
    if decl["kind"] == "full":
        return f"Workflow: full (plan: {decl['plan']})"
    if decl["kind"] == "shrunk":
        return f"Workflow: shrunk {decl['stages']} ({decl['why']})"
    return f"Workflow: none ({decl['why']})"


def check_commit(data, command, args, cwd):
    reuse = ("--no-edit", "-C", "-c", "--fixup", "--squash", "--reuse-message", "--reedit-message")
    if any(a in reuse or a.startswith(("--fixup=", "--squash=", "--reuse-message=", "--reedit-message="))
           for a in args):  # the message is reused or generated, not written here
        return
    repo = Repo.of(cwd)
    if repo is None:
        return
    message = command
    for i, a in enumerate(args):
        f = args[i + 1] if a in ("-F", "--file") and i + 1 < len(args) else (a[7:] if a.startswith("--file=") else None)
        if f and f != "-":
            try:
                message += "\n" + pathlib.Path(resolve(cwd, f)).read_text(errors="replace")
            except OSError:
                return  # can't read it: fail open
    try:  # a quoted multi-line -m message is one token of the whole command
        whole = shlex.split(command)
    except ValueError:
        whole = []
    attached = [a[2:] for a in args if a.startswith("-m") and len(a) > 2]  # -m"..."
    decl = declaration(data, repo)
    found = next((m for t in [message, *args, *whole, *attached] for m in [TRAILER.search(t)] if m), None)
    if not found:  # never show a trailer template: a session that copies one skips the declaration
        if decl:
            deny("Refused: this repo follows ~/.claude/workflow/dev-workflow.md, so the commit message ends with "
                 "the trailer workflow-declare printed for it, on its own line:\n" + trailer_for(decl))
        deny(f"Refused: this repo follows ~/.claude/workflow/dev-workflow.md and nothing was declared here. Run "
             f"workflow-declare from inside {repo.top} first, then end the commit message with the "
             "trailer it prints:\n" + FORMS)
    kind = found.group(1).split()[0]
    if kind == "none":
        files = committed_files(whole_commit_args(command) or args, cwd)
        code = [f for f in files or [] if not none_covers(repo, f)]
        if code:
            deny("Refused: the trailer says none, which covers Markdown, docs/, gitignored files and the "
                 "project's data paths, but this commit takes " + ", ".join(code[:10])
                 + (f" and {len(code) - 10} more" if len(code) > 10 else "")
                 + ". For code, declare shrunk 1-3 or full, and use the trailer it prints:\n" + FORMS)
        return
    if not decl or decl.get("kind") != kind:
        had = f"the declaration here is {decl['kind']}" if decl else "nothing was declared here"
        deny(f"Refused: the trailer says {kind}, but {had}. Declare it from inside {repo.top} and use "
             "the trailer it prints:\n" + FORMS)


def on_edit(data):
    ti = data.get("tool_input", {})
    path = ti.get("file_path") or ti.get("notebook_path")
    if not path:
        return
    path = os.path.realpath(os.path.expanduser(path))  # /var vs /private/var, symlinked checkouts
    if path.lower().endswith((".md", ".markdown")) or path.startswith(str(HOME / ".claude") + os.sep):
        return
    repo = Repo.of(path)
    if repo is None:
        return
    rel = os.path.relpath(path, repo.top)
    if none_covers(repo, rel, data=False):
        return
    decl = declaration(data, repo)
    if decl is None:
        deny(f"Declare first: this repo follows ~/.claude/workflow/dev-workflow.md. Run one of these from inside "
             f"{repo.top} (e.g. cd {shlex.quote(str(repo.top))} && workflow-declare ...); Markdown and "
             "docs/ are free, so write the plan first:\n" + FORMS)
    if decl["kind"] == "none":
        if not none_covers(repo, rel):
            deny(f"Refused: declared none ({decl.get('why')}), which covers Markdown, docs/ and the "
                 "data paths the project's Workflow section lists. For code, declare full or shrunk 1-3.")
        return
    if repo.on_integration():
        deny(f"Refused: stage 2 says work in a worktree branch, and {repo.top} is on the integration "
             "branch. Create the project's worktree (its CLAUDE.md names the command) and edit there.")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    tool = data.get("tool_name")
    if tool == "Bash":
        on_bash(data)
    elif tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        on_edit(data)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # never block work on a bug here
        print(f"workflow-gate: allowed after an internal error: {e!r}", file=sys.stderr)
    sys.exit(0)
