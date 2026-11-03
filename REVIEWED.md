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

## 2026-11-03 — Anthropic: Message threads (Messages API, public beta)
- **Source:** Anthropic's article. With a `thread` parameter a client sends the whole
  conversation once, then only the new messages plus the previous response's ID. Threads are held
  encrypted in memory and expire 5 minutes after the last request. On by default for most Claude
  Code users, per the article.
- **Verdict:** no change; nothing to adopt. It is already on.
- **Reason:** it changes latency, not cost, and the session-size rules are about cost.
  - Median time to first token is about 35% lower for 500k–1M-token requests (the article's
    figure).
  - Claude "still reads the full conversation on every turn", so token use and rate limits are
    unchanged. Turns over 400k context still cost about 3x a turn under 200k, so the 300k nudge
    and "unrelated work starts in a new session" stay. Faster long sessions are not cheaper long
    sessions; decline a proposal to relax those rules unless `claude-cost` shows the per-turn
    cost of large contexts has fallen.
  - The 5-minute expiry is separate from the prompt cache, which main sessions hold for an hour.

## 2026-11-03 — hook-everything (Vumb-VibeCoder/hook-everything, `953e486`)
- **Source:** v5.1, MIT, created that day, 11 commits, 11 stars: 13 copywriting and persuasion
  skills (about 100 KB of SKILL.md) and `tools/slop_scan.py`, a 46 KB stdlib scanner. The "hooks"
  are marketing hooks, not Claude Code hooks. Third repo reviewed from this author, after
  longview-skills and your-token (both rejected).
- **Verdict:** rejected.
- **Reason:** it serves no coding stage, and what it does for copy is already here or would fight
  the house style.
  - Copy is covered: the owner's standard for written English is `better-clear-language`
    (ASD-STE100), and the design-critic agent has a `copy` row. A persuasion pipeline is the
    opposite of what a privacy or standards page is for.
  - Thirteen skills widen triggering ("drafting or auditing copy" would compete with
    `better-clear-language` on every docs turn), the reason other large bundles were rejected.
  - The scanner would flag our own style: rule 15 scores bold-lead bullets as slop, a form
    proposals and this file use on purpose.
  - It is hours old, with no outside users.
- **Idea noted, not proposed:** `--hidden` reports zero-width, bidi, tag-block and lookalike
  characters, a real check for text from outside (pasted posts, fetched pages, a plugin's
  SKILL.md), since tag-block characters can hide instructions from a person. If wanted, a few
  lines of our own stdlib Python, not this file.

## 2026-11-03 — AI Parabellum: "Karpathy CLAUDE.md guidelines" tested (article, 1 Nov)
- **Source:** a test of forrestchang/andrej-karpathy-skills, a single CLAUDE.md of four rules
  (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution). Its author is
  `forrestchang`, not Karpathy; last commit April 2026, licence unclear.
- **Verdict:** nothing to adopt; no change.
- **Reason:** the two behaviours it changed are ones the stages already require.
  - Test: 4 tasks × 3 runs with the file and 3 without, on a tiny Node project, no other
    instructions. All hidden tests passed both ways; 274 s against 281 s, $2.56 against $2.69.
    With the file, 2 of 3 runs asked before coding on the vague request, and all 3 added a
    regression test on the messy file (none did without). No difference on the clear bug.
  - Asking first is stage 2 (brainstorming); a regression test is stage 4 (TDD, red run quoted);
    "surgical" and "simple" are stage 6 `simplify` and the agents' "do only what the brief asks".
  - Measured against a bare session; ours load a workflow, a project CLAUDE.md and skills, so the
    marginal effect would be smaller. The source is weak: n=3 per setup, a commercial listings
    site with an unnamed byline.
- **Noted:** "state your assumptions and ask when unclear" is the one rule with a measured effect,
  and stage 2 covers it only when a session reaches stage 2. Watch the scorecard's `shrunk`
  share; not worth a rule now.

## 2026-11-03 — Laracraft: Claude code review in GitHub Actions with a subscription (article)
- **Source:** a blog post setting up `anthropics/claude-code-action@v1` on `pull_request`,
  authenticated with a `claude setup-token` OAuth token so reviews count against a Pro or Max
  plan. Opus, `gh pr` tools, high-confidence findings only.
