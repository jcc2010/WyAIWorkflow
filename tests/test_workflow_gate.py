"""The gate's bug marker, integration-branch refusal and late-declaration log. GATE names the hook
under test; default the installed one. No network."""
import json, os, pathlib, shutil, subprocess, tempfile, unittest

GATE = os.environ.get("GATE", str(pathlib.Path.home() / ".claude/hooks/workflow-gate.py"))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = pathlib.Path(self.tmp.name)
        self.repo = self.home / "proj"
        self.repo.mkdir()
        subprocess.run(["git", "-C", str(self.repo), "init", "-q", "-b", "main"], check=True)
        (self.repo / "CLAUDE.md").write_text("Follows dev-workflow.md\n")
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "-b", "work"], check=True)

    def hook(self, command):
        data = dict(tool_name="Bash", session_id="s", cwd=str(self.repo), tool_input=dict(command=command))
        run = subprocess.run(["python3", GATE], input=json.dumps(data), capture_output=True, text=True,
                             env=dict(os.environ, HOME=str(self.home), **getattr(self, "extra_env", {})))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, "", "the gate failed open")
        return json.loads(run.stdout)["hookSpecificOutput"]["permissionDecisionReason"] if run.stdout else None

    def declared(self):
        self.assertIsNone(self.hook('workflow-declare shrunk 1-3 "known fix: x"'))

    T = "Workflow: shrunk 1-3 (known fix: x)"
    M = "Bug: none\nWorkflow: shrunk 1-3 (known fix: x)"

    def g(self, *args):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, env=env)

    def late(self):
        f = self.home / ".claude/workflow-late-declarations.jsonl"
        return [json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []

    def tracked(self, *paths):
        for path in paths:
            f = self.repo / path
            f.parent.mkdir(exist_ok=True)
            f.write_text("x")
        self.g("add", *paths)
        self.g("commit", "-q", "-m", "tracked")
        for path in paths:
            (self.repo / path).write_text("changed")


class Gate(Base):
    def test_shrunk_with_no_marker_is_refused(self):
        self.declared()
        reason = self.hook(f"""git commit -m 'subject

{self.T}'""")
        self.assertIn("Fixes #N", reason)
        self.assertIn("Bug: none", reason)

    def test_bug_none_passes(self):
        self.declared()
        self.assertIsNone(self.hook(f"""git commit -m 'subject

Bug: none
{self.T}'"""))

    def test_fixes_passes(self):
        self.declared()
        self.assertIsNone(self.hook(f"""git commit -m 'subject

Fixes #12
{self.T}'"""))

    def test_second_m_passes(self):
        self.declared()
        self.assertIsNone(self.hook(f"git commit -m subject -m 'Bug: none' -m '{self.T}'"))

    def test_heredoc_passes(self):
        self.declared()
        self.assertIsNone(self.hook(f"""git commit -m "$(cat <<'EOF'
subject

Fixes #3
{self.T}
EOF
)\""""))

    def test_file_message_passes_and_is_refused_without_it(self):
        self.declared()
        good, bad = self.home / "good.txt", self.home / "bad.txt"
        good.write_text(f"subject\n\nBug: none\n{self.T}\n")
        bad.write_text(f"subject\n\n{self.T}\n")
        self.assertIsNone(self.hook(f"git commit -F {good}"))
        self.assertIn("Fixes #N", self.hook(f"git commit -F {bad}"))

    def test_trailer_option_passes(self):
        self.declared()
        self.assertIsNone(self.hook(f"git commit -m subject --trailer 'Bug: none' --trailer '{self.T}'"))
        self.assertIsNone(self.hook(f"git commit -m subject --trailer='Bug: none' --trailer '{self.T}'"))

    def test_marker_mid_sentence_does_not_count(self):
        self.declared()
        self.assertIn("Fixes #N", self.hook(f"""git commit -m 'subject

this Fixes #12 maybe, and Bug: none too
{self.T}'"""))

    def test_none_is_exempt(self):
        self.assertIsNone(self.hook("""git commit -m 'subject

Workflow: none (docs)' CLAUDE.md"""))

    def test_reused_message_is_exempt(self):
        self.assertIsNone(self.hook("git commit --amend --no-edit"))
        self.assertIsNone(self.hook("git commit -C HEAD"))

    def test_undeclared_commit_never_sees_the_marker(self):
        reason = self.hook("git commit -m subject")
        self.assertNotIn("Bug: none", reason)
        self.assertNotIn("Fixes #N", reason)


class IntegrationAndLate(Base):
    def test_shrunk_on_integration_is_refused(self):
        self.g("checkout", "-q", "-b", "main")
        self.declared()
        self.assertIn("stage 2", self.hook(f"git commit -m 'subject\n\n{self.M}'"))

    def test_shrunk_on_a_branch_passes(self):
        self.declared()
        self.assertIsNone(self.hook(f"git commit -m 'subject\n\n{self.M}'"))

    def test_none_on_integration_passes(self):
        self.g("checkout", "-q", "-b", "main")
        self.assertIsNone(self.hook("git commit -m 'subject\n\nWorkflow: none (docs)' CLAUDE.md"))

    def test_finishing_a_merge_on_integration_passes(self):
        self.g("add", "CLAUDE.md"), self.g("commit", "-q", "-m", "base")
        self.g("branch", "-q", "main")
        (self.repo / "w.txt").write_text("w"); self.g("add", "w.txt"); self.g("commit", "-q", "-m", "w")
        self.g("checkout", "-q", "main")
        (self.repo / "m.txt").write_text("m"); self.g("add", "m.txt"); self.g("commit", "-q", "-m", "m")
        self.g("merge", "-q", "--no-commit", "--no-ff", "work")
        self.declared()
        self.assertIsNone(self.hook(f"git commit -m 'merge\n\n{self.M}'"))

    def test_undeclared_commit_is_logged(self):
        self.hook("git commit -m subject")
        self.assertEqual([r["why"] for r in self.late()], ["commit refused: nothing declared"])

    def test_code_changed_before_first_declaration_is_logged_once_and_does_not_refuse(self):
        (self.repo / "a.py").write_text("x")
        self.declared()
        self.declared()
        self.assertEqual(len(self.late()), 1)
        self.assertEqual(self.late()[0]["files"], ["a.py"])

    def test_unstaged_first_file_keeps_its_whole_name(self):
        self.tracked("app.py", "my app.py")
        self.declared()
        self.assertEqual(self.late()[0]["files"], ["app.py", "my app.py"])

    def test_unstaged_docs_change_is_not_a_late_declaration(self):
        self.tracked("docs/gen.py")
        self.declared()
        self.assertEqual(self.late(), [])

    def test_refusal_offers_shrunk_only_for_a_known_fix(self):
        (self.repo / "a.py").write_text("x")
        self.g("add", "a.py")
        self.assertIn("declare full, or shrunk 1-3 for a known fix", self.hook("git commit -m 'subject\n\nWorkflow: none (docs)'"))

    def test_clean_declaration_and_markdown_are_not_logged(self):
        self.declared()
        self.assertEqual(self.late(), [])


class MessageSources(Base):
    """Only what becomes this commit's message counts (review findings 2, 3, 7)."""

    def test_marker_in_another_commands_heredoc_does_not_count(self):
        self.declared()
        self.assertIn("Fixes #N", self.hook(f"cat > /tmp/zz <<EOF\nBug: none\nEOF\ngit commit -m 'x\n\n{self.T}'"))

    def test_marker_in_another_commit_does_not_count(self):
        self.declared()
        self.assertIn("Fixes #N", self.hook(f"git commit -m 'a\n\nBug: none\n{self.T}' && git commit -m 'y\n\n{self.T}'"))

    def test_marker_in_a_pr_body_does_not_count(self):
        self.declared()
        self.assertIn("Fixes #N", self.hook(f"git commit -m 'y\n\n{self.T}' && gh pr create --body 'x\nFixes #3\n'"))

    def test_trailer_in_another_command_does_not_count(self):
        self.assertIn("nothing was declared", self.hook("echo '\nWorkflow: none (docs)\n' && git commit -m x"))

    def test_heredoc_with_quotes_and_parens_in_the_body_passes(self):
        self.declared()
        self.assertIsNone(self.hook(f"""git commit -m "$(cat <<'EOF'
fix "quoted" and don't (break)

Bug: none
{self.T}
EOF
)\""""))

    def test_file_dash_reads_its_own_heredoc(self):
        self.declared()
        self.assertIsNone(self.hook(f"git commit -F - <<'EOF'\nsubject\n\nBug: none\n{self.T}\nEOF"))
        self.assertIn("Fixes #N", self.hook(f"git commit -F - <<'EOF'\nsubject\n\n{self.T}\nEOF"))

    def test_piped_file_dash_fails_open(self):
        self.assertIsNone(self.hook("printf x | git commit -F -"))

    def test_semicolon_in_a_message_is_not_a_command_boundary(self):
        self.declared()
        self.assertIsNone(self.hook(f"git commit -m 'a; b && c\n\nBug: none\n{self.T}'"))

    def test_quoted_git_commit_and_heredoc_body_are_not_run(self):
        self.assertIsNone(self.hook("grep -n 'x; git commit -m y' f"))
        self.assertIsNone(self.hook("cat > f <<EOF\ngit commit -m oops\nEOF"))
        self.assertIsNone(self.hook("ls # git commit -m don't"))

    def test_no_edit_beside_a_message_is_checked(self):
        self.assertIn("nothing was declared", self.hook("git commit -m x --no-edit"))

    def test_attached_reuse_is_exempt(self):
        self.assertIsNone(self.hook("git commit -CHEAD"))

    def test_trailer_equals_form_counts(self):
        self.declared()
        self.assertIsNone(self.hook(f"git commit -m subject --trailer='Bug: none' --trailer='{self.T}'"))

    def test_attached_file_is_read(self):
        self.declared()
        (self.repo / "msg.txt").write_text(f"subject\n\nBug: none\n{self.T}\n")
        self.assertIsNone(self.hook("git commit -Fmsg.txt"))
        self.assertIsNone(self.hook("git commit --file=msg.txt"))

    def test_none_with_a_redirect_still_sees_the_staged_code(self):
        (self.repo / "a.py").write_text("x")
        self.g("add", "a.py")
        self.assertIn("this commit takes a.py", self.hook("git commit -m 'x\n\nWorkflow: none (docs)' > /tmp/zz 2>&1"))


class Targets(Base):
    """Which repo a commit is in (review finding 4)."""

    def test_unresolvable_target_skips_the_gate(self):
        for c in ('cd "$V" && git commit -m x', 'git -C "$V" commit -m x', "cd - && git commit -m x",
                  "cd `pwd` && git commit -m x", 'cd "$V" && cd sub && git commit -m x'):
            self.assertIsNone(self.hook(c), c)

    def test_absolute_cd_after_a_variable_is_judged(self):
        self.assertIn("nothing was declared", self.hook(f'cd "$V" && cd {self.repo} && git commit -m x'))

    def test_cd_in_a_subshell_does_not_leak(self):
        self.assertIn("nothing was declared", self.hook("(cd /tmp && ls); git commit -m x"))
        self.assertIn("nothing was declared", self.hook('(cd "$V"); git commit -m x'))

    def test_commit_inside_a_subshell_is_judged_there(self):
        self.assertIsNone(self.hook("(cd /tmp && git commit -m x)"))

    def test_declare_from_an_unresolvable_target_records_nothing(self):
        self.assertIsNone(self.hook('cd "$V" && workflow-declare shrunk 1-3 "known fix: x"'))
        self.assertIn("nothing was declared", self.hook("git commit -m x"))


class FirstDeclaration(Base):
    """Cost and counting of the late pass (review findings 1, 5, 6)."""

    def shim(self):
        bin_dir, self.calls = self.home / "bin", self.home / "git-calls"
        bin_dir.mkdir()
        (bin_dir / "git").write_text(f"""#!/bin/sh
case "$*" in *status*) ls "$HOME/.claude/hooks/state/workflow" >> "{self.calls}" 2>&1;; esac
echo "git $*" >> "{self.calls}"
exec {shutil.which("git")} "$@"
""")
        (bin_dir / "git").chmod(0o755)
        self.extra_env = dict(PATH=f"{bin_dir}:{os.environ['PATH']}")

    def test_no_git_call_per_dirty_file(self):
        self.tracked("a.py", "b.py", "c.py")
        self.shim()
        self.declared()
        self.assertNotIn("check-ignore", self.calls.read_text())
        self.assertEqual(self.late()[0]["files"], ["a.py", "b.py", "c.py"])

    def test_declaration_is_written_before_the_status_pass(self):
        self.tracked("a.py")
        self.shim()
        self.declared()
        self.assertIn("s.json", self.calls.read_text().split("status")[0])

    def test_status_takes_no_optional_lock(self):
        self.shim()
        self.declared()
        self.assertIn("--no-optional-locks", self.calls.read_text())

    def test_ignored_files_are_not_logged(self):
        (self.repo / ".gitignore").write_text("*.log\n.gitignore\n")
        (self.repo / "x.log").write_text("x")
        self.declared()
        self.assertEqual(self.late(), [])

    def test_refused_declarations_are_not_logged(self):
        (self.repo / "a.py").write_text("x")
        for _ in range(3):
            self.assertIn("no plan at", self.hook("workflow-declare full --plan nope.md"))
        self.assertEqual(self.late(), [])

    def test_parallel_first_declarations_log_once(self):
        (self.repo / "a.py").write_text("x")
        data = dict(tool_name="Bash", session_id="s", cwd=str(self.repo),
                    tool_input=dict(command='workflow-declare shrunk 1-3 "known fix: x"'))
        env = dict(os.environ, HOME=str(self.home))
        runs = [subprocess.Popen(["python3", GATE], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, env=env, text=True)
                for _ in range(8)]
        for r in runs:
            r.stdin.write(json.dumps(data))
            r.stdin.close()
        for r in runs:
            r.wait()
        self.assertEqual(len(self.late()), 1)

    def test_new_folder_of_markdown_is_not_late(self):
        (self.repo / "plans").mkdir()
        (self.repo / "plans/p.md").write_text("x")
        self.declared()
        self.assertEqual(self.late(), [])

    def test_new_mixed_folder_logs_only_the_code(self):
        (self.repo / "plans").mkdir()
        (self.repo / "plans/p.md").write_text("x")
        (self.repo / "plans/p.py").write_text("x")
        self.declared()
        self.assertEqual(self.late()[0]["files"], ["plans/p.py"])


class Unfinished(Base):
    """Finishing a conflicted cherry-pick or revert on the integration branch (review finding 8)."""

    def conflict(self, *op):
        (self.repo / "f.txt").write_text("base\n")
        self.g("add", "f.txt"), self.g("commit", "-q", "-m", "base")
        self.g("branch", "-q", "main")
        (self.repo / "f.txt").write_text("work\n")
        self.g("commit", "-q", "-am", "w")
        self.g("checkout", "-q", "main")
        (self.repo / "f.txt").write_text("main\n")
        self.g("commit", "-q", "-am", "m")
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t", *op, "work"], capture_output=True)

    def test_finishing_a_cherry_pick_on_integration_passes(self):
        self.conflict("cherry-pick")
        self.declared()
        self.assertIsNone(self.hook(f"git commit -m 'pick\n\n{self.M}'"))

    def test_finishing_a_revert_on_integration_passes(self):
        self.conflict("revert")
        self.declared()
        self.assertIsNone(self.hook(f"git commit -m 'revert\n\n{self.M}'"))


if __name__ == "__main__":
    unittest.main()
