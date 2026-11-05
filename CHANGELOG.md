# Changelog

Why each workflow rule exists, newest first. Every change to this repo adds an entry here, in
the same commit, with a reason it can cite or "reason not recorded", never an inferred one. The
monthly deletion pass reads this file to find rules whose reason no longer applies.

This public copy starts at its first sync; earlier history lives in the private source repo.

## 2026-11-05 — stage 4: sweep a bug's shape after the fix (trial)
- **What:** one line in stage 4: after a fix, grep the repo for the bug's shape, judge every hit,
  keep a guard test if it can recur.
- **Why:** the owner chose it in chat. No written rule said this outside a security-audit skill.
- **Limits:** a trial, and nothing enforces it. In the one project checked, the two greppable
  candidates showed no new bug. The source's counts are tuned on its own repos and are not support.
  Judge it monthly by counting real hits by hand; none means remove the line.

## 2026-11-05 — stage 6: assume a write runs twice at once (trial)
- **What:** one line in stage 6 for a write that reads first, must be unique, or calls a payment
  or email service. To make room here, `dev-workflow.md` drops the `Recurring checks` line, the
  session-size figures and two parentheticals. The file is at its word limit, so the next rule
  must delete one first.
- **Why:** the owner chose it in chat. No rule covered application writes, and this bug had
  already happened: a double-clicked button saved two items.
- **Limits:** a trial, and nothing enforces it. It fires at review, after the code exists. Evidence
  that the line changes behaviour is weak: the source's concurrency tasks failed 4 of 45 runs
  without its skill and 2 of 45 with it. Judge it at a later retro: did it catch an overlap bug, or
  only cost time?

## 2026-11-05 — the gate reads the shell: eight findings from a fresh review
- **What:** one shell scanner replaces the gate's regex splitter, so only a commit's own -m, -F,
  --trailer and heredoc count as its message, a subshell's `cd` stays in the subshell, and a commit
  whose repo can't be worked out skips the gate. `--no-edit` or `-C` exempts only with no -m or -F.
  A first declaration writes its state before logging, runs no git call per file and logs once.
  Finishing a cherry-pick or revert is exempt from the branch rule, as a merge is. The scorecard's
  late column counts sessions.
- **Why:** 800 changed files took 21.29s against a 10s hook timeout, and now take 0.4s. A marker in
  another command's heredoc passed, and `git commit -m x --no-edit` passed with no trailer. Replay
  of 2,803 recorded commands through the parser: no crash, no trailer or marker lost that should
  count.
- **Limits:** 67 of 2,820 recorded commits (2.4%) have a target the gate can't resolve and are now
  skipped; the audit is the backstop. `-m "$MSG"` is now refused and a piped `-F -` now fails open.
  bash -c, eval, command git commit, git commit inside $(...) or after then/do, and pushd are not
  seen. Harness behaviour on a hook timeout and concurrent state-file writers are unmeasured.

## 2026-11-04 — the gate takes a bug marker, refuses full and shrunk on the integration branch, logs late declarations
- **What:** a `full` or `shrunk` commit must carry `Fixes #N` or `Bug: none`, and is refused on the
  integration branch (`none` and finishing a merge are exempt). The gate logs, and never refuses
  on, a commit refused with nothing declared or code already changed at a first declaration, in
  `~/.claude/workflow-late-declarations.jsonl`; the scorecard counts those sessions. `workflow-declare`
  prints the marker. A later fix keeps a logged file's whole name: a stripped `git status` line
  logged `app.py` as `pp.py`.
- **Why:** commit text can't identify bugs, so recurrences can't be counted without a marker. A
  feature edited through Bash and committed on the integration branch passed both the gate and the
  audit. Measured since the gate went live: the branch rule flags 1 of 59 commits, and 5 of 21
  sessions first declared after a commit refusal. The owner approved it in chat.
- **Limits:** Bash edits stay invisible at edit time, and every rule here fires after the work is
  done.

## 2026-11-04 — `shrunk` is for fixes only
- **What:** `dev-workflow.md` no longer sets `shrunk` by size. Fixing something broken whose cause
  is known shrinks stages 1-3; a feature or redesign takes every stage, however small. No check
  enforces this: it rests on honest declaration and the audit's other flags.
- **Why:** 9 of 16 `shrunk` commits since the gate went live changed more than 20 lines outside
  docs and tests, and no size limit separates a fix from a feature: one feature was 52 lines and a
  timeout retry 51. The owner chose "Fixes only" over enforcing "a few lines".