- **Verdict:** not adopted.
- **Reason:** it reviews pull requests, and our work rarely goes through one.
  - The main project integrates by pushing a branch to main: 921 commits in a month, 13 PRs, no
    GitHub Actions. A PR trigger would see a small fraction of the code.
  - Stage 6 already reviews every change before it lands. A CI review after the push would repeat
    it on Opus against the same plan limits (the article says they are shared).
  - One test, with planted bugs: it caught the three it was built to catch, with "detection rates
    on real code not established".
- **Ideas noted, not proposed:**
  - Background subagents in a headless run end with a false "No findings": the author reports the
    official code-review plugin finished green in 4–37 seconds because its subagents were still
    running. If a review ever moves into a scheduled or `claude -p` run, forbid background agents
    and require a turn count before trusting "no findings".
  - A subscription OAuth token as a repo secret is long-lived and tied to one person's plan; the
    article itself says teams should use an API key.
  - The action restores CLAUDE.md from the base branch, so a PR cannot change the rules it is
    reviewed against; a good property if this is ever adopted.

## 2026-11-03 — fatsearch (fatsearch/fatsearch, `b5bfdd3`)
- **Source:** a Rust CLI plus MCP server that "reads the web for agents". MIT or Apache-2.0, 17
  days old, 52 stars; came from a subreddit digest.
- **Verdict:** not adopted. A trial is possible if WebFetch's 403s start to block real work.
- **Reason:** its headline saving is measured against a baseline we don't use.
  - "81× less context" is against tools that dump the page (Firecrawl, Jina, mcp-server-fetch).
    WebFetch already has a small model read the page and return only an answer. Its own agent
    test compares with Firecrawl MCP, not WebFetch, and even there scored 50/51 against 51/51 and
    was slower at the tail (43.8 s against 21.5 s).
  - The real gain is reach: JS rendering and paid unblockers (Oxylabs, Bright Data, Decodo) for
    JS shells, captchas and 403s. Here, over 30 days: about 1,270 WebFetch calls and about 210
    "status code 403" results (rough grep counts). How many blocked a task is unmeasured.
  - It widens the injection surface: WebFetch's summariser stands between raw page text and the
    main model; fatsearch returns raw sections into context. The useful parts need a paid key.
- **Ideas noted, not proposed:** `fats setup` takes the key through a one-time localhost form
  behind a random token, so it never enters the chat, a good pattern for any tool needing a
  secret. A trial would reread the month's 403 URLs through `fats` and count what it reads with no
  paid key.

## 2026-11-03 — r/ClaudeWorkflows: plan review skill + context management (Reddit, `/plan-grind`)
- **Source:** a subreddit digest of a comment with a low score and no replies; the `/plan-grind`
  skill it names is not published.
- **Verdict:** nothing to adopt; no change.
- **Reason:** every step is already here, usually stronger.
  - `/plan-grind` has Claude critique its own plan. Stage 3 dispatches `plan-reality-check`, which
    runs in a fresh context with none of the planner's view and has caught duplicates and
    contradictions a same-context self-review missed.
  - Turning repeated instructions into skills is stage 9 `/retro` and "When a skill is added".
  - `/compact`, a new session per task and handoffs are the session-size rules.
  - Evidence: the author's impression only.

## 2026-11-03 — AI Parabellum: "Matt Pocock's Skills for Claude Code" (article, 31 Oct)
- **Source:** a hands-on test of mattpocock/skills v1.3.2 (27 skills) on Sonnet.
- **Verdict:** nothing to adopt; no change.
- **Reason:** the skills tested duplicate stages we fill, and its numbers argue against adding
  them. One run per task on a toy store, all correct with and without a skill:

  | Task | Plain | With the skill | Cost |
  |---|---|---|---|
  | Bug fix | $0.08, 20s | `/diagnosing-bugs`: $0.12, 28s | 1.5x |
  | Feature | $0.08, 20s | `/tdd`: $0.32, 90s | 4x |
  | Planning | $0.08, 29s | `/grill-me`: $0.23, 83s | about 3x |

  - Only gain: `/grill-me` asked 20 questions instead of 9, and in one run pushed an over-built
    design. n=1, a commercial listings site with no named author.
  - Counterparts here: `/tdd` is `superpowers:test-driven-development` (stage 4),
    `/diagnosing-bugs` is `superpowers:systematic-debugging`, `/grill-me` is
    `superpowers:brainstorming` plus `GRILLING.md`. Installing them adds competing triggers.
  - The numbers support the rule that stages 1–3 shrink for a known fix.
