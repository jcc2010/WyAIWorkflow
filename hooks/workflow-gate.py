#!/usr/bin/env python3
"""PreToolUse gate for ~/.claude/workflow/dev-workflow.md, in repos whose CLAUDE.md names it.

Bash `workflow-declare ...`: validate the declaration and record it for this session (and
    subagent, when agent_id is present), keyed by the repo's git common dir.
Bash `git commit`: refuse a message with no `Workflow:` trailer; refuse `none` on a file `none`
    does not cover, and `full` or `shrunk` with no declaration of that kind, or with neither
    `Fixes #N` nor `Bug: none`.
Bash `git stash`, `git add -A`, `git add .`, `git commit -a` from a subagent (agent_id present), in any repo:
    refuse (~/.claude/workflow/subagents.md).
Edit / Write / NotebookEdit: refuse until the session has declared; refuse full and shrunk on
    the integration branch (stage 2); under none, allow only the project's data paths.
Markdown, docs/, ~/.claude and files outside a workflow repo are never gated.

Limit: edits made through Bash (sed -i, heredocs) are not seen; the trailer and
the scorecard are the check on those, and the commit
gate checks the trailer against the files the commit takes. Fails open: any error here allows the call.

Allowed by design, with the audit as the backstop: a commit or declare whose repo can't be worked
out (cd "$VAR", cd -, git -C "$VAR"); -F - with no heredoc, and -F with an unreadable file. Not seen
at all: bash -c, eval, command git commit, git commit inside $(...) or after a shell keyword (then,
do), and pushd. -m "$VAR" is refused: the gate can't read the message."""
import ast, fcntl, functools, json, os, pathlib, re, shlex, subprocess, sys, tempfile, time, types

HOME = pathlib.Path.home()
STATE = HOME / ".claude/hooks/state/workflow"
VERDICTS = HOME / ".claude/review-verdicts.jsonl"
CHECK_NAMES = HOME / ".claude/workflow/check-names.py"
LATE = HOME / ".claude/workflow-late-declarations.jsonl"
TRAILER = re.compile(r"^Workflow: (full \(plan: \S+\)|shrunk [1-3](?:-[1-3])?(?:,[1-3](?:-[1-3])?)* \(.+\)|none \(.+\))\s*$", re.M)
BUG_MARKER = re.compile(r"^(Fixes #\d+|Bug: none)\s*$", re.M)
STAGES = re.compile(r"^[1-3](-[1-3])?(,[1-3](-[1-3])?)*$")
FORMS = ("workflow-declare full --plan <repo-relative plan path>   (plan checked by plan-reality-check, its verdict logged with \"plan\")\n"
         "workflow-declare shrunk 1-3 \"known fix: <one phrase>\"\n"
         "workflow-declare none \"<docs | data | archive | revert | merge>\"")


def log_late(data, repo, why, files=()):
    """One line for work the gate saw before any declaration. Never refuses: a refusal here would
    teach a session not to declare. The scorecard reads the counts."""
    try:  # a failed log must not turn the refusal that follows into an allow
        LATE.parent.mkdir(parents=True, exist_ok=True)
        with LATE.open("a") as f:
            f.write(json.dumps({"date": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "project": repo.name, "checkout": str(repo.top),
                                "session": data.get("session_id", ""), "why": why, "files": list(files)[:10]}) + "\n")
    except OSError:
        pass


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
REDIRECT = re.compile(r"&?(<<<|<<-|<<|>>|<>|>\||[<>]&?)")


def heredoc_body(s, i, word, dash):
    """(body, index after the terminator line) for a heredoc whose body starts at s[i]."""
    body = []
    while i < len(s):
        end = s.find("\n", i)
        end = len(s) if end < 0 else end
        line = s[i:end]
        i = end + 1
        if (line.lstrip("\t") if dash else line) == word:
            break
        body.append(line)
    return "\n".join(body), min(i, len(s))


def substitution_end(s, i):
    """The index just past the `)` closing a $( or <( whose contents start at s[i]."""
    depth, pending = 1, []
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
        elif c == "'":
            j = s.find("'", i + 1)
            i = len(s) if j < 0 else j + 1
        elif c == '"':
            i = double_quoted(s, i + 1)[1]
        elif c == "(":
            depth, i = depth + 1, i + 1
        elif c == ")":
            depth, i = depth - 1, i + 1
            if not depth:
                return i
        elif s.startswith("<<<", i):
            i += 3
        elif HEREDOC.match(s, i):
            m = HEREDOC.match(s, i)
            pending.append((m.group(2), m.group(0).startswith("<<-")))
            i = m.end()
        elif c == "\n":
            i += 1
            for word, dash in pending:
                i = heredoc_body(s, i, word, dash)[1]
            pending = []
        else:
            i += 1
    return i


