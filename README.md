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
| [`dev-workflow.md`](dev-workflow.md) | The workflow itself: nine stages with a "done when" for each, between-feature routines, session-size habits, and how to evaluate a newly added skill. Agents read it; each project's `CLAUDE.md` points to it and lists only its own substitutions. |
| [`check-names.py`](check-names.py) | Fails when the workflow, or a project's `## Workflow` section, names a skill or agent that isn't installed. Fill in `PROJECTS` for your own repos. |
| [`CHANGELOG.md`](CHANGELOG.md) | Why each rule exists, one entry per change, with a cited reason or "reason not recorded". |
| [`REVIEWED.md`](REVIEWED.md) | Every outside skill, repo or piece of feedback reviewed, with the verdict and why, so nothing is re-reviewed by accident. |
| [`agents/plan-reality-check.md`](agents/plan-reality-check.md) | A read-only subagent that checks a written plan against the code before anyone builds it: references that don't exist, claims the code contradicts, helpers that duplicate existing ones. |

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
- `check-names.py` runs before and after every edit to either file. It also holds `dev-workflow.md` to
  100 lines and 1,300 words, so a new rule means deleting or merging an old one.

## Skills it names

The workflow leans on the [superpowers](https://github.com/obra/superpowers) and
[sitrep-panel](https://github.com/dbl8005/sitrep-panel) plugins, Claude
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
- `product-management`, `productivity` and `operations`: Anthropic's Cowork plugins, used for
  roadmap, spec and runbook work.

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
- In zsh, an unquoted glob that matches nothing aborts the whole command with `no matches
  found`. That error means the search never ran. It does not mean "not found".

## Measuring improvement

Cost is measured; quality is not yet. Planned, not built: a monthly scorecard per project, read
only from data that already exists, with one reading as a baseline and one a month after:

- **Cost per shipped commit:** telemetry spend divided by non-merge commits on the integration
  branch, plus the share of spend from requests over 400k context.
- **Rework churn:** the share of a month's added lines changed or deleted again within 14 days.
  Commit-subject regexes don't work when subjects describe the change rather than say "fix".
- **Repeated traps:** fixes for a failure already recorded in the project's knowledge docs.
- **Review hit rate:** how often the design critic says polish or rework, and findings per run
  from the plan checker and the fresh reviewer. Each dispatch appends its verdict to a log;
  without that, verdicts are read once and lost.

Each reading is set beside the workflow changes that landed since the last one, which says only
that they coincided, never that one caused the other. With one developer only large effects
will show. The deletion pass can then test a removal: drop a rule and see whether the next
month gets worse. The first baseline (three days, late Oct 2026): requests over 400k context
were 17% of spend, and reopening a main session after more than an hour idle (a full cache
rebuild) was 12%.

## Publishing

Changes land in a private repo first. This public copy is cleaned and synced by hand
afterwards, never mirrored automatically.