## 2026-11-04 — `skip_audit.py` lists workflow skips; scorecard reports bugs and recurrences
- **What:** new `skip_audit.py`: one `workflow-skip` issue per commit, in that project's own private
  repo, for a missing `Workflow:` trailer, a `full` trailer whose plan is missing or has no
  plan-reality-check line, or a `Fixes #N` naming no issue. It dry-runs unless given `--file`. A git
  or GitHub failure skips the repo with its reason and never reads as clean. `scorecard.py` gains a
  table of bugs, recurrences, skips and causes per project. New `tests/`.
- **Why:** the owner wants recurring problems countable per project, and a skip logged even when
  the agent that skipped says nothing, so a script logs it. The cut-off reads the author date: the
  first dry run flagged 10 commits written before the gate that a rebase had re-dated.
- **Limits:** stages 4-9 show only where they leave evidence; a big change declared `shrunk`
  passes; cause labels are the agent's judgement, so the scorecard lists them for review.

## 2026-11-04 — debugging dead ends get recorded
- **What:** stage 8 now says debugging that ends without a fix leaves "tried X, failed because
  Y", two lines at most, as a trap in the project's knowledge docs, or as a memory if the project
  has none. `REVIEWED.md` also logs two posts as rejected, with no rule change.
- **Why:** a failed attempt that never becomes a trap is lost when the session ends; "what is
  already ruled out" in `subagents.md` covers one dispatch only. A cheap bet from a Reddit post
  with no evidence behind it; how often work is repeated this way is unmeasured. The owner
  approved it in chat.
- **Also:** to stay within the 1,300-word budget, `dev-workflow.md` drops the auto-compact line
  and the clause saying `scorecard.py` counts logged verdicts. The rule took this copy to 1,324
  words. Neither is in the private source copy, and `scorecard.py` itself is unchanged.

## 2026-11-03 — dev-workflow.md no longer names the business plugins' skills
- **What:** removed the `operations`, `product-management`, `productivity` and `data` skill names.
  Stage 1 points at the owner's request or the project's roadmap. Stage 7 says to give the owner
  the impact and rollback plan before a migration on live data or an auth change. Stage 8 records
  a trap or recurring procedure in the knowledge bundle or CLAUDE.md. The closing "Not part of
  coding work" note is gone. `check-names.py` keeps these as account plugins, because some
  projects' files still name them.
- **Why:** those plugins were turned off on 3 Nov; across 1,775 transcripts (484 Skill calls) none
  of the four was ever called or typed. The owner asked for them to be dropped.

## 2026-11-03 — dev-workflow.md no longer names sitrep-panel
- **What:** removed the `sitrep-panel:sitrep-panel` line for long-running work, and the panel as
  the example of a standing session.
- **Why:** the plugin is no longer installed, so `check-names.py` failed. The owner confirmed the
  removal in chat.

## 2026-11-03 — claude-cost splits each row by token type
- **What:** every project, agent-and-model and top-session row shows read $, write $, output $ and
  uncached input $, and the write-to-read dollar ratio. Agent rows also show the share of cache
  writes with the 5-minute lifetime. Each request's `cost_usd` is divided in proportion to list
  rates (`INPUT_PRICES` beside `PRICES`), so the four add up to the row total.
- **Why:** cache writes are a small share of cached tokens but about a third of spend, and the
  report gave each row one figure, so cold-cache sessions did not show. The log records
  `cache_creation_5m_tokens`, which tests the claim that subagents use a 5-minute cache: on 3 Nov
  every subagent row was 100% 5-minute and main sessions 2%.

## 2026-11-03 — the commit gate checks the trailer against the commit
- **What:** a `none` trailer is refused on files outside Markdown, `docs/`, gitignored files and
  the project's data paths, and a `full` or `shrunk` trailer is refused without a matching
  declaration. No refusal shows a trailer template: each says to run `workflow-declare` first, and
  quotes the declared trailer when there is one. The commit's paths are read from the whole
  command, so a path after a multi-line `-m` message is seen.
- **Why:** 3 of the 14 commits with a trailer since 2 Nov wrote `none` by hand over code edited
  through Bash, which the edit gate cannot see, and one session learned the trailer from the old
  refusal's template and typed `none` without declaring. The owner approved making it live.