def double_quoted(s, i):
    """(value, index past the closing quote) for a double-quoted string whose contents start at s[i].
    A substitution stays as written, so a heredoc inside one keeps its lines."""
    out = []
    while i < len(s) and s[i] != '"':
        if s[i] == "\\" and i + 1 < len(s):
            if s[i + 1] != "\n":
                out.append(s[i + 1] if s[i + 1] in '$`"\\' else s[i:i + 2])
            i += 2
        elif s.startswith("$(", i):
            j = substitution_end(s, i + 2)
            out.append(s[i:j])
            i = j
        else:
            out.append(s[i])
            i += 1
    return "".join(out), i + 1


def shell_commands(s):
    """The simple commands in s, in order, each with .tokens and .stdin (its heredoc and here-string
    text), with "(" and ")" between them where a subshell opens and closes."""
    out, cmd, word, target, pending, i = [], types.SimpleNamespace(tokens=[], stdin=[]), None, None, [], 0

    def end_word():
        nonlocal word, target
        if word is None:
            return
        if target == "here-string":
            cmd.stdin.append(word)
        elif target in ("<<", "<<-"):
            pending.append((word, target == "<<-", cmd))
        elif target is None:
            cmd.tokens.append(word)
        word, target = None, None

    def end_command():
        nonlocal cmd
        end_word()
        if cmd.tokens or cmd.stdin:
            out.append(cmd)
        cmd = types.SimpleNamespace(tokens=[], stdin=[])

    while i < len(s):
        c = s[i]
        if c == "\\":
            if s[i + 1:i + 2] != "\n":
                word = (word or "") + s[i + 1:i + 2]
            i += 2
        elif c == "'":
            j = s.find("'", i + 1)
            j = len(s) if j < 0 else j
            word = (word or "") + s[i + 1:j]
            i = j + 1
        elif c == '"':
            text, i = double_quoted(s, i + 1)
            word = (word or "") + text
        elif s.startswith(("$(", "<(", ">("), i):
            j = substitution_end(s, i + 2)
            word = (word or "") + s[i:j]
            i = j
        elif c == "`":
            j = s.find("`", i + 1)
            j = len(s) if j < 0 else j + 1
            word = (word or "") + s[i:j]
            i = j
        elif c in " \t":
            end_word()
            i += 1
        elif c == "#" and word is None:
            j = s.find("\n", i)
            i = len(s) if j < 0 else j
        elif c == "\n":
            end_command()
            i += 1
            for delimiter, dash, owner in pending:
                body, i = heredoc_body(s, i, delimiter, dash)
                owner.stdin.append(body)
            pending = []
        elif REDIRECT.match(s, i) and (c != "&" or s[i + 1:i + 2] == ">"):
            if word is not None and word.isdigit():  # 2>file: the 2 is not an argument
                word = None
            end_word()
            m = REDIRECT.match(s, i)
            op = m.group(1)
            target = "here-string" if op == "<<<" else op if op in ("<<", "<<-") else "drop"
            i = m.end()
        elif c in ";|&":
            end_command()
            i += 1
        elif c in "()":
            end_command()
            out.append(c)
            i += 1
        else:
            word = (word or "") + c
            i += 1
    end_command()
    return out


def segments(command, cwd0):
    """(command, cwd) for each simple command, following `cd`, and undoing it when a subshell ends.
    cwd is None once the directory can't be worked out."""
    cwd, opened = cwd0, []
    for item in shell_commands(command):
        if item == "(":
            opened.append(cwd)
        elif item == ")":
            cwd = opened.pop() if opened else cwd
        else:
            tokens = item.tokens
            while tokens and (tokens[0] == "{" or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0])):  # FOO=bar cmd
                tokens = tokens[1:]
            if not tokens or not tokens[0]:
                continue
            if tokens[0] == "cd":
                targets = [t for t in tokens[1:] if t == "-" or not t.startswith("-")]
                cwd = resolve(cwd, targets[0]) if targets else str(HOME)
                continue
            yield types.SimpleNamespace(tokens=tokens, stdin=item.stdin), cwd


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
    """base/sub, or None when a variable, a substitution, `cd -` or an unknown base hides it."""
    if sub is None:
        return base
    if sub == "-" or "$" in sub or "`" in sub:
        return None
    sub = os.path.expanduser(sub)
    if os.path.isabs(sub):
        return sub
    return os.path.join(base, sub) if base else None


