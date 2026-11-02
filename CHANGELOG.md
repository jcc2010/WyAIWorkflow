# Changelog

Why each workflow rule exists, newest first. Every change to this repo adds an entry here, in
the same commit, with a reason it can cite or "reason not recorded", never an inferred one. The
monthly deletion pass reads this file to find rules whose reason no longer applies.

This public copy starts at its first sync; earlier history lives in the private source repo.

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
