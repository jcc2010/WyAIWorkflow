"""python3 -m unittest discover -s tests   (no network: gh is replaced, git repos are temporary)"""
import contextlib, datetime as dt, io, json, os, pathlib, subprocess, sys, tempfile, types, unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scorecard
import skip_audit as sa


def git(repo, *args, when="2026-11-10T12:00:00+00:00"):
    env = dict(os.environ, GIT_COMMITTER_DATE=when, GIT_AUTHOR_DATE=when, GIT_AUTHOR_NAME="t",
               GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name) / "proj"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        self.start = sa.START
        sa.START = "2026-11-05T00:00:00+00:00"
        self.addCleanup(setattr, sa, "START", self.start)

    def commit(self, message, path="f.txt", when="2026-11-10T12:00:00+00:00"):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(message + when)
        git(self.repo, "add", path, when=when)
        git(self.repo, "commit", "-q", "-m", message, when=when)
        return git(self.repo, "rev-parse", "HEAD")

    def reasons(self, plans=(), exists=lambda n: True):
        return {sha: reasons for sha, _, reasons in sa.offences(self.repo, "main", set(plans), exists)}


class Offences(Fixture):
    def test_missing_trailer_is_flagged(self):
        sha = self.commit("no trailer")
        self.assertIn("no valid Workflow: trailer", self.reasons()[sha][0])

    def test_commit_before_the_start_date_is_not_flagged(self):
        self.commit("old", when="2026-11-01T12:00:00+00:00")
        self.assertEqual(self.reasons(), {})

    def test_old_work_rebased_after_the_start_date_is_not_flagged(self):
        (self.repo / "r.txt").write_text("x")
        git(self.repo, "add", "r.txt")
        env = dict(os.environ, GIT_AUTHOR_DATE="2026-11-01T12:00:00+00:00", GIT_COMMITTER_DATE="2026-11-10T12:00:00+00:00",
                   GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m", "rebased"], check=True, env=env)
        self.assertEqual(self.reasons(), {})

    def test_merge_is_not_flagged(self):
        self.commit("Workflow: none (docs)")
        git(self.repo, "checkout", "-q", "-b", "side")
        self.commit("s\n\nWorkflow: none (docs)", path="s.txt")
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "merge", "-q", "--no-ff", "-m", "merge it", "side")
        self.assertEqual(self.reasons(), {})

    def test_none_and_shrunk_are_clean(self):
        self.commit("a\n\nWorkflow: none (docs)")
        self.commit("b\n\nWorkflow: shrunk 1-3 (known fix: typo)")
        self.assertEqual(self.reasons(), {})

    def test_full_with_no_plan_at_that_commit(self):
        sha = self.commit("a\n\nWorkflow: full (plan: docs/p.md)")
        self.assertTrue(any("not at this commit" in r for r in self.reasons(plans={"docs/p.md"})[sha]))

    def test_full_with_no_reality_check_line(self):
        self.commit("plan", path="docs/p.md")
        # the plan commit itself has no trailer; only the second is under test
        sha = self.commit("a\n\nWorkflow: full (plan: docs/p.md)")
        self.assertTrue(any("plan-reality-check" in r for r in self.reasons()[sha]))

    def test_full_with_plan_and_check_is_clean(self):
        self.commit("plan\n\nWorkflow: none (docs)", path="docs/p.md")
        self.commit("a\n\nWorkflow: full (plan: ./docs/p.md)")
        self.assertEqual(self.reasons(plans={"docs/p.md"}), {})

    def test_failing_run_grep_never_flags(self):
        self.commit("a\n\nno quoted run here\n\nWorkflow: shrunk 1-3 (known fix: x)")
        self.assertEqual(self.reasons(), {})

    def test_fixes_naming_no_issue_is_flagged(self):
        sha = self.commit("a\n\nFixes #9\nWorkflow: shrunk 1-3 (known fix: x)")
        self.assertTrue(any("#9" in r for r in self.reasons(exists=lambda n: False)[sha]))

    def test_unknown_issue_state_is_not_flagged(self):
        self.commit("a\n\nFixes #9\nWorkflow: shrunk 1-3 (known fix: x)")
        self.assertEqual(self.reasons(exists=lambda n: None), {})