- **Caution noted:** the official plugin ships `improve-codebase-architecture`, and our adapted
  fork lives in `~/.claude/skills`. A second install route duplicates every skill; never install
  the plugin beside the fork.

## 2026-11-03 — unbuilt (vtrifonov/unbuilt, `bf053c9`)
- **Source:** plugin v0.1.0, MIT, 12 days old, 4 stars: a Node 22 validator and three skills
  (extract, build, validate) for publishing software as a spec instead of code.
- **Verdict:** rejected.
- **Reason:** a format for sharing a product without its source, not a development workflow; no
  project here asks that.
  - Extract and build are not among stages 1–9, and the products are shipped, not ideas to give
    away.
  - Its spec shape (requirement IDs with MUST/SHOULD/MAY, Given/When/Then scenarios, milestones
    with "done when") is what `writing-plans` already produces; a second format would compete.
  - It is well built: it treats the instance as untrusted input, never publishes, and keeps an
    opt-in redaction gate. This is not a quality rejection.
- **Ideas noted, not proposed:**
  - "Every MUST has a scenario that cites it", checked by a script: a public-claims parity check
    here already goes further, since it asks the code.
  - Dated evidence with `Expires:` lines: declined twice already (longview-skills, Reddit
    feedback #1). Traps stay true until the code changes.
  - A mechanical leak scan before publishing (emails, IPs, hostnames, home paths, secret shapes,
    masked output). The public copy's re-clean is a hand grep; `scripts/lib/redaction.mjs` (MIT)
    could back a check, but only if a push ever leaks something. None has.

## 2026-11-03 — lean-agents (Lean-LLM/lean-agents, `1baffe5`)
- **Source:** 2 weeks old, 24 commits, 6 stars, no licence: a cross-tool prompt pack (OpenCode,
  Codex, Pi, Command Code, Claude Code).
- **Verdict:** rejected.
- **Reason:** the headline claim is unbacked and the parts we already have.
  - "~66% faster, ~44% fewer tokens" has no benchmark, method or data; its own Limits line says
    no live agent run is implied.
  - The orchestrator rule conflicts with ours: the primary may edit only one-line fixes and must
    delegate the rest to a "CODER" subagent. Stage 4 decides when to dispatch. Forcing every
    multi-file change into fresh contexts is not a demonstrated saving.
  - Part of AGENTS.md is incoherent ("HarnessMM", "certify graph hash … via the request ledger")
    and costs tokens every turn. It denies questions and to-dos outright (OpenCode config),
    removing the owner's checkpoints.
  - No licence, so nothing can be copied. The Claude Code install is two agent files plus
    `@AGENTS.md`, with tool names (`read_file`) that are not Claude Code's.
- **Ideas noted, not proposed:** a "same behaviour, fewer lines?" pass is stage 6 `simplify`;
  "revisit assumptions after three failed fixes" is systematic-debugging. Subagents returning a
  fixed JSON manifest (changes, verify with exact command and exit, blockers) might shrink what a
  dispatch returns; unmeasured, and dispatches here already demand a quoted red run and exit codes.

## 2026-11-02 — software-audit-skill (luigimorel/software-audit-skill, `2b6eaa0`)
- **Source:** frontmatter name `audit-skill`, titled "Vibe App Audit": a read-only security and
  privacy audit for fast-built web and mobile apps. 15.6 KB SKILL.md plus ten references.
- **Verdict:** rejected; no ideas adopted.
- **Reason:**
  - Both security tiers are covered: `security-review` per change (stage 6) and `/security-audit`
    for the whole codebase; Supabase RLS by the `supabase` skills.
  - Its triggers are broad ("review", "harden", "is this safe to ship") and would compete with
    `security-review`.
  - Its README installs to `.agents/software-audit-skill/`, which Claude Code does not load, and
    the frontmatter name does not match the folder.

## 2026-11-02 — thepmcode decision-support (Anmoll-W/thepmcode-skills, `0deee03`)
- **Source:** `skills/decision-support`, 9.5 KB SKILL.md plus eight references (about 70 KB), with
  four modes: EVALUATE (a startup scorecard and kill criterion), GRILL, INVERT, CHALLENGE.
- **Verdict:** rejected; no ideas adopted.
- **Reason:**
  - No demand: owner prompts across all project transcripts hold no request to grill, pre-mortem
    or red-team an idea; every match was pasted or system text.
  - GRILL is `superpowers:brainstorming` plus `GRILLING.md`; INVERT is brainstorming's first
    step; EVALUATE's startup scorecard has no use here.
  - Its description fires on "should we build this" and would compete with stage 2.

## 2026-11-02 — longview-skills (Vumb-VibeCoder/longview-skills, `d1ff7f1`)
- **Source:** 40 skills (about 180 KB of SKILL.md) in core, coding, finance, design and ui, with
  stdlib scanners and a router; each asks "will this hold up in a few years?".
- **Verdict:** rejected; no ideas adopted.
- **Reason:**
  - The coding half duplicates the workflow: diff-review and ai-code-audit are stage 6
    (ai-code-audit's "break the code and see the test fail" is stage 4's red run);
    security-durability is `security-review`; adr-writer is the bundle's `Decision` concepts;
    rollback-path is the `--dry-run` rule; convention and reuse checks are plan-reality-check.
  - Forty skills widen triggering.
  - Its evidence is self-graded: the judge wrote the tasks and rubric, skills were patched after
    seeing the tasks, mostly on Haiku; the author calls it a hint.
  - Assumption tripwires (a check command, expiry and owner) are the only new idea; one-off
    scheduled checks do this here, with no missed tripwire to justify a ledger.

## 2026-11-02 — your-token (Vumb-VibeCoder/Your-token, `39d3533`)
- **Source:** a skill plus a stdlib ledger. Claude estimates each turn's weighted tokens against a
  guessed 5-hour budget and a context meter, and writes `HANDOFF.md` before either runs out.
- **Verdict:** rejected; already covered by measurement.
- **Reason:**
  - This setup measures: OTel telemetry and `claude-cost` record real tokens and cost per
    request; the context nudge fires at 300k and 500k.
  - Its cache claim is wrong here: it says a pause over 5 minutes expires the cache, but the main
    thread's cache held an hour (44 of 45 gaps of 10–60 minutes, 29–31 Oct). cctoken-saverr made
    the same assumption.
  - It skips the weekly limit, the one that bounds a Max account.
  - It calls its script every turn, and `HANDOFF.md` repeats what transcripts keep.

## 2026-11-02 — Overflow (Nitjsefnie/Overflow, `5e3e88e`)
- **Source:** a mutual-credit ledger: spend spare LLM subscription capacity fixing strangers'
  open-source issues, earn points on merge, spend them to get your own issues worked. GitHub
  sign-in; registering a repo grants `admin:repo_hook` or installs its App.
- **Verdict:** rejected; an exchange, not a workflow tool.
- **Reason:**
  - Nothing to put on it: some projects are confidential, and the main project's code, data
    and deploy rules belong in one owner's hands.
  - Earning means running strangers' issue text and "Done when" commands, which its own docs say
    to sandbox without credentials: a separate machine, not this one.
  - Spare capacity is unmeasured: about $509 API-equivalent in four days (29 Oct–2 Nov) with the
    weekly limit in play. The subscription terms for paid-for-points work are unchecked.

## 2026-11-02 — jolitz (superlab-by-supbrt/jolitz, `d08e475`)
- **Source:** a Claude Code project you open to administer servers over SSH, often as root:
  housekeeping, audits, incident triage, fleet updates. A 1,742-line PreToolUse guard blocks
  disk-wiping, boot-loader, SSH-lockout and power-off commands, and fails closed.
- **Verdict:** rejected; one idea adopted.
- **Reason:** nothing to administer: the main project runs on a managed VPS with no root, and the
  provider patches the OS. It also updates itself on every session start (the guard between
  Claude and root would change without review) and needs a passphrase-less SSH key per server.
- **Idea adopted (2 Nov):** its guard is the mechanical form of rules kept only in memory. The
  rule "never empty the production cache" (it holds a replay guard, locks and rate limiters)
  had no hook; a user-level hook now refuses that command when sent over SSH, beside an existing
  one that refuses a dangerous framework flag.

## 2026-11-02 — Sketchy (ddkbs/sketchy, `a480651`)
- **Source:** a layout engine for hand-drawn, interactive diagrams, shipped as a chat skill (4 KB)
  and a desktop MCP extension.
- **Verdict:** rejected.
- **Reason:**
  - No demand: no owner prompt in the dashboard projects' transcripts asks for a diagram; same need
    test as diagram-design.
  - The chat skill loads `sketchy.js` from a CDN branch and follows the current minor version, so
    whatever one maintainer (15 stars) publishes runs beside the scene, which in some
    projects could hold confidential figures.
  - One-off diagrams are covered by the chat's visualize tool and `artifact-diagramming`.

## 2026-11-02 — "context sockets" skill-sharing post (Reddit)
- **Source:** "Sharing Claude skills across clients without forking them". Skills hold generic
  guidance; a *context socket* names a document in the client's knowledge base instead of stating
  client facts; a *process socket* names how the business does a step, with a default line.
- **Verdict:** no change; the pattern is already how the workflow is built.
- **Reason:** process sockets with defaults are the stages, with each project's `## Workflow`
  section supplying substitutions (`check-names.py` checks every project fills them in); context
  sockets are the knowledge bundles and CLAUDE.md. Shared socket names across authors do not
  apply to one owner.
- **The fork problem it describes is real here, once:** improve-codebase-architecture is "heavily
  adapted" from mattpocock/skills@4ae2317. If upstream changes, the post's fix is right: restore
  upstream's SKILL.md and move local adaptations into a file it points to.
- **Found while checking:** better-clear-language had no provenance comment, which would have left
  it untracked by the monthly upstream check; fixed.

## 2026-11-02 — AlanChen4/skills (`798fe2d`)
- **Source:** better-clear-language, better-codex-superfan, better-one-by-one, better-walkthrough.
- **Verdict:** partly adopted. better-clear-language is adopted for text colleagues read in
  dashboards (2 Nov, after a trial); the other three are rejected.
- **Reason:**
  - **better-clear-language** (2.9 KB plus an 84-line `check_text.py`, no network): a plain-English
    (ASD-STE100-style) pass with a ban list of filler, em dashes and rhythmic triples that keeps
    required terms and exact names. Dashboard tooltips and how-to text are read by colleagues, and
    no project had a writing rule. No recorded complaint, so it began as a trial.
  - **Trial:** six of 76 labelled tooltips in one dashboard were rewritten in a scratch file. The
    checker found 5 em dashes and one "actually" in the originals and passed the rewrite.
    Sentences went from 20.6 to 13.6 words, the text from 413 to 434 words (+5%), every number
    kept. The first pass dropped one fact and turned "not all virgin" into "many"; comparing
    against the original caught both, which is why the project line requires a fact check. The
    owner judged it better and adopted it.
  - **better-walkthrough:** interactive D2 diagrams of code; needs `d2`, Node and `npm ci`, and
    explains code to developers where the audience reads a dashboard. Same need test as
    diagram-design.
  - **better-one-by-one** (497 bytes): numbers items `(i/N)`; the app's task list shows progress.
  - **better-codex-superfan:** Codex only; `loop` and `schedule` cover recurring work.

## 2026-11-02 — master-console (cygaco/master-console v2.1.0, `ee72825`)
- **Source:** an "AI operating system" installed into a project's `.claude/`: a persona over
  Product, Engineering and Growth departments, builders in worktrees, a review gauntlet, a sprint
  lifecycle and a sleep/dream memory cycle. 235 slash commands, 78 hooks, 1,701 files, about 13 MB.
- **Verdict:** rejected. Same reasons as claude-vibe-squad.
- **Reason:**
  - It replaces the workflow (stages, plan-reality-check, review agents, knowledge bundles).
  - Hook load: 39 PreToolUse and 24 PostToolUse hooks, a Node process per hook on nearly every
    call, overhead unmeasured.
  - It writes into the project: copies its manifest into `.claude/`, compiles `settings.json` and
    merges into CLAUDE.md, which a test caps at 400 lines in the main project.
  - Cross-lab review needs Codex and Antigravity CLIs; Windows-first (PowerShell installer),
    unverified on macOS; AGPL-3.0.
- **Idea noted, not proposed:** "every policy names an enforcer or logs the gap", which the main
  project mostly does already (smoke tests, parity checks, a hook per costly rule).

## 2026-11-02 — claude-vibe-squad (mtarcure/claude-vibe-squad v2.0.0, `5392a48`)
- **Source:** a second orchestrator: a coordinator in a tmux control room dispatching Markdown
  task files to 71 specialists, each bound to Codex, Claude, Gemini or Grok in its own worktree,
  with cross-family review and an Obsidian memory. 1,551 files, about 14 MB.
- **Verdict:** rejected.
- **Reason:**
  - It replaces what stages 3–5 and the knowledge bundles do, so it would run beside them.
  - Four model families, one in use: cross-family review, its main quality claim, needs
    authenticated Codex, Gemini and Grok CLIs.
  - Its own security note is disqualifying: optional launchd agents run checkout code on every
    launch with the user's shell secrets, and one owns the authenticated browser; workers run with
    full user permissions.
  - Much of the skill set is smart-contract and bug-bounty auditing and game and audio design.
- **Ideas noted, not proposed:** check a branch's changed paths against the plan's Create/Modify
  list at integration (plan-reality-check checks the list, but nothing checks the diff against
  it). Its installer keeps hooks out of tracked files, so checking out another branch cannot change
  the code git runs; a tracked `core.hooksPath` is low risk while every branch is the owner's.

## 2026-11-02 — Comet (Shoot2Skoot/comet-in-claude, `astronaut-buddy` 0.1.0)
- **Source:** a desktop-app mod (about 1,400 lines of TypeScript): an animated astronaut above the
  prompt box with readouts for free context, weekly usage left, task progress and the git branch.
- **Verdict:** rejected as a workflow change; the owner may install it for fun.
- **Reason:**
  - Harmless from the source read: no network calls, no context-injecting hooks, no tokens. Its
    one side effect is `git status --porcelain=v1 --branch` at session start, after each turn and
    after every file-changing tool.
  - It adds little: context and spend are covered by the nudge and `claude-cost`; the weekly-limit
    readout is the only one not on screen elsewhere.
  - `git status` takes `index.lock`, so in a shared checkout a concurrent `git commit` can hit
    "index.lock exists" (unmeasured; `GIT_OPTIONAL_LOCKS=0` would avoid it, the plugin does not set
    it).
  - A day old, no licence; if installed, leave marketplace auto-update off.

## 2026-11-02 — open-design-agent-kit design systems (feimacode/open-design-agent-kit)
- **Source:** the kit's `claude-design-systems/`, importable into Claude's design systems.
- **Verdict:** rejected.
- **Reason:**
  - The main project already has a design system (a read-only base stylesheet plus its own), and
    UI work is judged against that. Same conclusion as taste-skill, hallmark and impeccable.
  - Most entries are brand clones (airbnb, stripe, apple, spotify, tesla, uber…); a page in
    another brand's look is impersonation, which the Artifact tool refuses to publish.
  - The generic styles add nothing a throwaway mockup needs. The kit claims 270+ skills and a
    plugin; only the design systems were reviewed.

## 2026-11-02 — cogit (erensrtky/cogit v0.31.0, `072eacc`)
- **Source:** a Claude Code plugin plus an npm CLI. It records each user message as a "thought
  commit" in `.cogit/`, links code commits with a `Thought:` trailer, and uses a headless
  `claude -p` on Haiku every 5 turns and at session end.
- **Verdict:** rejected for now.
- **Reason:**
  - Cost is not the problem: the guide puts it near a cent a session (the author's claim,
    unmeasured here).
  - Its git hooks fight the commit rules: `init` edits `prepare-commit-msg` and `pre-commit` and
    follows `core.hooksPath`, so in a project that tracks its hooks it edits tracked files, and the
    `pre-commit` block stages the record with every code commit, which breaks committing by path
    in shared checkouts.
  - Worktrees: under the commit policy each worktree keeps its own record; under the ignore policy
    sessions write the main checkout's gitignored `.cogit/`, changing no tracked file but putting
    concurrent writes in one folder (it keeps locks; unmeasured). Corrected 2 Nov; the first
    version said it wrote into the shared checkout.
  - It adds hooks to every turn (`UserPromptSubmit`, `Stop`, and `PreToolUse` on every Edit/Write,
    which injects "what was tried here" into the main thread, 82% of spend). It is committed and
    pushed by default, the headless sign-in has expired, and it reached v0.31 in six days.
  - The need is mostly covered by `Decision` concepts, verdict logs, red-run quotes and transcripts.
- **Worth revisiting:** the commit-to-reason link (`cogit why <sha>`) and rejected options shown
  before editing are the new ideas. Re-review past 1.0, trialled under the ignore policy in a
  project with no shared checkout.

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