## 2026-11-03 — the verdict hook survives a removed plan checkout
- **What:** when the plan's own repo no longer exists, `hooks/log-review-verdict.py` takes the
  project from the caller's cwd and keeps the plan path from its `docs/` segment.
- **Why:** replaying a real plan check whose scratch worktree was gone logged project "plans" and
  an absolute plan path.

## 2026-11-03 — the review-verdict hook is wired, and reads the hand-back report
- **What:** settings.json's SubagentStop runs `log-review-verdict.py` for plan-reality-check and
  the design critic. The hook reads the report from the subagent's SubagentHandback tool call,
  which is how a background subagent returns it, and takes the project from the plan's own repo
  when the brief gives an absolute plan path.
- **Why:** the owner approved the wiring. The first live dispatch of each agent logged
  "unparsed": the report was in the hand-back tool input, not in assistant text. Replayed through
  the fix, both parsed, and a live recheck logged `ship`, 0 findings.

## 2026-11-03 — a hook logs review verdicts
- **What:** a SubagentStop hook (`hooks/log-review-verdict.py`) appends plan-reality-check and
  design-critic verdicts to `review-verdicts.jsonl` with `"source": "hook"`, the main checkout's
  directory as project, and the plan path made repo-relative so the workflow gate can match it.
  Output it cannot parse logs as "unparsed". The by-hand rule now covers only other review agents.
  `scorecard.py` shows the hook's share and counts "fix first" as flagged beside polish and rework.
- **Why:** one project dispatched those two agents 47 times in 30 days and logged none, so its
  review hit rate had no data. The owner approved the proposal.
- **Limits:** live only once wired in settings.json, which needs the owner's approval.

## 2026-11-03 — the subagent git refusal is wired
- **What:** settings.json's workflow-gate Bash hooks gain `if` patterns for git stash and git add,
  so the subagent refusals fire on their own, not only beside a commit or a declaration.
- **Why:** the owner approved it. Probed live: a subagent's git stash, git add -A and git commit
  -am were refused; its git add of a named file and git stash list ran; a main-session stash and
  pop ran. That also proves subagent hook input carries `agent_id`.

## 2026-11-03 — subagents may not git commit -a
- **What:** `hooks/workflow-gate.py` also refuses a subagent's git commit -a, --all, or a short
  cluster holding a (-am, -qa); --amend, --author and option values such as -m "-a" do not match.
  `subagents.md` and both agent files name it.
- **Why:** -a stages every modified tracked file, the same sweep as git add -A; one subagent run
  used it in 30 days. A review found the gap, and the owner approved closing it.

## 2026-11-03 — a separate workflow for subagents
- **What:** `subagents.md`, the dispatch workflow (pick the agent, write the brief, check the
  return), with its own `check-names.py` budget of 60 lines and 600 words. Stage 4 now says
  "dispatch per subagents.md"; the model rule moved there. A new `implementer` agent pinned to
  Opus writes code. `general-purpose.md` gains git and deploy lines. Both return a fixed report
  (status, changes, checks with exit codes, blockers). `workflow-gate.py` refuses a subagent's git
  stash, git add -A and git add . in any repo; main sessions are untouched.
- **Why:** the owner asked for one and approved the three parts. In the busiest project over 30
  days, 2,243 of 2,327 dispatches went to general-purpose with no agent-side git rules; 10 ran git
  stash and 12 ran git add -A or git add . `dev-workflow.md` had no room left.
- **Limits:** the hook sees git stash and git add only where settings.json's `if` patterns match;
  until they are added it fires only on commands that also contain a commit or a declaration. The
  implementer's Opus cost against per-dispatch choice is unmeasured; compare with `claude-cost`.

## 2026-11-02 — Opus subagents only to write code or review data, auth or money paths
- **What:** general-purpose subagents get model "opus" only to write code or to review data, auth
  or money paths. Workflow, docs and other reviews stay on the Sonnet default. To fit, the
  "Changing the workflow" sentence drops its file list ("this repo" covers it).
- **Why:** the owner asked for it. Over 2 days, general-purpose on Opus was $41.27 (9.7% of
  spend, $0.066 per request) against $0.034 per request on Sonnet; the workflow-file reviews that
  day were Opus dispatches. The saving is unmeasured.

