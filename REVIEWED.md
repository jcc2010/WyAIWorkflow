# Reviewed outside sources

Every outside skill, plugin, repo or piece of feedback reviewed for this workflow, newest first,
with the verdict and why. Check here before reviewing a source again; a re-review needs a reason
the earlier verdict did not cover (a new version, a changed need). A verdict is about fit with
this setup, not the quality of the source.

**What is measured:** cost is, from local OpenTelemetry and a small report script, and a monthly
scorecard (`scorecard.py`, see the README) reads cost per commit, churn, new traps and review
hit rate. Skill evals still wait on `claude plugin eval` leaving early access. With one
developer an adoption's effect is read beside the next month's scorecard, never as proof of
cause; until a reading exists it is judged by feel and by recorded defects in each project's
knowledge docs.

## 2026-11-01 — [diagram-design](https://github.com/cathrynlavery/diagram-design) (v2.6.136)
- **Source:** MIT: a skill that writes each of 45 diagram types as one self-contained HTML + SVG
  file in an editorial house style, with optional Python scripts for checks, export and import.
- **Verdict:** rejected; no ideas adopted.
- **Reason:**
  - No need: in 233 transcripts across 31 projects, the only owner prompt mentioning diagrams,
    flowcharts or Mermaid is this review request.
  - Claude's own artifact-diagramming and visualize skills already cover the occasional diagram.
  - Its SKILL.md is 30,874 bytes, against the 20k compaction guard (see superpowers below), and
    the skill is 5.7 MB with 60 references.
  - Brand onboarding blocks the first diagram.
- **Would change it:** regular diagram requests from the owner; try the built-in skills first
  even then.

## 2026-11-01 — [graphify](https://github.com/Graphify-Labs/graphify) (v1.0.0)
- **Source:** Apache-2.0, PyPI `graphifyy`: a tree-sitter knowledge graph of the repo, queried via
  `graphify query|path|explain` in place of grep and Read.
- **Verdict:** rejected for now; no ideas adopted.
- **Reason:**
  - Install adds PreToolUse hooks on Bash|Grep and Read|Glob (every call; `--strict` denies the
    first raw read). That's a settings edit.
  - It adds a CLAUDE.md "query the graph before any grep or read" rule, which competes with a
    knowledge-docs-first rule and the CLAUDE.md size budget.
  - Its skill.md is 48,455 bytes, against the 20k compaction guard.
  - Its git hooks rebuild graph.json on every commit.
  - Its code evidence is n=6 on ERPNext: 70.8% to 82.0% coverage at about 140K tokens per query,
    with no token saving reported. The "80%" claim is for the paid Cloud.
  - String- and container-resolved wiring in PHP frameworks is where a static graph is weakest.
    That was unmeasured until the trial below.
- **Trial (owner-approved):** hook-free, code-only, on the main Laravel project, five questions.

  | | graph first | grep/read |
  |---|---|---|
  | Context tokens | 1.68M | 0.83M |
  | Time | 2x | 1x |
  | Questions answered correctly | 4 of 5 | 5 of 5 |

  Graph-first lost the 5 same-namespace users of one class (the graph has no edge, because PHP
  needs no `use` for the same namespace). `query` returned unrelated Swift nodes; only
  `explain <Class>` was accurate, and grep matched it.
- **Would change it:** a release whose PHP resolver links same-namespace references, re-run on
  the same five questions.

## 2026-11-01 — [superpowers](https://github.com/obra/superpowers) (v7.0.1, against installed 7.0.0)
- **Verdict:** kept (it is the base of stages 2–7); the 20,000-character compaction limit adopted
  as a size guard on owned skills.
