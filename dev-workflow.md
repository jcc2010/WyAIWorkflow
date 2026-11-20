# Development workflow — every coding project

The default path a feature or bugfix takes, and the skill or agent at each stage. The
project's own CLAUDE.md wins wherever it disagrees; its "Workflow" section lists the
substitutions, and a substitution there replaces whatever a skill here would otherwise do. Fixing
something broken whose cause is known shrinks stages 1–3 to one sentence in chat naming the fix
and the test that proves it; everything else, even a small feature or redesign, takes every stage. Before the first edit, run
`workflow-declare` (full with its plan, shrunk 1–3 with why, or none with why); a hook enforces
it once installed, dispatches that edit run it first, and each commit ends with the
Workflow: trailer it prints. A full or shrunk commit also carries `Fixes #N` (issue labelled bug, plus cause:<trap name>) or `Bug: none`.

| Stage | Use | Done when |
|---|---|---|
| 1. Pick the work | The owner's request, or the project's roadmap | The owner named it, or it is next on the roadmap |
| 2. Shape it | Create the project's worktree first, so the spec commits on its branch, never on main; then `superpowers:brainstorming` | The owner approved the description or the spec |
| 3. Plan | `superpowers:writing-plans`, then dispatch the `plan-reality-check` agent with the plan path, the checkout and the base ref, and none of your own view of the plan; log its verdict with its plan path (below) | The check's findings are fixed in the plan |
| 4. Build | `superpowers:subagent-driven-development` (or `superpowers:executing-plans` inline) with `superpowers:test-driven-development` (dispatch per `subagents.md`); a bug starts at `superpowers:systematic-debugging`. After a fix, grep the repo for the bug's shape; judge every hit; keep a guard test if it can recur. | Every plan task is checked off, and its failing test's output (the red run) is quoted in the task's commit message |
| 5. Verify | `superpowers:verification-before-completion`; `run` or the browser/simulator for anything on screen; any review agent dispatched here logs its verdict (below) | The project's full suites exited 0, and you have screenshots of visual changes |
| 6. Review | `code-review` (medium; high for data, auth or money paths), `simplify`; `security-review` for auth, upload, payment or API surface. A write that reads first, must be unique, or calls a payment or email service: assume it runs twice at once; test that. | Every finding is fixed or explicitly declined with a reason |
| 7. Ship | `superpowers:finishing-a-development-branch`, then the project's deploy block (its Workflow section names the substitute where there is none); before a migration on live data or an auth change, give the owner its impact and rollback plan | Deployed and checked live, or the owner chose to hold |
| 8. Record | The project's knowledge docs or CLAUDE.md, for a trap found or a procedure that will recur; a trap a grep or test can catch gets that check, named in the trap (prose is for what no check sees); debugging that ends without a fix leaves "tried X, failed because Y" (two lines at most) as a trap, or a memory if the project has none | The lesson lives in one place a later session will read |
| 9. Retro | `/retro`, typed by the owner at session end | Each suggestion applied (a check, a trap or memory, a pruned rule) or declined |

A hook logs plan-reality-check and design-critic verdicts; log any other review agent's
verdict yourself: one line `{"date", "agent", "project", "verdict" or "count"}`
(plus `"plan"` for plan-reality-check; project is the repo directory name) appended to
`~/.claude/review-verdicts.jsonl`.

Size it before you start: name a multi-step task small (under an hour), medium (a few hours)
or large (a day or more). A large one gets an estimate and a smaller first cut proposed to the
owner before any build. Get something working early, then deepen it. Run `date` at the
start and each step; when a step passes twice its share of the estimate, tell the owner where
it stands and what is left.

Legacy names: rename them only
in an area the task already touches, as their own commit on its branch, never repo-wide. Never
rename a name held outside the repo without a planned migration: bundle, App Group or keychain
ids, URL schemes, tables or stored values, migration filenames, cookie and cache keys, env vars
and config keys, CLI command names.

Worktrees: where `core.hooksPath` is relative, never give Agent `isolation: "worktree"`; use the
project's worktree script, else `git worktree add`. After an isolated run, if `git config core.hooksPath`
is absolute, set it back (e.g. `.githooks`).

Between features: `/improve-codebase-architecture`, typed by the owner monthly or when `/retro`
keeps flagging the same area. Its report feeds stage 1 and its question rounds are stage 2; the chosen candidate
goes through stage 3 before any build.
`/security-audit`, typed by the owner each quarter or before a new public surface ships, audits
the whole codebase; `security-review` in stage 6 stays the per-change check. Start "quick"
or scoped, with an agent budget: a standard run is dozens of agents.
Output lands outside the repo; confirmed findings
enter stage 1. It is never scheduled.

Spend: run `claude-cost --days N --top N` when the owner
asks about cost or usage limits. Pass `model: opus` to general-purpose only for review, design or
diagnosis; everything else takes its Sonnet pin. `scorecard.py` takes a monthly reading; judge a workflow change by the next month's reading, never as cause.

Session size:
- At the 300k context nudge, finish the current task, then suggest `/compact` or a new session.
- A turn that ends above about 150k context offers "Compact now" at wrap-up (or in one
  line). Batch peer messages to a session idle an hour or more.
- Unrelated work starts in a new session (or after `/clear`), above all after an idle hour.
  Standing sessions keep to their thread.
- Read files narrowly in Bash: `grep -n`, then `sed -n` on a range. Never `cat` a whole file
  over about 200 lines; run `diff --stat` before a full diff.

## Changing the workflow

Outside ideas are judged in one session and applied in another, the only one that edits this
file. Each hand-off is a proposal file the owner can read and veto; after it lands, a fresh
subagent given only the diff and the proposal's goal checks it. Before reviewing an outside
source, read `REVIEWED.md`.
Any change to this repo adds a `CHANGELOG.md` entry in the same commit, with a reason it can cite or
"reason not recorded", never an inferred one. This file is at most
100 lines and 1,300 words (`check-names.py` enforces both): delete or merge a rule to make room.

## When a skill is added

Evaluate a new skill or plugin against this file before using it:

1. Run `python3 check-names.py` (exit 0 before you change anything). Read the
   new skill's `SKILL.md` (or the plugin's skill list) and name the stage it serves.
2. Decide: **add** (a stage gains a tool it lacked), **substitute** (it does an existing entry's
   job better; say what it does better), or **leave out** (overlaps without improving, or needs a
   connector the owner won't connect). A cost or optimizer plugin is measured first: run
   `claude-cost --days 7` and check its claims against these numbers.
3. Check every project's "Workflow" section for a conflict, e.g. a skill running
   `git worktree add` where a project has its own worktree script.
4. Propose the edit to this file and any project section; apply it once the owner agrees, rerun
   `check-names.py`, and commit with its `CHANGELOG.md` entry.
