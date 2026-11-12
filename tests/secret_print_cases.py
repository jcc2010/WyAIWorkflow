"""Cases and a 30-day replay for refuse-secret-print.py. Usage: python3 -I tests/secret_print_cases.py <hook.py> [replay]
The replay prints counts, reasons and at most 60 characters of each refused command; never a tool result."""
import sys, json, glob, os, time, collections, importlib.util
spec = importlib.util.spec_from_file_location('g', sys.argv[1]); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
B = lambda c: ('Bash', {'command': c})
R = lambda p: ('Read', {'file_path': p})
cases = [
 (B('cat .env'), 1), (B('cat /home/u/app/.env'), 1), (B('head -5 .env.production'), 1), (B('cat .env.example'), 0),
 (B('cat .env.testing.example'), 0), (B('cat .env | cut -d= -f1'), 0), (B("sed 's/=.*//' .env"), 0),
 (B("cat .env | sed 's/=.*//'"), 0), (B('wc -l .env'), 0), (B('cat .env | wc -l'), 0),
 (B('grep DB_PASSWORD .env'), 1), (B("grep '^SUPABASE_SERVICE_ROLE_KEY' .env.local"), 1), (B('grep AUTH_SECRET .env'), 1),
 (B('grep -q DB_PASSWORD .env'), 0), (B('grep -c STRIPE_SECRET .env'), 0), (B('grep -E "^(DB_DATABASE|APP_ENV)" .env'), 0),
 (B('grep DB_DATABASE .env'), 0), (B('grep APPLE_PRIVATE_KEY_PATH .env'), 0), (B('grep MAPKIT_KEY_ID .env'), 0),
 (B("grep -v '^#' .env"), 1), (B('grep = .env'), 1), (B('grep DB_PASSWORD .env >/dev/null'), 0),
 (B('ssh host "grep DB_PASSWORD ~/app/.env"'), 1),
 (B('ssh host grep DB_PASSWORD app/.env'), 1),
 (B('cd x && grep DB_PASSWORD .env && echo ok'), 1),
 (B('security find-generic-password -s k -w'), 1), (B('K=$(security find-generic-password -s k -w); use "$K"'), 0),
 (B('security find-generic-password -s k'), 0), (B('gh auth token'), 1), (B('GH_TOKEN=$(gh auth token) gh api x'), 0),
 (B('env'), 1), (B('printenv'), 1), (B('env | grep -c FOO'), 0), (B('env FOO=1 cmd'), 0), (B('printenv PATH'), 0),
 (B('printenv OPENAI_API_KEY'), 1), (B('echo $GITHUB_TOKEN'), 1), (B('echo ${#GITHUB_TOKEN}'), 0),
 (B('echo ${GITHUB_TOKEN:+set}'), 0), (B('echo $HOME'), 0), (B('[ -n "$API_KEY" ] && echo set'), 0),
 (B('cat ~/.ssh/id_ed25519'), 1), (B('cat ~/.ssh/id_ed25519.pub'), 0), (B('cat ~/.ssh/config'), 0), (B('cat ~/.aws/credentials'), 1),
 (B("cat > .env <<'EOF'\nAPP_ENV=local\nEOF"), 0), (B("python3 - <<'EOF'\nopen('.env')\nEOF"), 0),
 (B("bash <<'EOF'\ncat .env\nEOF"), 1), (B('cp .env.example .env'), 0), (B('source .env'), 0), (B('ls -la .env'), 0),
 (B('git diff -- .env.example'), 0), (B('echo "grep DB_PASSWORD .env"'), 0),
 (R('/x/.env'), 1), (R('/x/.env.local'), 1), (R('/x/.env.example'), 0), (R('/x/app/env.php'), 0), (R('/x/.ssh/id_rsa'), 1),
 (R('/x/AuthKey_ABC.p8'), 1),
 # from the 30-day replay: filters and redactions that keep values out
 (B("env | grep -i playwright"), 1), (B("env | grep -E '^(BASE|TOKEN)'"), 1), (B("env | grep -E '^(DB_|APP_ENV)'"), 1),
 (B("env | grep -E '^(APP_ENV|APP_URL)='"), 0), (B("cat .env | grep -E '^(DB_DATABASE|APP_URL)='"), 0),
 (B('cat .env | grep DB_'), 1), (B('cat .env.testing | grep DB_DATABASE'), 0),
 (B("grep -n -i youtube .env | sed -E 's/=.*/=<hidden>/'"), 0), (B("grep -oE '^[A-Z_]*PASSWORD' .env"), 0),
 (B("grep -oE '^STRIPE_[A-Z_]+' .env | sort"), 0), (B("grep -E '^STRIPE_SECRET=' .env | cut -c1-15"), 0),
 (B("sed -i '' 's/^TMDB_TOKEN=.*/TMDB_READ_TOKEN=x/' .env"), 0), (B("sed -E 's/=.*/=<redacted>/' .env.test.local"), 0),
 (B("awk -F= '/^[A-Za-z_]+=/{print NR\": \"$1}' web/.env.test.local"), 0), (B("awk -F= '{print $2}' .env"), 1),
 (B("grep -o '^[A-Z_]*=' web/.env.test.local"), 0), (B("sed 's/:[^:@]*@/:***@/' .env.local"), 0),
 (B('grep -n MUSIC .env'), 1), (B('grep -n ^TMDB_READ_TOKEN= .env'), 1), (B('grep DEMO_PASSWORD .env'), 1),
 (B('head -20 .env.testing'), 1), (B('head -1 storage/mapkit.p8'), 0), (B('cat storage/mapkit.p8'), 1),
 (B("security find-generic-password -s x -w 2>/dev/null | tr -d '\\n' | gpg --batch -d f"), 0),
 (B('security find-generic-password -s x -w 2>&1'), 1),
 (B("ssh host 'cd app && grep ^GOOGLE_BOOKS_API_KEY= .env'"), 1),
 (B("ssh host 'cd app && grep ^GOOGLE_BOOKS_API_KEY= .env | sed -E \"s/=(.{4}).*/=\\1…/\"'"), 0),
]
wrong = [(c, v, g.check(*c)) for c, v in cases if bool(g.check(*c)) != bool(v)]
print('cases', len(cases), 'wrong', len(wrong))
for c, v, why in wrong: print('  want', v, c, '->', why)
if len(sys.argv) > 2:
    cut = time.time() - 30 * 86400; seen = set(); n = 0; hits = collections.Counter(); ex = collections.defaultdict(list); days = set()
    for f in glob.glob(os.path.expanduser('~/.claude/projects/*/**/*.jsonl'), recursive=True):
        if os.path.getmtime(f) < cut: continue
        for line in open(f, errors='ignore'):
            if '"tool_use"' not in line: continue
            try: d = json.loads(line)
            except Exception: continue
            for c in (d.get('message') or {}).get('content') or []:
                if isinstance(c, dict) and c.get('type') == 'tool_use' and c.get('name') in ('Bash', 'Read') and c.get('id') not in seen:
                    seen.add(c['id']); n += 1
                    why = g.check(c['name'], c.get('input') or {})
                    if why:
                        k = why.split('.')[0][:70]; hits[k] += 1; days.add(d.get('timestamp', '')[:10])
                        s = c['input'].get('command') or c['input'].get('file_path') or ''
                        if len(ex[k]) < 3: ex[k].append(s[:60].replace('\n', ' '))
    print(f'replay: {n} Bash/Read calls, {sum(hits.values())} refused, on {len(days)} days')
    for k, v in hits.most_common(25): print(f'  {v:4d}  {k}  e.g. {ex[k]}')