## 2026-11-02 — the workflow gate is live
- **What:** `hooks/workflow-gate.py` is wired in settings.json PreToolUse:
  - Bash `workflow-declare`: validates the declaration and records it.
  - Bash `git commit`: refuses a commit without a `Workflow:` trailer.
  - `Edit|Write|NotebookEdit|MultiEdit`: refuses an edit until the session has declared; refuses
    full and shrunk on the integration branch (detached at its tip counts, a stopped rebase of a
    branch does not); limits none to a project's `Data paths` line.
  - Never gated: Markdown, a top-level `docs/`, gitignored files, `~/.claude`, and repos that are
    neither in PROJECTS nor name dev-workflow.md in their CLAUDE.md. Fails open on any error.
  - Declarations are keyed by session, plus `agent_id` for a subagent (which falls back to its
    parent's), and by the repo's git common dir, so one made in the main checkout covers its
    worktrees.
- **Why:** the owner asked to build it and then to wire it.
- **Tests:** 76 cases against a throwaway HOME, including one per finding of a fresh review (9
  fixed: heredoc bodies read as commands, rebase seen as main, subshell and chained `cd`,
  message-reuse flags, a state-file race, ignored files, the hint, worktree-named verdicts, data
  paths). Live after wiring, a Write in a gated repo and a `git commit --dry-run` (plain and
  heredoc message) were refused.
- **Limits:** edits made through Bash are not seen; `shrunk 1-3` with any reason reaches code;
  `full` cannot pass until a plan-reality-check verdict is logged with its plan path; whether a
  subagent's hook input carries the parent's session_id is unproven (the fallback covers both);
  about 0.2 s per Edit; state files under `~/.claude/hooks/state/workflow/` are never pruned.

## 2026-11-02 — scorecard --no-record writes nothing
- **What:** `scorecard.py --no-record` prints the report to stdout and writes neither the report
  file nor the history.
- **Why:** it skipped only the history append, so each test run replaced `scorecard-<month>.md`;
  that happened twice on 2 Nov and both times the file was restored from a backup.

## 2026-11-02 — fixes from the post-landing review of the declare/trailer change
- **What:**
  - The verdict-line schema in `dev-workflow.md` names `"plan"` (plan-reality-check only) and says
    project is the repo directory name. To fit, it drops "which `scorecard.py` counts"; the file
    is at 100 lines and 1,299 words, both at the limit.
  - `workflow-declare` refuses a plan path that is absolute or contains whitespace, and looks for
    the plan from the repo root, not the current directory.
  - `scorecard.py` normalises plan paths before matching them, and shows n/a for a history line
    with no trailer counts.
  - The entry below now says the gate does not see edits made through Bash.
- **Why:** a post-landing review found these. The schema had no plan key, so sessions would
  invent one and "checked" would stay 0; a path with a space or a leading `/` would print a
  trailer the scorecard counts as missing.

## 2026-11-02 — declare the path before the first edit; Workflow: commit trailer
- **What:**
  - `dev-workflow.md`: before its first edit, a session runs `workflow-declare` (full with its
    plan, shrunk 1–3 with why, or none with why). Each commit ends with the `Workflow:` trailer
    the declaration prints. Dispatches that edit run it first.
  - Stage 3's verdict line gains the plan path, so a `full` can be matched to its check.
  - `bin/workflow-declare` checks the form and prints the trailer.
  - `scorecard.py` reports each project's trailer shares: full, shrunk, none, missing. For full,
    it checks that the plan exists at that commit and that a check names it. For full and
    shrunk, it counts bodies that quote a failing run.
  - `scorecard.py` decodes git output leniently: non-UTF-8 blame output crashed the churn count.
  - To fit the budget, the session-size figures and the cost-plugin history are now pointers.
- **Not yet:** the two hooks. One records the declaration; the other refuses Edit, Write and
  NotebookEdit before a declaration, refuses full and shrunk on the integration branch, and limits
  none to data paths. Both wait for the owner's approval.
- **Limits:** the trailer is self-reported, and `shrunk 1-3` with any reason always reaches code;
  that is the open door, and the scorecard watches its share. Edits made through Bash (`sed -i`,
  heredocs, `python -c`) the gate does not see. The first month's reading is a baseline: October
  reads 0 trailers in 1,593 commits across 12 projects.
- **Why:** the owner asked for a marker that shows the workflow is followed, then for it to be
  enforced before the work rather than after. In the 14 days to 2 Nov, about 18 of 448 commits in
  seven projects quoted a failing test, and the verdict log had 3 lines.

## 2026-11-02 — software-audit-skill, thepmcode decision-support, longview-skills, your-token and Overflow reviewed, all rejected
- **What:** five `REVIEWED.md` entries. Nothing else changes.
- **Why:** the owner asked for each review.
  - software-audit-skill: per-change and whole-codebase security audits are covered
    (`security-review`, `/security-audit`), its broad triggers would compete with stage 6, and
    its install path is one Claude Code does not load.
  - thepmcode: no owner prompt asks for this kind of decision grilling, its useful modes are in
    brainstorming and `GRILLING.md`, and its description would compete with stage 2.
  - longview-skills: its coding skills duplicate stages 4–6, forty more descriptions would widen
    triggering, and its evidence is self-graded.
  - your-token: it estimates token use that telemetry and `claude-cost` already measure, assumes a
    5-minute cache that measured an hour here, and skips the weekly limit.
  - Overflow: an exchange for spare subscription capacity, not a workflow tool; earning means
    running strangers' issue text and commands, and no idle capacity is measured.

## 2026-11-02 — jolitz reviewed, rejected; its idea adopted
- **What:** a `REVIEWED.md` entry. A user-level hook now also refuses emptying the production
  cache over SSH, the idea recorded as adopted. The hook is not versioned here and settings.json
  is unchanged.
- **Why:** the owner asked for the review, then said to add the guard. There are no
  root-administered servers here, and jolitz pulls and runs its own updates on every session
  start. The rule "never empty the production cache" (it empties a replay guard, locks and rate
  limiters) had no mechanical check. Tested on 11 sample commands; not covered: a clear run from a
  script on the server.

## 2026-11-02 — "context sockets" post reviewed, no change; Sketchy reviewed, rejected
- **What:** two `REVIEWED.md` entries. `deps/` also picked up the provenance comment now in the
  installed better-clear-language SKILL.md.
- **Why:** the owner asked for each review.
  - Sockets: the pattern is already how `dev-workflow.md`, the project Workflow sections and the
    knowledge bundles work. The missing provenance comment, found while checking, would have left
    the skill untracked by the monthly upstream check.
  - Sketchy: no dashboard-project prompt asks for a diagram, its chat skill loads self-updating code
    from a CDN beside what could be confidential figures, and existing tools cover the occasional
    diagram.

## 2026-11-02 — better-clear-language adopted for dashboard text; AlanChen4/skills reviewed
- **What:** the `REVIEWED.md` AlanChen4/skills entry, first "rejected but one optional trial",
  became "partly adopted" with the trial result. `dev-workflow.md` does not change.
- **Why:** the owner tried better-clear-language on dashboard tooltips and said to adopt it. Only
  that skill could help, on text colleagues read; the other three are rejected.

## 2026-11-02 — master-console, claude-vibe-squad, Comet, open-design-agent-kit and cogit reviewed, all rejected
- **What:** five `REVIEWED.md` entries, plus a correction to cogit's worktree claim (under the
  ignore policy worktree sessions write the main checkout's gitignored `.cogit/`, changing no
  tracked file; under the commit policy each worktree keeps its own record). Verdicts unchanged.