class FakeGh:
    """Answers gh calls from a table; records them."""

    def __init__(self, visibility="private", has_issues=True, titles=(), fail_list=False, rows=None, fail_label=False, fail_create_on=()):
        self.calls, self.meta, self.titles, self.fail_list = [], dict(visibility=visibility, has_issues=has_issues), titles, fail_list
        self.rows, self.fail_label, self.fail_create_on, self.creates = rows, fail_label, fail_create_on, 0

    def __call__(self, *args):
        self.calls.append(args)
        ok = lambda out="": types.SimpleNamespace(returncode=0, stdout=out, stderr="")
        if args[0] == "api":
            return ok(json.dumps(self.meta))
        if args[:2] == ("issue", "list"):
            if self.fail_list:
                return types.SimpleNamespace(returncode=1, stdout="", stderr="boom")
            return ok(json.dumps(self.rows if self.rows is not None else [{"title": t, "body": ""} for t in self.titles]))
        bad = types.SimpleNamespace(returncode=1, stdout="", stderr="boom")
        if args[0] == "label" and self.fail_label:
            return bad
        if args[:2] == ("issue", "create"):
            self.creates += 1
            if self.creates in self.fail_create_on:
                return bad
        return ok()

    def created(self):
        return [c for c in self.calls if c[:2] == ("issue", "create")]