- **Reason:** after a compaction Claude Code re-attaches each invoked skill cut at 20,000
  characters ([obra/superpowers#2481](https://github.com/obra/superpowers/issues/2481): one
  session lost subagent-driven-development's five-round limit and ran 18 fix rounds). 7.0.1
  splits the three 7.0.0 skills over the limit (subagent-driven-development 32,577 bytes,
  writing-skills 26,623, executing-plans 20,405; the first and third are stage 4, which runs in
  the long sessions that compact). The brainstorming retune (reads the project first, two or
  three approaches, a short design doc even for a small change) fits stage 2's approval gate.
  The official marketplace still pinned 7.0.0, so the owner installed 7.0.1 from the author's
  own marketplace and disabled the old copy; switching back is an option once the official one
  catches up. Adopted: `check-names.py` fails on an owned `SKILL.md` of 20,000 bytes or more,
  and an owned skill of 22,223 bytes was split to 15,573.

## 2026-11-01 — [checkmate](https://github.com/rover-001/checkmate) (v2.1.0, re-review)
- **Source:** MIT. First reviewed at v1.1.0 on 25 Oct, before this file existed; the owner filed
  [rover-001/checkmate#1](https://github.com/rover-001/checkmate/issues/1) with five
  suggestions, and the author fixed each in v1.2.0–v1.2.2 and closed it.
- **Verdict:** rejected for now: the code issues are fixed; the gain for this setup is unmeasured.
- **Reason:** it injects about 1.8 KB of "goal-driven" rules at SessionStart (shortest path, terse
  answers, decide, ask rarely, finish, verify with evidence, earn complexity, a closing status
  line), with lite/full/ultra modes and a `/checkmate-gain` report. Every point in issue #1
  checks out in the v2.1.0 source. But every published result compares it with a bare agent (271
  vs 585 median output tokens; 97.2% vs 86.8% pass); its `realistic-*` arms (a CLAUDE.md plus a
  concise style, i.e. this setup) are in `benchmarks/run.mjs` but unpublished. Output tokens are
  14.9% of spend here ($50.78 of $341.66, 29 Oct–1 Nov), so even halving them saves at most ~7%,
  part of which a concise style already takes; the big costs (context over 400k, idle cache
  rebuilds) it does not touch. It overlaps the concise style, the CLAUDE.md verification rules
  and `verification-before-completion`; its "never assert on text" pulls against a
  markup-asserting test suite.
- **Would change it:** a published realistic-arm gain over a concise style plus CLAUDE.md, or a
  one-week trial on one project compared via `/checkmate-gain --sessions` and the month's
  scorecard; the owner's call.

## 2026-11-01 — [taste-skill](https://github.com/Leonxlnx/taste-skill) (v2)
- **Source:** MIT: an anti-slop art-direction skill of the same kind as impeccable and Hallmark
  (both rejected). `draw.mjs` deals three of twenty "researched directions" from about 1.8 MB of
  JSON; `inspect.mjs` (Node 22+, Chrome) enforces a "dated tells" registry; a screenshot
  look-and-fix loop closes the run.
- **Verdict:** rejected; no ideas adopted.
- **Reason:** its banned list is the main project's house style: hairline rules and 1px boxes,
  tracked uppercase captions, mono labels, soft card shadows. The project's stylesheets use all
  of them (85 `1px solid`, 29 `letter-spacing`, 13 uppercase labels, 16 `box-shadow`), so its
  inspector would fail the design system. It sets the design ("adopt the dealt direction";
  `--keep palette,type` still deals the composition), where the project's look comes from its own
  stylesheets. Its description fires on nearly all UI work, competing with `frontend-design` and
  the design-critic agent. It needs Node 22+ and Chrome and fetches images over the network, in a
  project with no JS toolchain by rule. Screenshot-and-fix is covered by stage 5 and the critic.

## 2026-11-01 — [Hallmark](https://github.com/Nutlope/hallmark) (v2.0.0)
- **Source:** Together AI, MIT: a design skill that builds new pages from one of fifty themes, hero
  first, then runs `sloplint` (static linter plus a puppeteer-core/Chrome render tier) and a
  fresh-context reviewer. Lists impeccable (rejected below) as an inspiration.
- **Verdict:** rejected; no ideas adopted.
- **Reason:** wrong job: the project is an existing app with a read-only base stylesheet, and
  Hallmark's own SKILL.md says not to run it on an existing design unless named; its themes,
  `tokens.css` and new fonts are the opposite of that styling. Its "Floor" checks, run against the
  project, found nothing (no `transition: all`, `overflow-x: hidden`, animated geometry or
  `@keyframes`; 27 `:focus-visible` rules); its only hits, 13 uppercase labels, are house style
  that one Floor rule would misflag. It needs npm, puppeteer-core and Chrome where the project has
  no JS toolchain by rule; headless screenshots and the design critic already give the browser
  check and the fresh reviewer. Its description would fire on every new screen, competing with
  `frontend-design`.

## 2026-11-01 — [agent-sleep](https://github.com/mocodainteractive-pixel/agent-sleep)
- **Source:** MIT, created 29 Oct 2026: a SessionEnd hook turns each transcript into memory files
  via background `claude -p`; a daily script checks each memory's `source:` and runs its
  `verify:` command; entries expire after `ttl_days` (default 30).
- **Verdict:** rejected; no ideas adopted.
- **Reason:** its source check, run over 39 real memories, found 0 stale (10 "missing" were all
  false alarms: paths relative to another repo, partial paths, URL fragments, a file on the remote
  branch but not the lagging checkout); verifying a named file at the moment of use already covers
  it. TTL expiry is wrong for traps and decisions, which stay true until the code changes. The
  hook would start an unsupervised background Opus run with Bash, Write and Edit for each of ~38
  sessions in 3 days, and needs a `settings.json` edit. Running each memory's `verify:` with
  `bash -c` daily turns a planted memory into a daily command.

## 2026-11-01 — [T3 Code](https://github.com/pingdotgg/t3code) (v0.1.6)
- **Source:** found via an [install review](https://aiparabellum.com/t3-code-claude-code-install-review/).
- **Verdict:** rejected; no ideas adopted.
- **Reason:** a visual front end over an agent already here (threads, approvals, diff panel,
  remote pairing). Claude Code's own desktop Code tab gives all of that plus what this workflow
  depends on and T3 Code lacks: cross-session messaging, side sessions and worktrees, the task
  list and wrap-up, Remote Control. Against it: new threads default to Full access, skipping the
  auto-mode classifier that sent settings and scheduled-task edits to the owner; telemetry on by
  default; the Agent SDK route may burn the 5-hour limit faster (unmeasured); v0.1.6, "very
  early" by its own README; its "no data to T3" claim is the maker's own, unaudited.

## 2026-11-01 — Reddit feedback #2 (review-loop hardening)
- **Verdict:** adopted.
- **Reason:** hand-offs between sessions were chat messages, leaving nothing on disk to read or
  veto; rejections lived only in one session's history; a change was checked for landing, not for
  meeting its goal. Now: proposal files, this file, and a fresh-subagent check of each diff.

## 2026-11-01 — Reddit feedback #1 (rules pile up until they contradict)
- **Verdict:** adopted.
- **Reason:** there was no record of why each rule existed and nothing that removed one. Now: a
  changelog, a line and word budget, and a monthly deletion pass. The suggestion to remove a rule
  and see whether results get worse is not adopted yet: it needs a quality measure (above).

## 2026-11-01 — [wheresryan22/anatomy](https://github.com/wheresryan22/anatomy)
- **Verdict:** partly adopted.
- **Reason:** its skill did not fit: it needs Node and Chrome where the main project has no JS
  toolchain, its pages are about 1 MB, and its visual style clashes with the project's existing
  design system. Adopted: size a task before starting, and 2x close-up crops of a changed region
  for the design-critic agent. Its staleness and exit-code checks were already covered here.

## 2026-11-01 — [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill)
- **Verdict:** adopted, owner-typed only.
- **Reason:** a whole-codebase audit that per-change `/security-review` does not give. Set to
  `disable-model-invocation` and never scheduled, because a standard run is many agents.

## 2026-11-01 — improve-codebase-architecture, from [mattpocock/skills](https://github.com/mattpocock/skills)
- **Verdict:** adopted (monthly, owner-typed; a scheduled task runs its scan-and-report half).
- **Reason:** finds deepening opportunities that per-feature review does not; adapted to read a
  project knowledge bundle.

## 2026-11-01 — [pbakaus/impeccable](https://github.com/pbakaus/impeccable)
- **Verdict:** not adopted after a trial run.
- **Reason:** v4.8.0, telemetry off, against four pages of a local server. Its detector found
  nothing the existing design review had not, and its main warning flagged a background colour
  the owner had deliberately chosen. Its one real lead (policy pages running about 100 characters
  a line) was kept as a note.

## 2026-10 — two token-saving / optimizer plugins
- **Verdict:** not adopted.
- **Reason:** measured against the local usage log first: one assumed a 5-minute prompt cache
  where main sessions held one hour, the other's guards had zero hits. Reviewing them produced
  the session-size habits in `dev-workflow.md` instead.
