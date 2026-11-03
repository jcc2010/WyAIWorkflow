#!/usr/bin/env python3
"""Monthly workflow scorecard: one reading a month, so a workflow change can be judged by the
next month's numbers. Read-only on every repo.

    scorecard.py                   the previous calendar month
    scorecard.py --month 2026-10   a given month
    scorecard.py --no-record       print the report to stdout; write no report and no history

Writes ~/.claude/skill-update-reports/scorecard-<YYYY-MM>.md and appends one JSON line to
~/.claude/workflow-metrics.jsonl (the history outlives otelcol's ~10 days of log rotation).

Per project in check-names.py's PROJECTS:
  cost      claude-cost spend over the part of the month the log covers, divided by non-merge
            commits on the integration ref in that same span; share of it from >400k contexts
  churn     of lines added by commits in the month shifted back 14 days (so every commit's
            window has closed), the share no longer blamed to that commit 14 days later
  traps     new TRAPS_DIR/*.md files added in the month (repeated traps cannot be
            detected reliably from commit text, so this counts new ones instead)
  reviews   from ~/.claude/review-verdicts.jsonl, which review dispatchers append to
  trailers  each month commit's `Workflow:` trailer (full, shrunk, none, missing); for full, whether
            its plan exists at that commit and has a plan-reality-check line naming it; for full
            and shrunk, whether the body quotes a failing run (a rough grep). Self-reported, so
            the cross-checks are the point; the first month (Nov 2026) is a baseline only.

One developer and noisy numbers: only large effects will show. The report sets each reading
beside the previous month's and the CHANGELOG entries in between; it never claims cause."""
import argparse, ast, collections, concurrent.futures, datetime as dt, importlib.machinery, importlib.util, json, os, pathlib, re, subprocess

HOME = pathlib.Path.home()
HERE = pathlib.Path(__file__).resolve().parent
REPORTS = HOME / ".claude/skill-update-reports"
HISTORY = HOME / ".claude/workflow-metrics.jsonl"
VERDICTS = HOME / ".claude/review-verdicts.jsonl"
TRAPS_DIR = "docs/knowledge/traps"  # where a project records one file per trap; "new traps" counts files added here
CHURN_DAYS = 14
BIG_CONTEXT = 400_000
UTC = dt.timezone.utc


