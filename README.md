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
- `check-names.py` runs before and after every edit to either file.

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
- In zsh, an unquoted glob that matches nothing aborts the whole command with `no matches
  found`. That error means the search never ran. It does not mean "not found".

## Publishing

Changes land in a private repo first. This public copy is cleaned and synced by hand
afterwards, never mirrored automatically.
