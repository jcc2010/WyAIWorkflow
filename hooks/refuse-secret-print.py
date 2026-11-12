#!/usr/bin/env python3
"""PreToolUse Bash and Read: refuse a call that would print a secret value into the transcript.

A *source* prints secrets: a Read of a .env file; cat/head/sed/grep/... of a .env file; env or printenv with no
argument; cat of a private key or credential file; security find-*-password -w; gh auth token; echo/printenv of a
secret variable. A source is allowed when it, or a later pipeline stage, keeps values out of the output:
  - a filter that names only full, non-secret keys   (grep DB_DATABASE .env, env | grep -E '^(APP_ENV|APP_URL)=')
  - a reduction to key names or redacted values       (cut -d= -f1, grep -o '^[A-Z_]*=', awk -F= '{print $1}',
                                                       sed 's/=.*/=<hidden>/', grep -q/-c/-l, wc, >/dev/null)
  - a consumer that never prints the value            (gpg, openssl, pbcopy; $(...) and backticks)
  - an in-place edit                                  (sed -i)
A prefix (DB_), a bare word (youtube, MUSIC) or any secret word (PASSWORD, SECRET, TOKEN, _KEY) is not a safe filter.
Heredoc bodies are data unless the heredoc feeds a shell, as in refuse-unguarded-rm.py. A parser error fails open."""
import json, re, shlex, sys

ENV_FILE = re.compile(r'(^|/)\.env(\.[\w.-]+)?$')
ENV_SAFE = re.compile(r'\.env(\.[\w-]+)?\.(example|dist|sample)$|\.env\.example$')
KEY_FILE = re.compile(r'(^|/)(id_rsa|id_ed25519|id_ecdsa|id_dsa)$|\.aws/credentials$|(^|/)\.netrc$|\.p8$|\.pem$|\.p12$')
SECRET_WORD = re.compile(r'(?i)((^|_)pass(word|wd|phrase)?($|_)|secret|token|private_key|api_?key|(^|_)key($|_))(?!_?(path|id|file))')
FULL_KEY = re.compile(r'[A-Z][A-Z0-9]*(_[A-Z0-9]+)+')
DUMPERS = {'cat', 'head', 'tail', 'less', 'more', 'bat', 'nl', 'xxd', 'od', 'strings', 'tac', 'base64', 'sort', 'uniq'}
SEARCHERS = {'grep', 'egrep', 'rg', 'sed', 'awk', 'cut'}
CONSUMERS = {'gpg', 'openssl', 'pbcopy'}
HEREDOC = re.compile(r"""(?<!<)<<-?(?!<)\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1""")
SHELL = re.compile(r"""(?:^|[\s;&|(])(?:bash|sh|zsh|ssh)\b""")
SUBST = re.compile(r'\$\((?:[^()]|\([^()]*\))*\)|`[^`]*`')
SSH_ARG = {'-i', '-p', '-o', '-l', '-F', '-J', '-E', '-b', '-c', '-m', '-L', '-R', '-D', '-W'}


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


def words(s):
    try:
        return shlex.split(s, comments=False)
    except ValueError:
        # an unclosed quote: the command was split on && or | inside a quoted ssh argument
        return [t.strip('\'"') for t in s.split()]


def prog_of(w):
    while w and (w[0] in ('sudo', 'command', 'builtin', 'nice', 'time') or re.fullmatch(r'[A-Z_]+=\S*', w[0])):
        w = w[1:]
    return (w[0].rsplit('/', 1)[-1], w) if w else ('', w)


def flags(w):
    return [a for a in w[1:] if a.startswith('-')]


def has_flag(w, letters, longs=()):
    return any((a.startswith('-') and not a.startswith('--') and set(a[1:]) & set(letters)) or a in longs for a in w[1:])


def pattern_of(w, files):
    """grep's pattern is its first positional argument (or every -e argument); the rest are files."""
    es = [w[i + 1] for i, a in enumerate(w[:-1]) if a in ('-e', '--regexp')]
    if es:
        return ' '.join(es)
    pos = [a for a in w[1:] if not a.startswith('-') and a not in files and not re.match(r'\d?>', a)]
    return pos[0] if pos else ''