def on_bash(data):
    command = data.get("tool_input", {}).get("command", "")
    cwd0 = data.get("cwd") or os.getcwd()
    for cmd, here in segments(command, cwd0):
        tokens = cmd.tokens
        if os.path.basename(tokens[0]) == "workflow-declare" and here:
            declare(data, tokens[1:], here)
        sub = git_subcommand(tokens)
        if sub and sub[0] == "commit":
            where = resolve(here, sub[1])
            if where:
                check_commit(data, cmd, sub[2], where)
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
    if name == "commit" and commit_options(rest).all:
        deny("Subagents never run git commit -a: it stages every modified tracked file, a "
             "peer's too. Name your paths: git commit <paths>.")


COMMIT_VALUE_SHORT = set("mFcCt")  # -m msg, -F file, ...: the rest of the cluster, or the next word, is the value
COMMIT_VALUE_LONG = {"--message", "--file", "--author", "--date", "--template", "--reuse-message",
                     "--reedit-message", "--fixup", "--squash", "--cleanup", "--trailer",
                     "--pathspec-from-file"}
REUSE = {"--no-edit", "-C", "-c", "--reuse-message", "--reedit-message", "--fixup", "--squash"}


def commit_options(args):
    """What a git commit's arguments say: .all, .paths, .paths_hidden (--pathspec-from-file),
    .messages (-m), .files (-F), .trailers and .reuse (the message is reused or generated)."""
    o = types.SimpleNamespace(all=False, paths=[], paths_hidden=False, messages=[], files=[], trailers=[], reuse=False)

    def note(name, value):
        o.reuse |= name in REUSE
        o.all |= name == "--all"
        o.paths_hidden |= name == "--pathspec-from-file"
        for names, into in ((("-m", "--message"), o.messages), (("-F", "--file"), o.files), (("--trailer",), o.trailers)):
            if name in names:
                into.append(value)

    i = 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            o.paths += args[i:]
            break
        if a.startswith("--"):
            name, eq, value = a.partition("=")
            if name in COMMIT_VALUE_LONG and not eq:
                value = args[i] if i < len(args) else ""
                i += 1
            note(name, value)
        elif a.startswith("-") and len(a) > 1:
            for j, c in enumerate(a[1:], 1):
                if c == "a":
                    o.all = True
                elif c in COMMIT_VALUE_SHORT:
                    value = a[j + 1:]
                    if not value:
                        value = args[i] if i < len(args) else ""
                        i += 1
                    note("-" + c, value)
                    break
                elif c in "uS":  # optional value, attached only
                    break
        elif a != "-":
            o.paths.append(a)
    return o


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
        first = declaration(data, repo) is None  # under the lock: parallel first declares log once
        state = load(f)
        state[str(repo.common)] = dict(decl, repo=str(repo.common.parent),
                                       at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        with tempfile.NamedTemporaryFile("w", dir=STATE, suffix=".tmp", delete=False) as tmp:
            tmp.write(json.dumps(state, indent=1))
        os.replace(tmp.name, f)
    if first:  # after the state is written, so a killed hook can't lose a declaration
        log_changed_code(data, repo)


def log_changed_code(data, repo):
    """Code already changed at a first declaration: a peer's in a shared checkout, so only logged.
    -z because git() strips a first line's leading status space; every untracked file, because a
    new folder otherwise reads as one path. Status never lists ignored files, so no check-ignore."""
    status = subprocess.run(["git", "--no-optional-locks", "-C", str(repo.top), "status", "--porcelain", "-z",
                             "--no-renames", "--untracked-files=all"],
                            capture_output=True, text=True, errors="replace").stdout
    dirty = [entry[3:] for entry in status.split("\0") if entry and not free_path(entry[3:])]
    if dirty:
        log_late(data, repo, "code already changed at the first declaration", dirty)


def committed_files(args, cwd):
    """Repo-relative files the commit takes, or None when git can't say (fail open)."""
    options = commit_options(args)
    paths = options.paths
    if options.paths_hidden:
        return None
    if paths:
        out = git(cwd, "diff", "--name-only", "--no-relative", "HEAD", "--", *paths)
        if out is not None and any(a in ("-i", "--include") for a in args):
            staged = git(cwd, "diff", "--cached", "--name-only", "--no-relative")
            out = None if staged is None else out + "\n" + staged
    elif options.all:
        out = git(cwd, "diff", "--name-only", "--no-relative", "HEAD")
    else:
        out = git(cwd, "diff", "--cached", "--name-only", "--no-relative")
    return None if out is None else sorted({f for f in out.splitlines() if f})


def free_path(rel):
    """Markdown or docs/: never needs a declaration."""
    rel = rel.replace(os.sep, "/")
    return rel.lower().endswith((".md", ".markdown")) or rel.split("/")[0] == "docs"


def none_covers(repo, rel, data=True):
    """True if a `none` declaration covers rel: Markdown, docs/, gitignored, and (data=True) the
    project's data paths. on_edit() uses data=False for the files that need no declaration."""
    rel = rel.replace(os.sep, "/")
    if free_path(rel):
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


def check_commit(data, cmd, args, cwd):
    options = commit_options(args)
    if options.reuse and not options.messages and not options.files:
        return  # the message is reused or generated, not written here
    repo = Repo.of(cwd)
    if repo is None:
        return
    message = options.messages + options.trailers  # only what becomes this commit's message counts
    for f in options.files:
        if f == "-":
            if not cmd.stdin:  # piped: can't read it, fail open
                return
            message += cmd.stdin
            continue
        path = resolve(cwd, f)
        if path is None:
            return
        try:
            message.append(pathlib.Path(path).read_text(errors="replace"))
        except OSError:
            return  # can't read it: fail open
    decl = declaration(data, repo)
    found = next((m for t in message for m in [TRAILER.search(t)] if m), None)
    if not found:  # never show a trailer template: a session that copies one skips the declaration
        if not decl:
            log_late(data, repo, "commit refused: nothing declared")
        if decl:
            deny("Refused: this repo follows ~/.claude/workflow/dev-workflow.md, so the commit message ends with "
                 "the trailer workflow-declare printed for it, on its own line:\n" + trailer_for(decl))
        deny(f"Refused: this repo follows ~/.claude/workflow/dev-workflow.md and nothing was declared here. Run "
             f"workflow-declare from inside {repo.top} first, then end the commit message with the "
             "trailer it prints:\n" + FORMS)
    kind = found.group(1).split()[0]
    if kind == "none":
        files = committed_files(args, cwd)
        code = [f for f in files or [] if not none_covers(repo, f)]
        if code:
            deny("Refused: the trailer says none, which covers Markdown, docs/, gitignored files and the "
                 "project's data paths, but this commit takes " + ", ".join(code[:10])
                 + (f" and {len(code) - 10} more" if len(code) > 10 else "")
                 + ". For code, declare full, or shrunk 1-3 for a known fix, and use the trailer it prints:\n" + FORMS)
        return
    if not decl:
        log_late(data, repo, "commit refused: nothing declared")
    if not decl or decl.get("kind") != kind:
        had = f"the declaration here is {decl['kind']}" if decl else "nothing was declared here"
        deny(f"Refused: the trailer says {kind}, but {had}. Declare it from inside {repo.top} and use "
             "the trailer it prints:\n" + FORMS)
    finishing = any(git(repo.top, "rev-parse", "-q", "--verify", h) is not None
                    for h in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"))  # the work was done elsewhere
    if repo.on_integration() and not finishing:
        deny(f"Refused: stage 2 says work in a worktree branch, and {repo.top} is on the integration "
             "branch. Move this work to one (the project's CLAUDE.md names the command), commit there, "
             "and land it the way the project's stage 7 says. Only none commits go straight here.")
    # After the declaration checks, so a session that hasn't declared never sees this. The audit,
    # not this hook, checks that #N exists: no network call here.
    if not any(BUG_MARKER.search(t) for t in message):
        deny("Refused: a full or shrunk commit also says whether it fixes a bug, on a line of its own: "
             "Fixes #N, naming the issue (labels: bug, and cause:<trap name> where the project has one), "
             "or Bug: none when it fixes no bug.")


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
                 "data paths the project's Workflow section lists. For code, declare full, or shrunk 1-3 for a known fix.")
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
