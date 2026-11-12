#!/usr/bin/env python3
"""PreToolUse Bash: refuse a recursive rm whose target is an unguarded variable, or the cwd/home/root.
Heredoc bodies are data (a file being written, a script for python), so they are skipped,
unless the heredoc feeds a shell (bash, sh, zsh, ssh), where the body runs."""
import json, re, sys

RM = re.compile(r"""(?:^|[;&|(`\n'"]|\b(?:then|do|else)\b)\s*(?:sudo\s+)?rm\s+((?:-[A-Za-z]+\s+)*)([^;&|\n`)]*)""")
BAD_LITERAL = {'.', './', '..', '/', '~', '~/', '*', './*', '$HOME', '${HOME}', '"$HOME"', '$PWD', '"$PWD"'}
HEREDOC = re.compile(r"""(?<!<)<<-?(?!<)\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1""")
SHELL = re.compile(r"""(?:^|[\s;&|(])(?:bash|sh|zsh|ssh)\b""")


def strip_heredocs(cmd):
    out, lines, i = [], cmd.split('\n'), 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        m = HEREDOC.search(line)
        if not m:
            continue
        delim, runs = m.group(2), bool(SHELL.search(line))
        while i < len(lines) and lines[i].strip() != delim:
            if runs:
                out.append(lines[i])
            i += 1
        if i < len(lines):
            out.append(lines[i])
            i += 1
    return '\n'.join(out)


def check(cmd):
    for m in RM.finditer(strip_heredocs(cmd)):
        flags, args = m.group(1), m.group(2)
        if not re.search(r'-[A-Za-z]*[rR]', flags):
            continue
        for a in args.split():
            if a in BAD_LITERAL:
                return f'rm -r of {a}'
            if '$' in a and ':?' not in a and not a.startswith("'"):
                return f'rm -r of {a}: an empty or failed variable would delete from the cwd. Write "${{VAR:?}}/..." instead'
    return None


if __name__ == '__main__':
    d = json.load(sys.stdin)
    why = check(d.get('tool_input', {}).get('command', ''))
    if why:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
              "permissionDecision": "deny", "permissionDecisionReason": why}}))
