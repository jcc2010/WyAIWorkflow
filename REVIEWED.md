# Reviewed outside sources

Every outside skill, plugin, repo or piece of feedback reviewed for this workflow, newest first,
with the verdict and why. Check here before reviewing a source again; a re-review needs a reason
the earlier verdict did not cover (a new version, a changed need). A verdict is about fit with
this setup, not the quality of the source.

**What is measured:** cost is, from local OpenTelemetry and a small report script. Quality is
not yet: skill evals wait on `claude plugin eval` leaving early access, and a monthly scorecard
(see the README) is planned, not built. Until it runs, an adoption is judged by feel and by
recorded defects in each project's knowledge docs, not by a measured effect.

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
