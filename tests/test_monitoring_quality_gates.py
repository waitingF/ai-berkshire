from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-monitoring.sh"
PRE_COMMIT = ROOT / ".githooks" / "pre-commit"
PRE_PUSH = ROOT / ".githooks" / "pre-push"
INSTALLER = ROOT / "scripts" / "install-git-hooks.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-monitoring.yml"
DAILY_WORKFLOW = ROOT / ".github" / "workflows" / "daily-monitor.yml"
REFRESHER = ROOT / "scripts" / "refresh-daily-monitor-before-commit.py"


def run(command, *, cwd, env=None, stdin=None):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


class MonitoringValidatorTest(unittest.TestCase):
    def test_syntax_validation_handles_git_quoted_filenames(self):
        syntax_check = VALIDATOR.read_text(encoding="utf-8").split(
            "run_python - <<'PY'\n", 1
        )[1].split("\nPY", 1)[0]
        for source, expected_code in [("value = 1\n", 0), ("value =\n", 1)]:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                run(["git", "init", "-q"], cwd=repo)
                run(["git", "config", "core.quotePath", "true"], cwd=repo)
                script = repo / "reports" / "中文 空格" / '模型"\n脚本.py'
                script.parent.mkdir(parents=True)
                script.write_text(source, encoding="utf-8")
                run(["git", "add", "--", str(script.relative_to(repo))], cwd=repo)

                result = run([sys.executable, "-c", syntax_check], cwd=repo)

                self.assertEqual(result.returncode, expected_code, result.stderr)
                if expected_code == 0:
                    self.assertIn("Checked 1 tracked Python files", result.stdout)
                else:
                    self.assertIn("SyntaxError", result.stderr)

    def test_fast_validation_propagates_daily_config_failure(self):
        self.assertTrue(VALIDATOR.exists(), "缺少统一监控校验脚本")
        with tempfile.TemporaryDirectory() as tmp:
            fake_python = Path(tmp) / "python3"
            fake_python.write_text(
                """#!/bin/sh
if [ "$1" = "tools/daily_monitor.py" ]; then
  echo daily-config-failed >&2
  exit 42
fi
exit 0
""",
                encoding="utf-8",
            )
            fake_python.chmod(fake_python.stat().st_mode | stat.S_IXUSR)
            env = os.environ.copy()
            env["PATH"] = f"{tmp}:{env['PATH']}"
            env["AI_BERKSHIRE_PYTHON"] = str(fake_python)

            result = run(["bash", str(VALIDATOR), "--fast"], cwd=ROOT, env=env)

        self.assertEqual(result.returncode, 42)
        self.assertIn("daily-config-failed", result.stderr)


