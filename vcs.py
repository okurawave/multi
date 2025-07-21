# Python

import subprocess
from pathlib import Path

class GitManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        if not (repo_path / ".git").exists():
            self._run_git_command(["init"])

    def _run_git_command(self, command: list[str]):
        result = subprocess.run(["git"] + command, cwd=self.repo_path, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        return result.stdout.strip()

    def create_worktree(self, path: str, branch_name: str, base_branch: str = None):
        command = ["worktree", "add", path, branch_name]
        if base_branch:
            self._run_git_command(["branch", branch_name, base_branch])
        self._run_git_command(command)

    def commit(self, worktree_path: Path, message: str):
        subprocess.run(["git", "add", "."], cwd=worktree_path, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=worktree_path, check=True)

    def get_diff(self, branch1: str, branch2: str) -> str:
        return self._run_git_command(["diff", f"{branch1}..{branch2}"])

    def merge(self, target_branch: str, source_branch: str):
        self._run_git_command(["checkout", target_branch])
        self._run_git_command(["merge", "--no-ff", source_branch])

    def cleanup(self, worktree_path: str, branch_name: str):
        self._run_git_command(["worktree", "remove", worktree_path])
        self._run_git_command(["branch", "-d", branch_name])
