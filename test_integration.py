# Python
import unittest

class IntegrationTest(unittest.TestCase):
    def test_agents_module(self):
        from agents import MasterAI
        agent = MasterAI()
        result = agent.generate_plan("Test requirements")
        self.assertIsInstance(result, str)

    def test_orchestrator_module(self):
        from orchestrator import Orchestrator
        from pathlib import Path
        orchestrator = Orchestrator(Path("."))
        self.assertIsNotNone(orchestrator)

    def test_vcs_module(self):
        from vcs import GitManager
        from pathlib import Path
        git = GitManager(Path("."))
        self.assertIsNotNone(git)

    def test_workspace_module(self):
        from workspace import WorkspaceManager
        workspace = WorkspaceManager("test_session")
        self.assertIsNotNone(workspace)

if __name__ == "__main__":
    unittest.main()
