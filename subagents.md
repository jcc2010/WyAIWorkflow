# Subagent workflow — dispatching and checking a subagent

The controller's side of dev-workflow.md stage 4, and of any other dispatch. Subagents never
read this file or dev-workflow.md: they see the project's CLAUDE.md, their agent file and the
brief. A rule they must follow goes in the agent file or the brief.

## 1. Pick the agent
- **Explore** finds things. **plan-reality-check** checks a plan. **design-critic**
  reviews UI.
- **`implementer`** (pinned to Opus) writes code. Use it for the implementer step of
  `superpowers:subagent-driven-development`, in place of the general-purpose agent its
  templates name.
- **general-purpose** (Sonnet) does research, docs, and reviews that touch no data, auth or
  money path. A review of those paths goes to general-purpose with model "opus".

## 2. Write the brief
Every brief states:
- the goal, in the owner's words where there are some;
- the checkout path and branch;
- the files in scope;
- what is already ruled out;
- the acceptance check, as an exact command;
- the Co-Authored-By line and the Workflow: trailer, verbatim;
- "no deploy, ssh or rsync".

Point to logs by path; never paste them.

## 3. Check the return before you trust it
The agent returns the fixed report: status (PASS, UNVERIFIED, BLOCKED or FAILED), changes,
checks (each command with its exit code), red run, blockers. PASS needs a check that ran.
Then:
- read the trailers with `git log -1 --format=%B`;
- compare `git diff --stat <base>` with the files in scope;
- rerun the acceptance command yourself and read its exit status;
- log the verdict of a review agent, as dev-workflow.md says.

## 4. Parallel dispatches
One writer per set of files, each in its own worktree. Serialise shared build and test
commands: two test runs can share a database.

## Enforced
The workflow gate hook (`hooks/workflow-gate.py`) refuses a subagent's git stash, git add -A,
git add . and git commit -a in any repo. Main sessions are not affected.
