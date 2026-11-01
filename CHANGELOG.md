# Changelog

Why each workflow rule exists, newest first. Every change to this repo adds an entry here, in
the same commit, with a reason it can cite or "reason not recorded", never an inferred one. The
monthly deletion pass reads this file to find rules whose reason no longer applies.

This public copy starts at its first sync; earlier history lives in the private source repo.

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
