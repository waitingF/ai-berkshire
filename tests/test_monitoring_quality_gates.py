from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-monitoring.sh"
PRE_COMMIT = ROOT / ".githooks" / "pre-commit"
PRE_PUSH = ROOT / ".githooks" / "pre-push"
INSTALLER = ROOT / "scripts" / "install-git-hooks.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-monitoring.yml"


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


if __name__ == "__main__":
    unittest.main()
