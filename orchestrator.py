# Python

import json
import time
from pathlib import Path
from vcs import GitManager
from workspace import WorkspaceManager
from agents import MasterAI

class Orchestrator:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.git = GitManager(project_path)
        self.workspace = WorkspaceManager(session_name=project_path.name)
        self.master_ai = MasterAI(self.workspace)
        self.tasks = []
        self.task_status = {} # {task_id: "pending/running/review/testing/completed"}

    def run(self):
        self._planning_phase()
        self._execution_phase()

    def _planning_phase(self):
        print("Orchestrator: Planning phase started.")
        requirements_path = self.project_path / "01_requirements.md"
        requirements = requirements_path.read_text()
        tasks_json_str = self.master_ai.generate_plan(requirements)
        tasks_path = self.project_path / "02_tasks.json"
        tasks_path.write_text(tasks_json_str)
        self.tasks = json.loads(tasks_json_str)
        self.workspace.setup_worker_panes(num_workers=3)

    def _execution_phase(self):
        print("Orchestrator: Execution phase started.")
        while not self._all_tasks_completed():
            runnable_tasks = self._find_runnable_tasks()
            for task in runnable_tasks:
                worker_pane = self.workspace.get_idle_worker_pane()
                if worker_pane:
                    self._dispatch_task(task, worker_pane)
            time.sleep(5)

    def _dispatch_task(self, task: dict, pane):
        task_id = task["id"]
        task_type = task["task_type"]
        self.task_status[task_id] = "running"
        print(f"Dispatching task {task_id} ({task_type}) to pane {pane.id}")
        if task_type == "develop":
            self.git.create_worktree(f"worktrees/{task_id}", task["branch_name"])
            result = self.workspace.execute_task_in_pane(pane, task["prompt"])
        elif task_type == "review":
            diff = self.git.get_diff("main", task["target_branch"])
            review_prompt = f"以下のコード変更をレビューせよ。\n\n{diff}"
            result = self.workspace.execute_task_in_pane(pane, review_prompt)
        self.task_status[task_id] = "completed"
        self.workspace.set_pane_status_idle(pane.id)

    def _find_runnable_tasks(self):
        return []

    def _all_tasks_completed(self):
        return False