def alternatives(pattern, limit=64):
    """Expand a grep pattern's groups and alternations into the plain strings it can match:
    ^APP_(NAME|URL)= -> APP_NAME, APP_URL; FEATURE_MEDIA(_CAST)? -> FEATURE_MEDIA, FEATURE_MEDIA_CAST."""
    p = pattern.replace('\\|', '|').replace('\\(', '(').replace('\\)', ')')
    alts = [a for a in re.split(r'\|(?![^()]*\))', p)]
    out = []
    while alts and len(out) < limit:
        a = alts.pop()
        m = re.search(r'\(([^()]*)\)(\?)?', a)
        if not m:
            out.append(a)
            continue
        opts = m.group(1).split('|') + ([''] if m.group(2) else [])
        alts.extend(a[:m.start()] + o + a[m.end():] for o in opts)
    return out if not alts else None


def key_safe(pattern):
    """A filter is safe when every string it can match is a full, non-secret key (prefixes and bare words are not)."""
    alts = alternatives(pattern)
    if not alts:
        return False
    for a in alts:
        k = re.sub(r'^\^|=$|\$$', '', a.strip().strip('\'"'))
        if not FULL_KEY.fullmatch(k) or SECRET_WORD.search(k):
            return False
    return True


def reduces(stage):
    """This pipeline stage keeps values out of whatever it is fed."""
    if re.search(r'(^|[^0-9&])>\s*[^&\s]', stage) or '>/dev/null' in stage.replace(' ', ''):
        return True  # stdout goes to a file, not the transcript
    prog, w = prog_of(words(stage))
    s = ' '.join(w)
    if prog in CONSUMERS or prog == 'wc':
        return True
    if prog == 'cut':
        if re.search(r"-d\s*['\"]?=", s) and re.search(r'-f\s*1(?![,\d-])', s):
            return True
        m = re.search(r'-c\s*1?-?(\d+)\b', s)
        return bool(m and int(m.group(1)) <= 20)
    if prog == 'sed':
        return bool(re.search(r"s/.*(=|:)[^/]*(\.\*|\.\+|\.\{|\[\^)", s)) and not has_flag(w, 'i')
    if prog == 'awk':
        return '-F=' in s.replace(' ', '').replace("'", '').replace('"', '') and not re.search(r'print[^}]*\$(0|2|[3-9])', s) and 'print' in s
    if prog in ('grep', 'egrep', 'rg'):
        if has_flag(w, 'v') and SECRET_WORD.search(pattern_of(w, [])):
            return True  # grep -v PASS drops the secret lines
        if has_flag(w, 'qclL', ('--quiet', '--count', '--files-with-matches')):
            return True
        if has_flag(w, 'o') and not re.search(r'=(\.|\[\^|\S*\*|\S*\+)', pattern_of(w, [])):
            return True
        return key_safe(pattern_of(w, []))
    return False


def safe_after(rest):
    return any(reduces(st) for st in rest)