class Project(Fixture):
    def run_audit(self, fake, do_file):
        sa.run_gh, old = fake, sa.run_gh
        self.addCleanup(setattr, sa, "run_gh", old)
        return sa.audit_project(self.repo, "main", "o/proj", do_file, plans=set())

    def test_dry_run_files_nothing_and_makes_no_label(self):
        self.commit("no trailer")
        fake = FakeGh()
        result = self.run_audit(fake, False)
        self.assertEqual(fake.created(), [])
        self.assertFalse([c for c in fake.calls if c[0] == "label"])
        self.assertEqual(len(result["new"]), 1)

    def test_file_creates_one_issue_per_commit_with_sha_in_title(self):
        a, b = self.commit("one"), self.commit("two")
        fake = FakeGh()
        self.run_audit(fake, True)
        titles = [c[c.index("--title") + 1] for c in fake.created()]
        self.assertEqual(len(titles), 2)
        self.assertTrue(any(a[:12] in t for t in titles) and any(b[:12] in t for t in titles))
        self.assertTrue(all(sa.LABEL in c for c in fake.created()))

    def test_already_filed_commit_is_not_filed_twice(self):
        sha = self.commit("one")
        fake = FakeGh(titles=[f"Workflow skip: {sha[:12]} one"])
        result = self.run_audit(fake, True)
        self.assertEqual(fake.created(), [])
        self.assertEqual(result["new"], [])
        listed = next(c for c in fake.calls if c[:2] == ("issue", "list"))
        self.assertIn(("--state", "all"), list(zip(listed, listed[1:])))

    def list_call(self, fake):
        return next(c for c in fake.calls if c[:2] == ("issue", "list"))

    def test_removing_the_label_does_not_file_again(self):
        sha = self.commit("one")
        fake = FakeGh(titles=[f"Workflow skip: {sha[:12]} one"])
        self.run_audit(fake, True)
        self.assertNotIn("--label", self.list_call(fake))
        self.assertEqual(fake.created(), [])

    def test_editing_the_title_does_not_file_again(self):
        sha = self.commit("one")
        fake = FakeGh(rows=[dict(title="renamed", body=f"Commit {sha} on the integration branch")])
        self.assertEqual(self.run_audit(fake, True)["new"], [])
        self.assertEqual(fake.created(), [])

    def test_a_full_issue_list_files_nothing(self):
        self.commit("one")
        fake = FakeGh(rows=[dict(title="x", body="")] * scorecard.ISSUE_LIMIT)
        self.assertIn("issue list", self.run_audit(fake, True)["skipped"])
        self.assertEqual(fake.created(), [])

    def test_git_failure_is_skipped_with_its_reason(self):
        self.commit("one")
        with mock.patch.object(sa, "offences", side_effect=sa.GitError("git broke")):
            self.assertIn("git broke", self.run_audit(FakeGh(), True)["skipped"])

    def test_label_failure_files_nothing(self):
        self.commit("one")
        fake = FakeGh(fail_label=True)
        self.assertIn("label", self.run_audit(fake, True)["skipped"])
        self.assertEqual(fake.created(), [])

    def test_partial_create_failure_is_reported(self):
        self.commit("one"), self.commit("two")
        result = self.run_audit(FakeGh(fail_create_on=(1,)), True)
        self.assertEqual(result["filed"], 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_dry_run_says_it_is_over_the_cap(self):
        old, sa.MAX_PER_RUN = sa.MAX_PER_RUN, 1
        self.addCleanup(setattr, sa, "MAX_PER_RUN", old)
        self.commit("one"), self.commit("two")
        result = self.run_audit(FakeGh(), False)
        self.assertTrue(result["over_cap"])
        self.assertEqual(len(result["new"]), 2)

    def test_public_repo_is_skipped_even_when_filing(self):
        self.commit("one")
        fake = FakeGh(visibility="public")
        result = self.run_audit(fake, True)
        self.assertEqual(fake.created(), [])
        self.assertIn("public", result["skipped"])

    def test_repo_with_issues_off_is_skipped(self):
        self.commit("one")
        self.assertIn("issues", self.run_audit(FakeGh(has_issues=False), True)["skipped"])

    def test_unreadable_issue_list_files_nothing(self):
        self.commit("one")
        fake = FakeGh(fail_list=True)
        self.assertIn("issue list", self.run_audit(fake, True)["skipped"])
        self.assertEqual(fake.created(), [])

    def test_over_the_cap_files_nothing(self):
        old, sa.MAX_PER_RUN = sa.MAX_PER_RUN, 1
        self.addCleanup(setattr, sa, "MAX_PER_RUN", old)
        self.commit("one"), self.commit("two")
        fake = FakeGh()
        self.assertIn("cap", self.run_audit(fake, True)["skipped"])
        self.assertEqual(fake.created(), [])


class GitFailure(Fixture):
    def test_failing_log_raises_rather_than_reading_as_clean(self):
        self.commit("one")
        with self.assertRaises(sa.GitError):
            sa.offences(self.repo, "no-such-ref", set(), lambda n: True)

    def test_commit_git_cannot_read_is_an_error_not_a_missing_plan(self):
        self.commit("one")
        with self.assertRaises(sa.GitError):
            sa.reasons_for(self.repo, "0" * 40, "x\n\nWorkflow: full (plan: p.md)", {"p.md"}, lambda n: True)


class IssueExists(unittest.TestCase):
    def answer(self, returncode, stderr=""):
        unknown = []
        with mock.patch.object(sa, "run_gh", return_value=types.SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)):
            return sa.issue_exists("o/p", unknown)("9"), unknown

    def test_answers(self):
        self.assertEqual(self.answer(0), (True, []))
        self.assertEqual(self.answer(1, "HTTP 404: Not Found"), (False, []))
        self.assertEqual(self.answer(1, "HTTP 502"), (None, ["9"]))

    def test_gh_that_cannot_run_is_a_failed_answer(self):
        with mock.patch.object(sa.subprocess, "run", side_effect=subprocess.TimeoutExpired("gh", 60)):
            self.assertEqual(sa.run_gh("api", "x").returncode, 1)


