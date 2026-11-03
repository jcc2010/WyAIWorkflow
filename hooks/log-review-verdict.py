#!/usr/bin/env python3
"""SubagentStop hook: append a plan-reality-check or design-critic verdict to
~/.claude/review-verdicts.jsonl, in the format dev-workflow.md gives, with "source": "hook".

Wired with matcher plan-reality-check|design-critic. Output it cannot parse is still
logged, as "verdict": "unparsed", so a dispatch never disappears. Fails open and silent: any
error writes nothing, prints nothing and exits 0."""
import datetime, json, os, pathlib, re, subprocess, sys

LOG = pathlib.Path.home() / ".claude/review-verdicts.jsonl"
AGENTS = ("plan-reality-check", "design-critic")
PRC_VERDICT = re.compile(r"^\s*\**Verdict:?\**:?\s*(ready|fix first)\b", re.I | re.M)
PRC_FINDING = re.compile(r"^\s*\d+\.\s*\[(?:Blocker|Major|Minor)\]", re.M)
PLAN = re.compile(r"[\w./~-]*plans/[\w.-]+\.md")


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content or [] if isinstance(b, dict))


def records(path):
    with open(path) as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                pass


def agent_transcript(data):
    """The subagent's own transcript: given directly, or beside the parent's."""
    for key in ("agent_transcript_path",):
        if data.get(key) and os.path.isfile(data[key]):
            return data[key]
    parent, agent = data.get("transcript_path"), data.get("agent_id")
    if parent and agent:
        p = pathlib.Path(parent)
        p = (p.with_suffix("") if p.suffix == ".jsonl" else p) / "subagents" / f"agent-{agent}.jsonl"
        if p.is_file():
            return str(p)
    if parent and os.path.isfile(parent) and "/subagents/" in parent:
        return parent
    return None


def brief_and_last(path):
    brief = last = None
    for r in records(path):
        msg = r.get("message") or {}
        if r.get("type") == "user" and brief is None:
            brief = text_of(msg.get("content"))
        elif r.get("type") == "assistant":
            content = msg.get("content")
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "SubagentHandback":
                    handback = (b.get("input") or {}).get("message")
                    if handback:
                        last = handback  # the report itself, delivered through the tool
            t = text_of(content)
            if t.strip():
                last = t
    return brief, last


def repo_name(path):
    """The main checkout's directory name for path's repo, or None outside a live repo."""
    if not os.path.isdir(path):
        return None
    r = subprocess.run(["git", "-C", path, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True, timeout=5)
    return pathlib.Path(r.stdout.strip()).parent.name if r.returncode == 0 and r.stdout.strip() else None


def project(cwd):
    return repo_name(cwd) or pathlib.Path(cwd).resolve().name


def repo_relative(plan, cwd):
    """The workflow gate matches plans by repo-relative path; make an absolute one relative."""
    plan = os.path.expanduser(plan)
    if os.path.isabs(plan):
        top = subprocess.run(["git", "-C", os.path.dirname(plan), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        if top and os.path.realpath(plan).startswith(os.path.realpath(top) + os.sep):
            return os.path.relpath(os.path.realpath(plan), os.path.realpath(top))
        if "/docs/" in plan:  # its checkout is gone: keep the part a repo-relative path would have
            return "docs/" + plan.rsplit("/docs/", 1)[1]
    return os.path.normpath(plan)


def parse(agent, message):
    if agent == "plan-reality-check":
        m = PRC_VERDICT.search(message)
        if m:
            return m.group(1).lower(), len(PRC_FINDING.findall(message))
    else:
        s = message.strip()
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
        try:
            j = json.loads(s[s.index("{"):s.rindex("}") + 1])
            if j.get("verdict") in ("ship", "polish", "rework"):
                return j["verdict"], len(j.get("findings") or [])
        except (ValueError, AttributeError):
            pass
    return "unparsed", None


def main():
    data = json.load(sys.stdin)
    agent = data.get("agent_type")
    if agent not in AGENTS:
        return
    path = agent_transcript(data)
    brief, last = brief_and_last(path) if path else (None, None)
    message = data.get("last_assistant_message") or ""
    if last and parse(agent, last)[0] != "unparsed":
        message = last  # a SubagentHandback report wins over a closing remark
    verdict, count = parse(agent, message)
    line = {"date": datetime.date.today().isoformat(), "agent": agent,
            "project": project(data.get("cwd") or os.getcwd()), "verdict": verdict}
    if count is not None:
        line["count"] = count
    if agent == "plan-reality-check" and brief:
        m = PLAN.search(brief)
        if m:
            line["plan"] = repo_relative(m.group(0), data.get("cwd") or os.getcwd())
            if os.path.isabs(os.path.expanduser(m.group(0))):  # the plan's own repo, not the caller's cwd
                line["project"] = repo_name(os.path.dirname(os.path.expanduser(m.group(0)))) or line["project"]
    line["source"] = "hook"
    with open(LOG, "a") as f:
        f.write(json.dumps(line) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
