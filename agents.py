# Python

from workspace import WorkspaceManager

class BaseAgent:
    def __init__(self, workspace_manager: WorkspaceManager):
        self.workspace = workspace_manager

    def execute(self, prompt: str) -> str:
        raise NotImplementedError

class MasterAI(BaseAgent):
    def generate_plan(self, requirements: str) -> str:
        prompt = f"以下の要件定義書からタスクリストをJSONで生成せよ。\n\n{requirements}"
        pane = self.workspace.get_idle_worker_pane()
        if not pane:
            raise Exception("No available worker for MasterAI")
        result = self.workspace.execute_task_in_pane(pane, prompt)
        self.workspace.set_pane_status_idle(pane.id)
        return result

# DevWorkerAIやQAWorkerAIはOrchestratorがプロンプトを組み立て、WorkspaceManagerがペインに割り当てることで実現される。