class LocalGitHookTest(unittest.TestCase):
    def make_repo(self, tmp):
        repo = Path(tmp) / "repo"
        repo.mkdir()
        run(["git", "init", "-q"], cwd=repo)
        run(["git", "config", "user.name", "Test"], cwd=repo)
        run(["git", "config", "user.email", "test@example.com"], cwd=repo)
        (repo / "scripts").mkdir()
        (repo / "data").mkdir()
        (repo / "README.md").write_text("baseline\n", encoding="utf-8")
        (repo / "data" / "triggers.json").write_text("{}\n", encoding="utf-8")
        run(["git", "add", "."], cwd=repo)
        run(["git", "commit", "-qm", "baseline"], cwd=repo)
        (repo / "scripts" / "run-local-python.sh").write_text(
            (ROOT / "scripts" / "run-local-python.sh").read_text(), encoding="utf-8"
        )
        (repo / "scripts" / REFRESHER.name).write_text(
            "from pathlib import Path\nPath('refresh-ran.txt').write_text('refreshed')\n",
            encoding="utf-8",
        )
        return repo

    def install_stub_validator(self, repo, *, exit_code):
        marker = repo / "validator-mode.txt"
        validator = repo / "scripts" / "validate-monitoring.sh"
        validator.write_text(
            f"#!/bin/sh\nprintf '%s' \"$1\" > validator-mode.txt\nexit {exit_code}\n",
            encoding="utf-8",
        )
        validator.chmod(validator.stat().st_mode | stat.S_IXUSR)
        return marker

    def test_pre_commit_skips_monitoring_validation_for_unrelated_files(self):
        self.assertTrue(PRE_COMMIT.exists(), "缺少 pre-commit hook")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            marker = self.install_stub_validator(repo, exit_code=23)
            (repo / "README.md").write_text("changed\n", encoding="utf-8")
            run(["git", "add", "README.md"], cwd=repo)

            result = run(["bash", str(PRE_COMMIT)], cwd=repo)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(marker.exists())
            self.assertTrue((repo / "refresh-ran.txt").exists())

    def test_pre_commit_blocks_unstaged_monitor_inputs_even_for_unrelated_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            (repo / "README.md").write_text("changed\n")
            run(["git", "add", "README.md"], cwd=repo)
            (repo / "data" / "triggers.json").write_text('{"unstaged":true}\n')

            result = run(["bash", str(PRE_COMMIT)], cwd=repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("未暂存", result.stderr)
            self.assertFalse((repo / "refresh-ran.txt").exists())

    def test_pre_commit_does_not_run_document_whitespace_check(self):
        self.assertTrue(PRE_COMMIT.exists(), "缺少 pre-commit hook")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            marker = self.install_stub_validator(repo, exit_code=0)
            (repo / "data" / "triggers.json").write_text(
                '{"updated":true}\n', encoding="utf-8"
            )
            report = repo / "reports" / "sample.md"
            report.parent.mkdir()
            report.write_text("document with trailing spaces  \n", encoding="utf-8")
            run(["git", "add", "data/triggers.json", "reports/sample.md"], cwd=repo)

            result = run(["bash", str(PRE_COMMIT)], cwd=repo)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "--fast")

    def test_pre_commit_blocks_relevant_change_when_fast_validation_fails(self):
        self.assertTrue(PRE_COMMIT.exists(), "缺少 pre-commit hook")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            marker = self.install_stub_validator(repo, exit_code=23)
            (repo / "data" / "triggers.json").write_text('{"updated":true}\n', encoding="utf-8")
            run(["git", "add", "data/triggers.json"], cwd=repo)

            result = run(["bash", str(PRE_COMMIT)], cwd=repo)

            self.assertEqual(result.returncode, 23)
            self.assertEqual(marker.read_text(encoding="utf-8"), "--fast")

    def test_pre_commit_validates_deletion_of_relevant_file(self):
        self.assertTrue(PRE_COMMIT.exists(), "缺少 pre-commit hook")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            marker = self.install_stub_validator(repo, exit_code=23)
            run(["git", "rm", "-q", "data/triggers.json"], cwd=repo)

            result = run(["bash", str(PRE_COMMIT)], cwd=repo)

            self.assertEqual(result.returncode, 23)
            self.assertEqual(marker.read_text(encoding="utf-8"), "--fast")

    def test_pre_push_runs_full_validation_and_propagates_failure(self):
        self.assertTrue(PRE_PUSH.exists(), "缺少 pre-push hook")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            marker = self.install_stub_validator(repo, exit_code=24)

            result = run(
                ["bash", str(PRE_PUSH), "origin", "git@example.invalid:repo.git"],
                cwd=repo,
                stdin="",
            )

            self.assertEqual(result.returncode, 24)
            self.assertEqual(marker.read_text(encoding="utf-8"), "--full")

    def test_pre_push_isolates_git_operations_in_linked_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            worktree = Path(tmp) / "monitor worktree"
            added = run(["git", "worktree", "add", "--detach", str(worktree)], cwd=repo)
            self.assertEqual(added.returncode, 0, added.stderr)
            (worktree / "scripts").mkdir()
            (worktree / "scripts" / "validate-monitoring.sh").write_text(
                "#!/bin/sh\nset -e\nmkdir foreign.git\ngit -C foreign.git init --bare -q\n",
                encoding="utf-8",
            )
            git_dir = run(["git", "rev-parse", "--absolute-git-dir"], cwd=worktree).stdout.strip()
            env = os.environ.copy()
            env.update({"GIT_DIR": git_dir, "GIT_WORK_TREE": str(worktree),
                        "GIT_INDEX_FILE": str(Path(git_dir) / "index")})

            result = run(["bash", str(PRE_PUSH)], cwd=worktree, env=env, stdin="")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((worktree / "foreign.git" / "HEAD").exists())
            bare = run(["git", "config", "--bool", "core.bare"], cwd=repo)
            self.assertEqual(bare.stdout.strip(), "false")

    def test_pre_push_does_not_run_document_whitespace_check(self):
        self.assertTrue(PRE_PUSH.exists(), "缺少 pre-push hook")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            marker = self.install_stub_validator(repo, exit_code=0)
            report = repo / "reports" / "sample.md"
            report.parent.mkdir()
            report.write_text("document with trailing spaces  \n", encoding="utf-8")
            run(["git", "add", "reports/sample.md"], cwd=repo)
            run(["git", "commit", "-qm", "add report"], cwd=repo)
            local_sha = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
            zero_sha = "0" * 40

            result = run(
                ["bash", str(PRE_PUSH), "origin", "git@example.invalid:repo.git"],
                cwd=repo,
                stdin=(
                    f"refs/heads/main {local_sha} refs/heads/main {zero_sha}\n"
                ),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "--full")

    def test_installer_sets_repository_hooks_path(self):
        self.assertTrue(INSTALLER.exists(), "缺少 Git hooks 安装脚本")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)

            result = run(["bash", str(INSTALLER), str(repo)], cwd=ROOT)
            configured = run(
                ["git", "config", "--local", "--get", "core.hooksPath"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(configured.stdout.strip(), ".githooks")


class DailyMonitorCommitRefreshTest(unittest.TestCase):
    def test_real_commit_refreshes_and_includes_only_generated_outputs(self):
        self.assertTrue(REFRESHER.exists(), "缺少提交前刷新脚本")
        for monitor_exit, commit_args in ((0, ()), (2, ()), (0, ("--only", "README.md"))):
            with self.subTest(monitor_exit=monitor_exit, commit_args=commit_args), tempfile.TemporaryDirectory() as tmp:
                repo = LocalGitHookTest().make_repo(tmp)
                baseline = repo / "data" / "monitoring-state.json"
                baseline.write_text('{"notification_baseline":"preserved"}\n')
                (repo / "scripts" / REFRESHER.name).write_text(REFRESHER.read_text())
                (repo / ".githooks").mkdir()
                (repo / ".githooks" / "pre-commit").write_bytes(PRE_COMMIT.read_bytes())
                (repo / ".githooks" / "pre-commit").chmod(0o755)
                run(["git", "config", "core.hooksPath", ".githooks"], cwd=repo)
                (repo / "tools").mkdir()
                (repo / "tools" / "daily_monitor.py").write_text(
                    "import json, sys\nfrom pathlib import Path\n"
                    "assert sys.argv[1] == '--state-file' and sys.argv[3] == '--json'\n"
                    "state = Path(sys.argv[2])\n"
                    "assert 'preserved' in state.read_text()\n"
                    "directory = Path('reports/daily-monitor')\n"
                    "directory.mkdir(parents=True, exist_ok=True)\n"
                    "for name in ('daily-monitor-latest.md', 'daily-monitor-20261124.md'):\n"
                    "    (directory / name).write_text('fresh monitor\\n')\n"
                    f"status = {'OK' if monitor_exit == 0 else 'DEGRADED'!r}\n"
                    "(directory / 'daily-monitor-latest.json').write_text(json.dumps({'date': '2026-11-24', 'status': status}))\n"
                    "state.write_text('{}\\n')\n"
                    "print(json.dumps({'date': '2026-11-24', 'status': status}))\n"
                    f"sys.exit({monitor_exit})\n"
                )
                archive = repo / "reports" / "daily-monitor" / "daily-monitor-20261123.md"
                archive.parent.mkdir(parents=True)
                archive.write_text("unrelated archive\n")
                (repo / "README.md").write_text("changed\n")
                run(["git", "add", "README.md"], cwd=repo)

                committed = run(["git", "commit", "-qm", "test refresh", *commit_args], cwd=repo)
                paths = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=repo)

                self.assertEqual(committed.returncode, 0, committed.stderr)
                self.assertEqual(set(paths.stdout.splitlines()), {
                    "README.md",
                    "reports/daily-monitor/daily-monitor-latest.md",
                    "reports/daily-monitor/daily-monitor-latest.json",
                    "reports/daily-monitor/daily-monitor-20261124.md",
                })
                self.assertEqual(run(["git", "show", "HEAD:reports/daily-monitor/daily-monitor-latest.md"], cwd=repo).stdout, "fresh monitor\n")
                self.assertIn("preserved", baseline.read_text())

    def test_refresh_failure_preserves_index_and_prevents_commit(self):
        self.assertTrue(REFRESHER.exists(), "缺少提交前刷新脚本")
        with tempfile.TemporaryDirectory() as tmp:
            repo = LocalGitHookTest().make_repo(tmp)
            (repo / "scripts" / REFRESHER.name).write_text(REFRESHER.read_text())
            (repo / "tools").mkdir()
            (repo / "tools" / "daily_monitor.py").write_text("raise SystemExit(1)\n")
            (repo / "README.md").write_text("changed\n")
            run(["git", "add", "README.md"], cwd=repo)
            before = run(["git", "diff", "--cached"], cwd=repo).stdout

            result = run([sys.executable, str(repo / "scripts" / REFRESHER.name)], cwd=repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(run(["git", "diff", "--cached"], cwd=repo).stdout, before)
            self.assertIn("提交已阻止", result.stderr)


class GithubQualityGateTest(unittest.TestCase):
    def test_workflow_installs_dependencies_for_every_test_module(self):
        self.assertTrue(WORKFLOW.exists(), "缺少 GitHub 监控规则校验 workflow")
        workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

        commands = [
            step.get("run", "")
            for step in workflow["jobs"]["validate-monitoring"]["steps"]
        ]
        install_command = next(
            (command for command in commands if "pip install" in command),
            "",
        )
        self.assertIn("requirements-monitoring.txt", install_command)
        self.assertIn("requirements-pages.txt", install_command)

    def test_workflow_runs_full_shared_validation_on_pull_requests_and_main(self):
        self.assertTrue(WORKFLOW.exists(), "缺少 GitHub 监控规则校验 workflow")
        workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

        self.assertIn("pull_request", workflow["on"])
        self.assertIn("push", workflow["on"])
        self.assertEqual(workflow["on"]["push"]["branches"], ["main"])
        job = workflow["jobs"]["validate-monitoring"]
        commands = [step.get("run", "") for step in job["steps"]]
        self.assertIn("bash scripts/validate-monitoring.sh --full", commands)

    def test_daily_workflow_keeps_degraded_report_non_blocking(self):
        self.assertTrue(DAILY_WORKFLOW.exists(), "缺少每日监控 workflow")
        workflow = yaml.load(
            DAILY_WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
        )

        steps = workflow["jobs"]["monitor"]["steps"]
        run_monitor = next(step for step in steps if step.get("id") == "run_monitor")
        self.assertIn('"$monitor_exit" -ne 2', run_monitor["run"])
        self.assertFalse(
            any(
                "steps.run_monitor.outputs.exit_code" in step.get("run", "")
                for step in steps
            ),
            "降级报告已生成时不应由后续门禁把 workflow 标记为失败",
        )


if __name__ == "__main__":
    unittest.main()
