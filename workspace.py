# Python

import libtmux
import time

class WorkspaceManager:
    def __init__(self, session_name: str):
        self.server = libtmux.Server()
        self.session = self.server.find_where({"session_name": session_name})
        if not self.session:
            self.session = self.server.new_session(session_name=session_name)
        self.window = self.session.attached_window
        self.panes = {} # {pane_id: {"status": "idle", "pane": pane_object}}

    def setup_worker_panes(self, num_workers: int):
        self.window.attached_pane.set_width(30)
        for i in range(num_workers):
            pane = self.window.split_window(attach=False, vertical=False)
            pane.send_keys("gemini", enter=True)
            self.panes[pane.id] = {"status": "idle", "pane": pane}
        self.window.select_layout('tiled')

    def get_idle_worker_pane(self) -> 'libtmux.Pane | None':
        for pane_id, info in self.panes.items():
            if info["status"] == "idle":
                info["status"] = "busy"
                return info["pane"]
        return None

    def execute_task_in_pane(self, pane: 'libtmux.Pane', prompt: str) -> str:
        completion_marker = "!!CMD_COMPLETE!!"
        full_prompt = f"{prompt}\n\n応答が完了したら、必ず '{completion_marker}' という文字列だけを最後に出力してください。"
        pane.send_keys(full_prompt, enter=True)
        output = ""
        while completion_marker not in output:
            time.sleep(2)
            output = pane.capture_pane(start_line="-1000")
        return output.split(completion_marker)[0].strip()

    def set_pane_status_idle(self, pane_id: str):
        if pane_id in self.panes:
            self.panes[pane_id]["status"] = "idle"
