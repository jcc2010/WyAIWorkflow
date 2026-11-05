# WyAIWorkflow

A working development workflow for [Claude Code](https://claude.com/claude-code): the stages a
feature or bugfix goes through, which skill or agent handles each one, and how a solo developer
keeps that list honest as skills come and go. It's in daily use across several
projects: a Laravel web app, native iOS apps and single-file HTML tools.

Comments and suggestions are welcome: open an issue for something wrong or missing, or start a
discussion for ideas and questions.

## What's here

| File | What it is |
|---|---|
| [`dev-workflow.md`](dev-workflow.md) | The workflow itself: nine stages with a "done when" for each, the declare-before-editing rule, between-feature routines, session-size habits, and how to evaluate a newly added skill. Agents read it; each project's `CLAUDE.md` points to it and lists only its own substitutions. |
| [`subagents.md`](subagents.md) | The dispatch workflow, stage 4's other half: which agent to pick, what a brief states, and what to check on return. Held to its own budget of 60 lines and 600 words. |
| [`check-names.py`](check-names.py) | Fails when the workflow, or a project's `## Workflow` section, names a skill or agent that isn't installed, when `dev-workflow.md` passes its line or word budget, when `subagents.md` passes its budget, or when a `SKILL.md` you own reaches 20,000 bytes. Fill in `PROJECTS` for your own repos. |
| [`CHANGELOG.md`](CHANGELOG.md) | Why each rule exists, one entry per change, with a cited reason or "reason not recorded". |
| [`REVIEWED.md`](REVIEWED.md) | Every outside skill, repo or piece of feedback reviewed, with the verdict and why, so nothing is re-reviewed by accident. |
| [`scorecard.py`](scorecard.py) | The monthly scorecard: cost per commit, rework churn, new trap docs, review hit rate and `Workflow:` trailer shares per project, appended to a history file. Reads `PROJECTS` from `check-names.py`. |
| [`skip_audit.py`](skip_audit.py) | Daily audit: one `workflow-skip` issue per commit that skipped the workflow, in that project's private repo. Dry run unless given `--file`. Set `START` to when your gate went live. |
| [`tests/`](tests) | `GATE=hooks/workflow-gate.py python3 -m unittest discover -s tests`: no network. |
| [`bin/claude-cost`](bin/claude-cost) | Where Claude Code spend goes, from a local OpenTelemetry event log: by project, by agent and model, by context size, and cache rebuilds after idle gaps. Put it on your `PATH`; `scorecard.py` uses it. |
| [`agents/general-purpose.md`](agents/general-purpose.md) | Overrides the built-in general-purpose subagent: defaults to Sonnet (pass model "opus" per dispatch to review data, auth or money paths), carries the git and deploy rules a subagent must follow, and returns a fixed report (status, changes, checks with exit codes, blockers). |
| [`agents/implementer.md`](agents/implementer.md) | A subagent pinned to Opus that writes code for one task, test first, and returns the same fixed report plus the red run. |
| [`agents/plan-reality-check.md`](agents/plan-reality-check.md) | A read-only subagent that checks a written plan against the code before anyone builds it: references that don't exist, claims the code contradicts, helpers that duplicate existing ones. |
| [`bin/workflow-declare`](bin/workflow-declare) | Declares a session's path before its first edit (`full` with a plan, `shrunk 1-3` with a reason, or `none` with a reason) and prints the `Workflow:` trailer each commit ends with. Put it on your `PATH`. |
| [`hooks/workflow-gate.py`](hooks/workflow-gate.py) | A PreToolUse hook: records declarations, refuses an edit before one, refuses a commit whose trailer doesn't match its files or that lacks a bug marker, refuses `full` and `shrunk` on the integration branch, logs late declarations, and refuses a subagent's `git stash`, `git add -A` / `.` and `git commit -a`. Fails open. |
| [`hooks/log-review-verdict.py`](hooks/log-review-verdict.py) | A SubagentStop hook that logs `plan-reality-check` and design-critic verdicts to `~/.claude/review-verdicts.jsonl`, which `scorecard.py` reads. |

## How it's wired

- `~/.claude/workflow/dev-workflow.md`, next to `check-names.py`, holds the shared stages, the only copy.
- Each project's `CLAUDE.md` has a short section:

  ```markdown
  ## Workflow
  Follow `~/.claude/workflow/dev-workflow.md`. Substitutions here:
  - Stage 5: a visible UI change goes to the design-critic agent with screenshots.
  - Stage 7: no deploy block; merging to main is the ship.
  ```

  List only what differs from the shared file, or what a project rule already forbids (for
  example, a skill that would merge to main locally in a repo that only integrates by push). A
  line that repeats a rule already stated elsewhere in the same `CLAUDE.md` is noise.
- The two hooks and `workflow-declare` are optional. Put `workflow-declare` on your `PATH`, copy
  the hooks under `~/.claude/hooks/`, and wire them in `~/.claude/settings.json` (PreToolUse for
  the gate, SubagentStop for the verdict log). The wiring isn't published, and until it exists
  the declaration and trailer rules rest on the agent following them.
- `check-names.py` runs before and after every edit to either file. It also holds `dev-workflow.md` to
  100 lines and 1,300 words, so a new rule means deleting or merging an old one.

## Skills it names

The workflow leans on the [superpowers](https://github.com/obra/superpowers) plugin, Claude
Code's built-in `/code-review`, `/simplify` and `/security-review`, and a few skills from
elsewhere. Those are linked rather than copied here:

- `retro`, `writing-for-agents` and `improve-codebase-architecture`, from
  [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). The local
  `improve-codebase-architecture` is adapted to read a project knowledge bundle.
- `security-audit`, from
  [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) (MIT).
  The only local change is `disable-model-invocation: true` in its frontmatter. As published,
  its description matches any security question, so it would otherwise take over from the
  per-change `/security-review`.

`/retro`, `/improve-codebase-architecture` and `/security-audit` are only ever started by the
owner typing them, never by an agent. That's how they can sit beside the per-task stages
without firing mid-task.

## Lessons behind it

- A session retro found three rules duplicated in `CLAUDE.md`. That's why each project's section
  now lists substitutions only.
- An independent review found 15 defects in the first version. The checker passed while it
  skipped projects, and a skill's default "merge locally" contradicted a repo's push-only rule.
  The checker now fails loudly in both cases.
- `cmd | tail && git commit` commits even when `cmd` fails, because a pipeline returns its last
  command's status. Gate commits on the check's own exit status.
- A cost report that reads only the live telemetry log silently covers just the time since the
  last rotation: at 50 MB a file, about a day. A "30-day" report covered 3 hours. Read the
  rotated backups too, print the range actually covered, and keep a monthly summary, because
  the backups age out as well.
- Subagent cost is invisible until it is split by agent. Over 4 days, general-purpose subagents
  on Opus cost about $0.077 a request against $0.037 on Sonnet, and an earlier pin of only the
  Explore agent to Sonnet saved almost nothing, because dispatches go to general-purpose. The
  default now lives in `agents/general-purpose.md`; whether it saves money per task is not yet
  measured, since a Sonnet dispatch may take more turns.
- Compaction re-attaches an invoked skill cut at 20,000 characters, so rules past that point
  vanish in long sessions. `check-names.py` now fails on an owned `SKILL.md` that large.
- In zsh, an unquoted glob that matches nothing aborts the whole command with `no matches
  found`. That error means the search never ran. It does not mean "not found".

## Measuring improvement

Cost is measured with `bin/claude-cost`; quality is read once a month by `scorecard.py`, only
from data that already exists, so each reading sits beside the last. Per project in
`PROJECTS`, it reports:

- **Cost per shipped commit:** telemetry spend divided by non-merge commits on the integration
  branch, plus the share of spend from requests over 400k context and from main-session cache
  rebuilds after an hour idle.
- **Rework churn:** the share of a month's added lines changed or deleted again within 14 days,
  by `git blame`. Commit-subject regexes don't work when subjects describe the change rather
  than say "fix".
- **New traps:** trap docs added to the project's knowledge docs that month. Repeated traps
  can't be detected reliably from commit text, so this counts new ones.
- **Review hit rate:** how often the design critic says polish or rework, and findings per run
  from the plan checker and the fresh reviewer. Each dispatch appends its verdict to a log;
  without that, verdicts are read once and lost.
- **Bugs and skips:** from each repo's GitHub issues opened that month: bugs, recurrences (a
  `cause:<slug>` issue with an earlier one of that cause) and `workflow-skip` issues, plus sessions
  the gate logged as declaring late. Cause labels are the agent's judgement, so they are listed for
  review.

The report sets each reading beside the workflow changes that landed since the last one, which
says only that they coincided, never that one caused the other. With one developer only large
effects will show. The deletion pass can then test a removal: drop a rule and see whether the
next month gets worse. A rerun replaces its month's line unless it covers less of the cost log,
because the log keeps only about 10 days of backups. The first baseline (three days, late Oct
2026): requests over 400k context were 17% of spend, and reopening a main session after more
than an hour idle (a full cache rebuild) was 12%. No month-over-month result exists yet.

## Publishing

Changes land in a private repo first. This public copy is cleaned and synced by hand
afterwards, never mirrored automatically.