- **Why:** the owner asked for each review.
  - master-console and claude-vibe-squad would replace `dev-workflow.md` rather than slot in;
    master-console registers 63 tool hooks and is Windows-first, and claude-vibe-squad's cross-
    family review needs three other CLIs and its optional launchd agents run checkout code with
    the user's secrets.
  - Comet is harmless but shows little not already on screen, and its `git status` runs can
    contend for `index.lock` in shared checkouts. The owner may still install it for fun.
  - open-design-agent-kit: the main project already has a design system, most entries are other
    brands' looks, and the generic ones add nothing a throwaway mockup needs.
  - cogit: its git hooks would edit tracked hooks and stage its record with every commit, and it
    adds hooks to every turn.

## 2026-11-01 — general-purpose subagents default to Sonnet
- **What:** an `agents/general-purpose.md` override (model sonnet, all tools, a short report-back
  prompt). Stage 4 says to pass model "opus" per dispatch for implementation and review.
- **Why:** the owner approved it after `claude-cost` showed general-purpose on Opus at $62.59 and
  about $0.077 a request over 4 days, against $0.037 on Sonnet. Per-task saving is unmeasured,
  since a Sonnet dispatch may take more turns. Check after a week against review and
  implementation quality. Only sessions started after the change load the file.

## 2026-11-01 — `claude-cost` reports spend by agent and model
- **What:** a "By agent and model" section: requests, cost and $/request per agent name (absent =
  main thread) and model, sorted by cost. The script is now published as `bin/claude-cost`.