class Main(unittest.TestCase):
    def test_no_checkout_and_no_remote_are_said_and_exit_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp)
            (home / "bare").mkdir()
            git(home / "bare", "init", "-q")
            out = io.StringIO()
            with mock.patch.object(sa.sc, "HOME", home), mock.patch.object(sa.sc, "projects", return_value={"gone": "main", "bare": "origin/main"}), \
                    mock.patch.object(sys, "argv", ["skip_audit.py"]), contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as stop:
                sa.main()
        self.assertEqual(stop.exception.code, 0)
        self.assertIn("gone: skipped: no checkout", out.getvalue())
        self.assertIn("bare: skipped: no GitHub remote", out.getvalue())


class Scorecard(unittest.TestCase):
    def test_slug_from_each_remote_form(self):
        for url in ("https://github.com/o/p.git", "git@github.com:o/p.git", "https://github.com/o/p"):
            with mock.patch.object(scorecard, "git", return_value=url + "\n"):
                self.assertEqual(scorecard.github_slug("r"), "o/p")
        with mock.patch.object(scorecard, "git", return_value=""):
            self.assertIsNone(scorecard.github_slug("r"))

    def issues_with(self, rows, returncode=0):
        start = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
        end = dt.datetime(2026, 12, 1, tzinfo=dt.timezone.utc)
        run = types.SimpleNamespace(returncode=returncode, stdout=json.dumps(rows))
        with mock.patch.object(scorecard, "github_slug", return_value="o/p"), mock.patch.object(scorecard.subprocess, "run", return_value=run):
            return scorecard.issues("r", start, end)

    def test_a_full_list_is_no_answer(self):
        row = dict(createdAt="2026-11-02T00:00:00Z", labels=[])
        self.assertIsNone(self.issues_with([row] * scorecard.ISSUE_LIMIT))
        self.assertEqual(self.issues_with([row])["bugs"], 0)

    def test_a_failed_list_is_no_answer(self):
        self.assertIsNone(self.issues_with([], returncode=1))


class LateDeclarations(unittest.TestCase):
    def test_counts_sessions_in_this_project_and_month_and_skips_bad_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = pathlib.Path(tmp) / "late.jsonl"
            log.write_text('{"date": "2026-11-05T10:00:00-0500", "project": "a", "session": "s1"}\n'
                           '{"date": "2026-11-05T10:01:00-0500", "project": "a", "session": "s1"}\n'
                           '{"date": "2026-11-06T10:00:00-0500", "project": "a", "session": "s2"}\n'
                           '{"date": "2026-11-06T10:00:00-0500", "project": "b", "session": "s3"}\n'
                           '{"date": "2026-12-06T10:00:00-0500", "project": "a", "session": "s4"}\n'
                           'not json\n')
            start = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
            end = dt.datetime(2026, 12, 1, tzinfo=dt.timezone.utc)
            with mock.patch.object(scorecard, "LATE", log):
                self.assertEqual(scorecard.late_declarations("a", start, end), 2)


class IssueSummary(unittest.TestCase):
    def row(self, n, created, *labels):
        return dict(number=n, createdAt=created, labels=[dict(name=l) for l in labels])

    def test_counts_and_recurrence(self):
        start = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
        end = dt.datetime(2026, 12, 1, tzinfo=dt.timezone.utc)
        rows = [self.row(1, "2026-10-20T00:00:00Z", "bug", "cause:safari-z"),   # before the month, sets the cause
                self.row(2, "2026-11-02T00:00:00Z", "bug", "cause:safari-z"),   # recurrence
                self.row(3, "2026-11-03T00:00:00Z", "bug", "cause:new-one"),    # first of its cause
                self.row(4, "2026-11-04T00:00:00Z", "bug"),                     # no cause
                self.row(5, "2026-11-05T00:00:00Z", "workflow-skip"),
                self.row(6, "2026-12-05T00:00:00Z", "bug", "cause:safari-z")]   # after the month
        self.assertEqual(scorecard.issue_summary(rows, start, end), dict(
            bugs=3, uncaused=1, recurrences=1, skips=1, causes={"new-one": 1, "safari-z": 1}))


if __name__ == "__main__":
    unittest.main()