def load_claude_cost():
    # bin/claude-cost beside this file, else the copy on your PATH (~/.local/bin)
    path = next((p for p in (HERE / "bin/claude-cost", HOME / ".local/bin/claude-cost") if p.is_file()),
                HERE / "bin/claude-cost")
    loader = importlib.machinery.SourceFileLoader("claude_cost", str(path))
    spec = importlib.util.spec_from_loader("claude_cost", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def projects():
    """PROJECTS from check-names.py, read without running it."""
    tree = ast.parse((HERE / "check-names.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PROJECTS":
            return ast.literal_eval(node.value)
    raise SystemExit("no PROJECTS in check-names.py")


def transcript_dir(path):
    """~/.claude/projects folder name Claude Code uses for a checkout path."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(HOME / path))


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, errors="replace").stdout


def commits(repo, ref, start, end):
    """(sha, time) of non-merge commits on ref with committer time in [start, end)."""
    out = git(repo, "log", ref, "--no-merges", "--format=%H %ct",
              f"--since={int(start.timestamp())}", f"--until={int(end.timestamp())}")
    rows = [line.split() for line in out.splitlines()]
    return [(sha, dt.datetime.fromtimestamp(int(t), UTC)) for sha, t in rows
            if start <= dt.datetime.fromtimestamp(int(t), UTC) < end]


def churn(repo, ref, start, end, now):
    """(added, churned, files skipped) for commits in [start, end) whose 14-day window has closed.

    For each day's commits, blame each touched file once at the last commit on ref before
    day + 14 days and count the lines still attributed to each of those commits."""
    by_day = collections.defaultdict(list)
    for sha, t in commits(repo, ref, start, end):
        if t + dt.timedelta(days=CHURN_DAYS) <= now:
            by_day[t.date()].append(sha)
    jobs = []  # (day, snapshot, path, {sha: lines added})
    for day, shas in sorted(by_day.items()):
        cutoff = dt.datetime.combine(day, dt.time(), UTC) + dt.timedelta(days=CHURN_DAYS + 1)
        snap = git(repo, "rev-list", "-1", f"--before={int(cutoff.timestamp())}", ref).strip()
        files = collections.defaultdict(dict)
        for sha in shas:
            for line in git(repo, "show", "--numstat", "--format=", "--no-renames", sha).splitlines():
                plus, _, path = line.split("\t", 2)
                if plus != "-" and int(plus):
                    files[path][sha] = int(plus)
        jobs += [(day, snap, path, per_commit) for path, per_commit in files.items()]

    def blame(job):
        day, snap, path, per_commit = job
        # --since stops blame a day before: older lines are boundary lines, never counted. A bare
        # date would mean that date at the current time of day and cut off the morning's commits.
        since = f"{(day - dt.timedelta(days=1)).isoformat()} 00:00:00 +0000"
        run = subprocess.run(["git", "-C", str(repo), "blame", "-s", "-l", f"--since={since}",
                              snap, "--", path], capture_output=True, text=True, errors="replace")
        if run.returncode:  # gone or renamed by the snapshot: can't tell churn from a move
            return None
        alive = collections.Counter(line[:40] for line in run.stdout.splitlines())
        return sum(per_commit.values()), sum(max(0, n - alive[sha]) for sha, n in per_commit.items())

    added = churned = skipped = 0
    with concurrent.futures.ThreadPoolExecutor(8) as pool:  # one blame is ~1s, mostly waiting
        for result in pool.map(blame, jobs):
            if result is None:
                skipped += 1
            else:
                added += result[0]
                churned += result[1]
    return added, churned, skipped


def new_traps(repo, ref, start, end):
    out = git(repo, "log", ref, "--diff-filter=A", "--name-only", "--format=",
              f"--since={int(start.timestamp())}", f"--until={int(end.timestamp())}",
              "--", TRAPS_DIR + "/")
    return len({p for p in out.splitlines() if p.endswith(".md")})


TRAILER = re.compile(r"^Workflow: (full \(plan: (\S+)\)|shrunk [1-3](?:-[1-3])?(?:,[1-3](?:-[1-3])?)* \(.+\)|none \(.+\))\s*$", re.M)
RED_RUN = re.compile(r"red run|FAIL|failed as expected|Tests: .*failed")


def plan_key(path):
    """A repo-relative plan path in one spelling, so `./docs/p.md` and `docs/p.md` match."""
    return os.path.normpath(str(path).strip())


def checked_plans(project):
    """Plan paths a plan-reality-check line in the verdict log names for this project."""
    out = set()
    for line in VERDICTS.read_text().splitlines() if VERDICTS.exists() else []:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if "plan-reality-check" in str(row.get("agent", "")) and row.get("project") == project and row.get("plan"):
            out.add(plan_key(row["plan"]))
    return out


def trailers(repo, ref, start, end):
    out = collections.Counter()
    plans = checked_plans(repo.name)
    log = git(repo, "log", ref, "--no-merges", "--format=%H%x00%B%x1e",
              f"--since={int(start.timestamp())}", f"--until={int(end.timestamp())}")
    for entry in filter(str.strip, log.split("\x1e")):
        sha, _, body = entry.strip().partition("\0")
        m = TRAILER.search(body)
        kind = m.group(1).split()[0] if m else "missing"
        out[kind] += 1
        if kind == "full":
            plan = m.group(2)
            out["full_plan_exists"] += subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}:{plan}"],
                                                      capture_output=True).returncode == 0
            out["full_plan_checked"] += plan_key(plan) in plans
        if kind in ("full", "shrunk"):
            out["red_quoted"] += bool(RED_RUN.search(body))
    return dict(out)


def reviews(start, end):
    """agent -> [n, flagged, findings, hook]; flagged = verdict polish/rework/fix first,
    findings = summed counts, hook = lines log-review-verdict.py wrote."""
    out = collections.defaultdict(lambda: [0, 0, 0, 0])
    if not VERDICTS.exists():
        return out
    for line in VERDICTS.read_text().splitlines():
        try:
            row = json.loads(line)
            when = dt.datetime.fromisoformat(row["date"])
            when = when.replace(tzinfo=UTC) if when.tzinfo is None else when.astimezone(UTC)
            count = int(row.get("count", 0) or 0)
        except (ValueError, KeyError, TypeError):
            print(f"warning: skipped a bad line in {VERDICTS}: {line[:80]}")
            continue
        if start <= when < end:
            agg = out[row.get("agent", "?")]
            agg[0] += 1
            agg[1] += row.get("verdict") in ("polish", "rework", "fix first")
            agg[2] += count
            agg[3] += row.get("source") == "hook"
    return out


def changelog_between(after, until):
    """CHANGELOG headings dated in (after, until]."""
    out = []
    for m in re.finditer(r"^## (\d{4}-\d{2}-\d{2}) — (.+)$", (HERE / "CHANGELOG.md").read_text(), re.M):
        day = dt.date.fromisoformat(m.group(1))
        if (after is None or day > after) and day <= until:
            out.append(f"{m.group(1)} {m.group(2)}")
    return out


def covered(reading):
    """Seconds of cost log a reading covers; 0 when it had none or it can't be read."""
    try:
        span = reading.get("cost_span")
        return (dt.datetime.fromisoformat(span[1]) - dt.datetime.fromisoformat(span[0])).total_seconds()
    except (TypeError, ValueError, IndexError, AttributeError):
        return 0


def record(reading):
    """Put the reading in the history, one line per month, sorted, written atomically.

    A rerun replaces its month's line unless it covers less cost time: the otelcol log keeps
    about 10 days, so a late rerun would otherwise swap a real reading for spend 0. Returns the
    reading the history now holds for the month, so the report can match it."""
    rows, bad = {}, []
    for line in HISTORY.read_text().splitlines() if HISTORY.exists() else []:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row["month"], str):  # sorted() would fail on a mix of types
                raise TypeError
            rows[row["month"]] = row, line
        except (ValueError, KeyError, TypeError):
            bad.append(line)  # kept as it was, in order; the reader warns about it
    old = rows.get(reading["month"])
    if old and covered(old[0]) > covered(reading):
        print(f"kept the existing {reading['month']} line: it covers more cost time than this run")
        return dict(old[0], kept=True)
    rows[reading["month"]] = reading, json.dumps(reading)
    tmp = HISTORY.with_suffix(".jsonl.tmp")
    with tmp.open("w") as f:
        f.write("".join(line + "\n" for line in bad + [rows[m][1] for m in sorted(rows)]))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, HISTORY)  # a kill mid-write leaves the old file whole
    return reading


def month_bounds(label):
    start = dt.datetime.strptime(label, "%Y-%m").replace(tzinfo=UTC)
    end = (start + dt.timedelta(days=32)).replace(day=1)
    return start, end


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    last = (dt.datetime.now(UTC).replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    ap.add_argument("--month", default=last)
    ap.add_argument("--no-record", action="store_true")
    args = ap.parse_args()
    now = dt.datetime.now(UTC)
    start, end = month_bounds(args.month)

    cc = load_claude_cost()
    reqs = [r for r in cc.load(start) if r["t"] < end]
    folders = {f.stem: f.parent.name for f in (HOME / ".claude/projects").glob("*/*.jsonl")}
    span = (reqs[0]["t"], reqs[-1]["t"]) if reqs else None
    partial = not span or span[0] - start > dt.timedelta(days=1) or end - span[1] > dt.timedelta(days=1)

    dirs = {transcript_dir(p): p for p in projects()}

    def owner(session):  # a project's worktree sessions live in "<its folder>--claude-worktrees-…"
        folder = folders.get(session, "")
        return next((p for d, p in dirs.items() if folder == d or folder.startswith(d + "--")), None)

    spend, big = collections.Counter(), collections.Counter()
    for r in reqs:
        p = owner(r["session"])
        spend[p] += r["cost"]
        if cc.context(r) >= BIG_CONTEXT:
            big[p] += r["cost"]
    total = sum(r["cost"] for r in reqs)
    idle = sum(r["cost"] for r, gap in cc.rebuilds(reqs) if r["main"] and gap >= 60)

    rows = {}
    for path, ref in projects().items():
        repo = HOME / path
        if not repo.is_dir():
            continue
        cost_commits = len(commits(repo, ref, *span)) if span else 0
        shift = dt.timedelta(days=CHURN_DAYS)
        added, churned, skipped = churn(repo, ref, start - shift, end - shift, now)
        rows[path] = dict(
            spend=round(spend[path], 2), commits_in_cost_span=cost_commits,
            cost_per_commit=round(spend[path] / cost_commits, 2) if cost_commits else None,
            big_context_share=round(big[path] / spend[path], 3) if spend[path] else None,
            commits_in_month=len(commits(repo, ref, start, end)),
            churn_added=added, churn_lines=churned, churn_files_skipped=skipped,
            churn_share=round(churned / added, 3) if added else None,
            new_traps=new_traps(repo, ref, start, end) if (repo / TRAPS_DIR).is_dir() else None,
            trailers=trailers(repo, ref, start, end))
    unassigned = round(sum(c for p, c in spend.items() if p is None), 2)
    review_rows = {a: dict(n=n, flagged=f, findings=k, hook=h) for a, (n, f, k, h) in reviews(start, end).items()}

    previous = None
    if HISTORY.exists():
        for line in HISTORY.read_text().splitlines():
            try:
                row = json.loads(line)
                if row["month"] < args.month and (not previous or row["month"] > previous["month"]):
                    previous = row
            except (ValueError, KeyError, TypeError):
                print(f"warning: skipped a bad line in {HISTORY}: {line[:80]}")
    reading = dict(month=args.month, taken=now.isoformat(timespec="seconds"), partial=partial,
                   cost_span=[t.isoformat(timespec="minutes") for t in span] if span else None,
                   total_spend=round(total, 2), unassigned_spend=unassigned,
                   big_context_share=round(sum(big.values()) / total, 3) if total else None,
                   idle_rebuild_share=round(idle / total, 3) if total else None,
                   projects=rows, reviews=review_rows)
    if not args.no_record:  # first, so the report shows whichever reading the history kept
        reading = record(reading)
        rows, review_rows = reading["projects"], reading["reviews"]
        unassigned, partial = reading["unassigned_spend"], reading["partial"]

    def vs(key, project=None):
        show = lambda v: "n/a" if v is None else v
        now_v = (rows[project] if project else reading).get(key)
        if not previous:
            return f"{show(now_v)}"
        prev_v = (previous["projects"].get(project, {}) if project else previous).get(key)
        return f"{show(now_v)} (was {show(prev_v)})"

    prev_day = dt.date.fromisoformat(previous["month"] + "-01") if previous else None
    lines = [f"# Workflow scorecard, {args.month} (UTC month bounds)", "",
             (f"**This rerun covered less cost time, so the history kept the reading taken "
              f"{reading['taken']}; it is shown here.** " if reading.get("kept") else "") +
             f"Taken {reading['taken']}. " + ("**Partial:** the cost log covers only "
             f"{reading['cost_span'][0]} to {reading['cost_span'][1]}." if partial and reading["cost_span"] else
             "**Partial: no cost data.**" if partial else "Cost covers the whole month."),
             "One developer and noisy numbers: only large effects show. Readings sit beside the "
             "workflow changes that landed in between; that is coincidence in time, not cause.", "",
             f"Spend ${vs('total_spend')}; >400k-context share {vs('big_context_share')}; "
             f"main-session cache rebuilds after >60 min idle {vs('idle_rebuild_share')}; "
             f"spend in sessions outside the listed projects ${unassigned}.", "",
             "| Project | Spend | $/commit | >400k share | Commits (month) | Churn | New traps |",
             "|---|---|---|---|---|---|---|"]
    for p in rows:
        lines.append(f"| {p.split('/')[-1]} | {vs('spend', p)} | {vs('cost_per_commit', p)} | "
                     f"{vs('big_context_share', p)} | {vs('commits_in_month', p)} | {vs('churn_share', p)} | "
                     f"{vs('new_traps', p)} |")
    lines += ["", f"$/commit divides spend by commits in the cost span only. Churn covers commits dated "
              f"{(start - dt.timedelta(days=CHURN_DAYS)).date()} to {(end - dt.timedelta(days=CHURN_DAYS + 1)).date()} "
              "UTC (the month shifted back 14 days, so every window has closed); each commit's lines are "
              "checked 14 to 15 days later (at the end of the 14th day after its UTC date). Files gone "
              "or renamed by then are skipped.", "",
              "## Review hit rate", ""]
    lines += ([f"- {a}: {r['n']} reviews ({r.get('hook', 0)} logged by hook), {r['flagged']} flagged "
               f"(polish, rework or fix first), {r['findings']} findings"
               for a, r in review_rows.items()] or ["No data: nothing logged to review-verdicts.jsonl this month."])
    lines += ["", "## Workflow trailers", "",
              "Self-reported in each commit. `shrunk` is the open door: watch its share beside the "
              "red-run rate, since stage 4 applies either way. Baseline only until Dec 2026.", "",
              "| Project | Commits | full | shrunk | none | missing | full: plan exists / checked | full+shrunk quoting a red run |",
              "|---|---|---|---|---|---|---|---|"]
    for p, r in rows.items():
        if "trailers" not in r:  # a history line from before trailers were counted
            lines.append(f"| {p.split('/')[-1]} | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        t = r["trailers"]
        n = sum(t.get(k, 0) for k in ("full", "shrunk", "none", "missing"))
        lines.append(f"| {p.split('/')[-1]} | {n} | {t.get('full', 0)} | {t.get('shrunk', 0)} | {t.get('none', 0)} | "
                     f"{t.get('missing', 0)} | {t.get('full_plan_exists', 0)} / {t.get('full_plan_checked', 0)} | "
                     f"{t.get('red_quoted', 0)} of {t.get('full', 0) + t.get('shrunk', 0)} |")
    lines += ["", "## Workflow changes since the previous reading", ""]
    lines += [f"- {c}" for c in changelog_between(prev_day, (end - dt.timedelta(days=1)).date())] or ["- none"]

    if args.no_record:  # a test run must not replace the month's recorded report
        print("\n".join(lines))
        return
    REPORTS.mkdir(parents=True, exist_ok=True)
    report = REPORTS / f"scorecard-{args.month}.md"
    report.write_text("\n".join(lines) + "\n")
    print(report)


if __name__ == "__main__":
    main()
