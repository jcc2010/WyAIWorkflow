# Development workflow — every coding project

The default path a feature or bugfix takes, and the skill or agent used at each stage. The
project's own CLAUDE.md wins wherever it disagrees; its "Workflow" section lists the
substitutions, and a substitution there replaces whatever a skill here would otherwise do. A
fix of a few lines with a known cause shrinks stages 1–3 to one sentence in chat naming the fix
and the test that proves it; everything else takes every stage. Say which stages you shrank.

| Stage | Use | Done when |
|---|---|---|
| 1. Pick the work | `product-management:roadmap-update`, `productivity:task-management` | The owner named the task in chat, or it is the next item on the project's roadmap |
| 2. Shape it | Create the project's worktree first, so the spec commits on its branch, never on main; then `superpowers:brainstorming`; `product-management:write-spec` when the feature has user-facing goals worth measuring | The owner approved the description or the spec |
| 3. Plan | `superpowers:writing-plans`, then dispatch the `plan-reality-check` agent with the plan path, the checkout and the base ref, and none of your own view of the plan | The check's findings are fixed in the plan |
| 4. Build | `superpowers:subagent-driven-development` (or `superpowers:executing-plans` inline) with `superpowers:test-driven-development`; a bug starts at `superpowers:systematic-debugging` | Every plan task is checked off, and its failing test's output (the red run) is quoted in the task's commit message |
| 5. Verify | `superpowers:verification-before-completion`; `run` or the browser/simulator for anything on screen | The project's full suites exited 0, and you have screenshots of visual changes |
| 6. Review | `code-review` (medium; high for data, auth or money paths), `simplify`; `security-review` for auth, upload, payment or API surface | Every finding is fixed or explicitly declined with a reason |
| 7. Ship | `superpowers:finishing-a-development-branch`, then the project's deploy block (its Workflow section names the substitute where there is none); `operations:change-request` first for a migration on live data or an auth change | Deployed and checked live, or the owner chose to hold |
| 8. Record | `operations:runbook` for a procedure that will recur; the project's knowledge docs or CLAUDE.md for a trap found; `product-management:stakeholder-update` for a weekly "what shipped" | The lesson lives in one place a later session will read |
| 9. Retro | `/retro`, typed by the owner at the end of a session; it suggests missing automated checks, CLAUDE.md rules that belong in a check, and wasteful tool calls | Each suggestion applied (a check, a trap or memory, a pruned rule) or declined |

Size it before you start: name a multi-step task small (under an hour), medium (a few hours)
or large (a day or more). A large one gets an estimate and a smaller first cut proposed to the
owner before any build. Get something working early and deepen it from there. Run `date` at the
start and at each step; when a step passes twice its share of the estimate, tell the owner where
it stands and what is left.

Long-running work: `sitrep-panel:sitrep-panel` for a live progress page. Recurring checks:
`loop` (this session) or `schedule` (cloud, cron).

Between features: `/improve-codebase-architecture`, typed by the owner monthly or when `/retro`
keeps flagging the same area (a local scheduled task can run its scan-and-report half on the
1st). Its report feeds stage 1 and its question rounds are stage 2; the chosen candidate then
goes through stage 3 (a written plan and `plan-reality-check`) before any build.
`/security-audit`, typed by the owner each quarter or before a new public surface ships, audits
the whole codebase; `security-review` in stage 6 stays the per-change check. Start with the
"quick" profile or a run scoped to one trust boundary (tenant data isolation, outbound fetchers)
and an explicit agent budget: a standard run is dozens of agents. Output lands outside the repo;
confirmed findings enter stage 1. It is never scheduled.

## Session size

From one user's telemetry (three days, late Oct 2026; measure your own before relying on it):
turns over 400k context cost about 3x a turn under 200k and were 29% of spend, and one 697k
session alone was 35%. Reads of cached context, not output, were most of the bill.
- When a context-size nudge fires (a Stop hook at 300k works), finish the current task, then
  suggest `/compact` or a new session for the next one. Mid-task, keep going.
- Unrelated work starts in a new session; a long one makes every turn re-read context the new
  task never needs. Standing sessions (a live status panel) keep to their own thread.
- An earlier auto-compact (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`) is a lever; measure what it saves
  on your own log before and after setting it.

## Changing the workflow

Outside ideas are judged in one session and applied in another, the only one that edits this
file. Each hand-off is a proposal file (what was found, why adopt it, the exact change, what was
rejected) that the owner can read and veto; after it lands, a fresh subagent given only the diff
and the proposal's goal checks it. Before reviewing an outside source, read `REVIEWED.md`. Every
change to this repo adds a `CHANGELOG.md` entry in the same commit, with a reason it can cite or
"reason not recorded", never an inferred one. This file is at most 100 lines and 1,300 words
(`check-names.py` enforces both): delete or merge a rule to make room. A monthly pass proposes
deletions (rules that contradict or repeat another, whose reason no longer applies, or that go
unused) and never deletes on its own.

## When a skill is added

When the owner adds a skill or plugin, evaluate it against this file before using it:

1. Run `python3 check-names.py` (exit 0 before you change anything). Read the new skill's
   `SKILL.md` (or the plugin's skill list) and name the stage it serves.
2. Decide: **add** (a stage gains a tool it lacked), **substitute** (it does an existing entry's
   job better; say what it does better), or **leave out** (overlaps without improving, or needs a
   connector the owner won't connect). A cost or optimizer plugin is measured first against your
   own usage log: one such plugin assumed a 5-minute prompt cache where main sessions held one
   hour, and another's guards had zero hits in a real log.
3. Check every project's "Workflow" section for a conflict, e.g. a skill that runs
   `git worktree add` in a project that requires its own worktree script.
4. Propose the edit to this file and any project section; apply it once the owner agrees, rerun
   `check-names.py`, and commit with its `CHANGELOG.md` entry.