def check_stage(w, rest, depth=0):
    prog, w = prog_of(w)
    if not prog:
        return None
    if prog == 'ssh':
        i = 1
        while i < len(w) and w[i].startswith('-'):
            i += 2 if w[i] in SSH_ARG else 1
        remote = ' '.join(w[i + 1:])
        if not remote or depth > 2 or safe_after(rest):
            return None
        return check_bash(remote, depth + 1)
    # a redirect target is written, not read: `cat > .env <<EOF` creates the file
    files = [a for i, a in enumerate(w) if i and not a.startswith('-') and not re.match(r'\d?>', a)
             and not re.fullmatch(r'\d?>>?|&>', w[i - 1])]
    envs = [f for f in files if ENV_FILE.search(f) and not ENV_SAFE.search(f)]
    tail = ' '.join(w)
    if envs and (prog in DUMPERS or prog in SEARCHERS):
        if prog == 'sed' and has_flag(w, 'i'):
            return None
        if prog in SEARCHERS and reduces(' '.join(a for a in w if a not in envs)):
            return None
        if safe_after(rest) or reduces(tail):
            return None
        pat = pattern_of(w, envs) if prog in SEARCHERS else ''
        named = [t for t in re.findall(r'[A-Za-z][A-Za-z0-9_]*', pat) if SECRET_WORD.search(t)]
        if named:
            return f'{prog} of {named[0]} in {envs[0]} prints its value. Use grep -q or grep -c to test it is set'
        return (f'{prog} on {envs[0]} can print a secret. Name full non-secret keys (grep -E "^(DB_DATABASE|APP_ENV)="), '
                f'or cut -d= -f1 for names, or sed "s/=.*/=<set>/" to redact')
    if prog in DUMPERS:
        keys = [f for f in files if KEY_FILE.search(f) and not f.endswith('.pub')]
        one_line = re.search(r'(^|\s)(-1|-n\s*1)(\s|$)', tail) and prog == 'head'
        if keys and not one_line and not safe_after(rest):
            return f'{prog} {keys[0]} prints a private key or credential'
    if prog == 'security' and len(w) > 1 and re.match(r'find-(generic|internet)-password', w[1]) and '-w' in w:
        if not rest:
            return 'security find-*-password -w prints the secret. Use it inside $(...) or pipe it straight into its consumer'
    if prog == 'gh' and w[1:3] == ['auth', 'token'] and not rest:
        return 'gh auth token prints the token. Use it inside $(...)'
    if prog in ('printenv', 'env') and len(w) == 1 and not safe_after(rest):
        return f'{prog} with no argument prints every secret in the environment. Filter by full key names, or cut -d= -f1'
    if prog == 'printenv' and any(SECRET_WORD.search(a) for a in w[1:]) and not safe_after(rest):
        return 'printenv of a secret variable prints its value. Test it with [ -n "$VAR" ]'
    if prog in ('echo', 'printf') and not safe_after(rest):
        for a in w[1:]:
            m = re.search(r'\$\{?([A-Za-z0-9_]+)', a)
            if m and FULL_KEY.fullmatch(m.group(1)) and SECRET_WORD.search(m.group(1)) and ':+' not in a and '{#' not in a:
                return f'{prog} ${m.group(1)} prints a secret. Test it with [ -n "${m.group(1)}" ] or ${{#{m.group(1)}}}'
    return None


def split_top(body):
    """Split on ; && || & newline into pipelines and on | into stages, outside quotes only."""
    pipes, stages, cur, q, i = [], [], '', None, 0
    while i < len(body):
        c = body[i]
        if q:
            cur += c
            if c == q:
                q = None
            elif c == '\\' and q == '"' and i + 1 < len(body):
                cur += body[i + 1]; i += 1
        elif c in '\'"':
            q = c; cur += c
        elif c == '\\' and i + 1 < len(body):
            cur += c + body[i + 1]; i += 1
        elif body.startswith('&&', i) or body.startswith('||', i):
            pipes.append(stages + [cur]); stages, cur = [], ''; i += 1
        elif c == '|':
            stages.append(cur); cur = ''
        elif c in ';\n' or (c == '&' and not cur.rstrip().endswith('>') and not body.startswith('&>', i)):
            pipes.append(stages + [cur]); stages, cur = [], ''
        else:
            cur += c
        i += 1
    pipes.append(stages + [cur])
    return pipes


def check_bash(cmd, depth=0):
    body = SUBST.sub(' SUBST ', strip_heredocs(cmd))
    for stages in split_top(body):
        for i, st in enumerate(stages):
            why = check_stage(words(st), stages[i + 1:], depth)
            if why:
                return why
    return None


def check(tool, inp):
    if tool == 'Read':
        p = inp.get('file_path', '')
        if ENV_FILE.search(p) and not ENV_SAFE.search(p):
            return f'Reading {p.rsplit("/", 1)[-1]} puts every secret in it into the transcript. Grep the non-secret key you need'
        if KEY_FILE.search(p) and not p.endswith('.pub'):
            return 'Reading a private key or credential file puts it into the transcript'
        return None
    if tool == 'Bash':
        return check_bash(inp.get('command', ''))
    return None


if __name__ == '__main__':
    try:
        d = json.load(sys.stdin)
        why = check(d.get('tool_name', ''), d.get('tool_input', {}))
    except Exception:
        why = None  # a parser bug must never block work: fail open
    if why:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
              "permissionDecision": "deny", "permissionDecisionReason": why}}))