- **Why:** 4 days of spend was 82% main thread on Opus, 12% general-purpose on Opus and 5%
  general-purpose on Sonnet. An earlier pin of the Explore agent to Sonnet had saved almost
  nothing ($0.33 of spend went through Explore), because dispatches go to general-purpose.

## 2026-11-01 — Legacy names renamed area by area
- **What:** `dev-workflow.md` gains a paragraph: rename legacy internal names only in an area a
  task already touches, as their own commit, never repo-wide, and never a name held outside the
  repo (ids, URL schemes, stored values, migration filenames, env vars, command names) without a
  planned migration.
- **Why:** the owner asked for the clean-up one area at a time. A repo-wide rename (8,588 hits)
  was rejected as churn that collides with every open worktree; renaming an external name breaks
  installs, sessions or production.

## 2026-11-01 — graphify and diagram-design reviewed; graphify trial recorded
- **What:** two `REVIEWED.md` entries, both rejected; the graphify entry then gained the trial's
  result table. No rule changes.
- **Why:** the owner asked for the reviews. graphify-first used 2x the tokens and time of
  grep/read and missed same-namespace PHP callers; diagram-design has no demand behind it and a
  30,874-byte SKILL.md over the size guard below.

## 2026-11-01 — Skill size guard; superpowers 7.0.1
- **What:** `check-names.py` fails on any owned `SKILL.md` of 20,000 bytes or more. An owned
  22,223-byte skill was split into sibling files read at the step that needs them (15,573 bytes),
  and references that pointed at moved sections were repointed. superpowers 7.0.1 was installed
  from the author's own marketplace; the monthly skill-update check now also compares each
  enabled plugin's installed version with its upstream.
- **Why:** after a compaction Claude Code re-attaches an invoked skill cut at 20,000 characters
  (obra/superpowers#2481), so rules past that point silently vanish in long sessions. 7.0.1
  splits the three 7.0.0 skills over the limit. A skill listed but missing counted as 0 bytes
  and passed; that now fails.

## 2026-11-01 — Monthly scorecard and review-verdict log
- **What:** `scorecard.py` writes a monthly report and appends one line to a history file: spend
  and cost per commit per project, the shares over 400k context and after idle gaps, 14-day line
  churn, new trap docs, review hit rate. Review dispatchers append one line per verdict to a log
  (a "Spend" section and a rule after the stages table in `dev-workflow.md`). The monthly scan
  runs it before the deletion pass. A rerun replaces its month's line unless it covers less cost
  time; the history is written atomically; bad history lines are kept and warned about.
  `claude-cost` reads the rotated log backups and warns when the log is shorter than `--days`.
  `REVIEWED.md` gained entries for T3 Code, agent-sleep, Hallmark, taste-skill and a checkmate
  re-review (all rejected).
- **Why:** the owner asked how improvement is measured; cost was measured and quality was not.
  `claude-cost --days 30` had covered only the 3 hours since the last log rotation, and the log
  keeps about 10 days, so the history file is the only long-term record. A fresh-subagent check
  found the verdict-log rule sat where no dispatcher reads, so it moved next to the stages table.

## 2026-11-01 — Measuring improvement (planned)
- **What:** README "Measuring improvement" section and a log-rotation lesson; `REVIEWED.md`
  measurement note updated. (The scorecard was built in the entry above.)
- **Why:** outside feedback asked whether improvement is measured or judged by feel; the honest
  answer was by feel for quality. Checking the cost data for a baseline found the report had been
  reading only the live log file.

## 2026-11-01 — Changelog, budgets, review loop, sizing
- **What:** this file and `REVIEWED.md`; a "Changing the workflow" section (proposal files, a
  fresh-subagent check of each change, a monthly deletion pass that only proposes);
  `check-names.py` fails `dev-workflow.md` past 100 lines or 1,300 words and accepts a shell
  command on PATH (`date`) as a known name; "Size it before you start".
- **Why:** two pieces of outside feedback on this setup (see `REVIEWED.md`): rules pile up until
  they contradict, with no record of why each exists; hand-offs left nothing to read or veto; the
  implementer was the only judge of its own change. Sizing came from wheresryan22/anatomy. The
  checker had flagged `date` as a missing skill.

## 2026-11-01 — First public version
- **What:** `dev-workflow.md`, `check-names.py`, `agents/plan-reality-check.md`, README.
- **Why:** share the workflow for comments and suggestions.
