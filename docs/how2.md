承知いたしました。これは非常に挑戦的でエキサイティングなプロジェクトです。概念設計から実装へと駒を進めるために、具体的なコードの構造やライブラリの使い方を含めた、詳細な実装ガイドを提示します。

これは完全なソースコードではありませんが、各コンポーネントをどのように構築し、連携させるかの骨子となるものです。

---

### **実装ガイド: 自律型AI開発プラットフォーム `ParallelXec-Agent`**

#### 1. プロジェクトのセットアップ

**1.1. ディレクトリ構造**

```
parallelexec-agent/
├── main.py                # CLIのエントリーポイント
├── orchestrator.py        # Orchestratorクラス（中核エンジン）
├── agents.py              # 各AIエージェントの定義
├── vcs.py                 # Git連携モジュール (GitManager)
├── workspace.py           # tmux連携モジュール (WorkspaceManager)
├── dialogue.py            # 対話インターフェース
├── config.py              # 設定管理
└── prompts/               # プロンプトのテンプレートを格納
    ├── master_plan.txt
    ├── qa_review.txt
    └── qa_test.txt
```

**1.2. 必要なライブラリ**

```bash
pip install click libtmux pyyaml python-dotenv prompt_toolkit watchdog
```

#### 2. 主要コンポーネントの実装詳細

**2.1. `vcs.py` - Git連携モジュール**

`subprocess`をラップし、可読性の高いGit操作を提供します。

```python
# vcs.py
import subprocess
from pathlib import Path

class GitManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        if not (repo_path / ".git").exists():
            self._run_git_command(["init"])

    def _run_git_command(self, command: list[str]):
        # subprocessを使ってgitコマンドを実行するヘルパー
        # cwd=self.repo_path で、常にリポジトリのルートで実行
        result = subprocess.run(["git"] + command, cwd=self.repo_path, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        return result.stdout.strip()

    def create_worktree(self, path: str, branch_name: str, base_branch: str = None):
        command = ["worktree", "add", path, branch_name]
        if base_branch:
            # base_branchから新しいブランチを作成してworktreeを作る
            # 例: git worktree add ../test test/T01 feature/T01
            # このコマンドは直接はないので、ブランチを先に作る必要がある
            self._run_git_command(["branch", branch_name, base_branch])
        self._run_git_command(command)

    def commit(self, worktree_path: Path, message: str):
        # 特定のworktree内でcommitする
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
```

**2.2. `workspace.py` - tmux連携モジュール**

`libtmux`を使い、AIワーカーたちの作業場を管理します。

```python
# workspace.py
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
        # 最初のペインをリサイズ
        self.window.attached_pane.set_width(30) # Orchestratorログ用
        # ワーカー用のペインを作成
        for i in range(num_workers):
            pane = self.window.split_window(attach=False, vertical=False)
            pane.send_keys("gemini", enter=True) # インタラクティブモードで起動
            self.panes[pane.id] = {"status": "idle", "pane": pane}
        self.window.select_layout('tiled')

    def get_idle_worker_pane(self) -> libtmux.Pane | None:
        for pane_id, info in self.panes.items():
            if info["status"] == "idle":
                info["status"] = "busy"
                return info["pane"]
        return None

    def execute_task_in_pane(self, pane: libtmux.Pane, prompt: str) -> str:
        # プロンプトの最後に完了マーカーを追加
        completion_marker = "!!CMD_COMPLETE!!"
        full_prompt = f"{prompt}\n\n応答が完了したら、必ず '{completion_marker}' という文字列だけを最後に出力してください。"
        
        pane.send_keys(full_prompt, enter=True)

        # 完了マーカーが現れるまでポーリングして待つ
        output = ""
        while completion_marker not in output:
            time.sleep(2) # 負荷を考慮して適度に待つ
            output = pane.capture_pane(start_line="-1000") # 直近1000行を取得
        
        # マーカーを除いた純粋な結果を返す
        return output.split(completion_marker)[0].strip()

    def set_pane_status_idle(self, pane_id: str):
        if pane_id in self.panes:
            self.panes[pane_id]["status"] = "idle"
```

**2.3. `agents.py` - AIエージェント定義**

各AIの役割と、プロンプト生成ロジックをここに集約します。

```python
# agents.py
class BaseAgent:
    def __init__(self, workspace_manager: WorkspaceManager):
        self.workspace = workspace_manager

    def execute(self, prompt: str) -> str:
        # このメソッドはサブクラスでオーバーライドされる
        raise NotImplementedError

class MasterAI(BaseAgent):
    def generate_plan(self, requirements: str) -> str:
        # prompts/master_plan.txt などを読み込んでプロンプトを組み立てる
        prompt = f"以下の要件定義書からタスクリストをJSONで生成せよ。\n\n{requirements}"
        
        # MasterAIは専用のペインで実行するか、直接APIを叩くか選択できる
        # ここではシンプルに1つのワーカーペインを借りる想定
        pane = self.workspace.get_idle_worker_pane()
        if not pane:
            raise Exception("No available worker for MasterAI")
        result = self.workspace.execute_task_in_pane(pane, prompt)
        self.workspace.set_pane_status_idle(pane.id)
        return result

# DevWorkerAIやQAWorkerAIは実体を持たない。
# 彼らのロジックはOrchestratorがプロンプトを組み立て、
# WorkspaceManagerが空いているペインに割り当てることで実現される。
```

**2.4. `orchestrator.py` - 中核エンジン**

これがシステムの心臓部。状態を管理し、他のモジュールを協調させてプロジェクトを進行させます。

```python
# orchestrator.py
import json
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
        # フェーズ0: 計画
        self._planning_phase()

        # フェーズ1: 実行ループ
        self._execution_phase()

    def _planning_phase(self):
        print("Orchestrator: Planning phase started.")
        # ここでdialogue.pyを呼び出し、要件定義書を生成
        requirements_path = self.project_path / "01_requirements.md"
        # (対話ロジック...)
        
        requirements = requirements_path.read_text()
        tasks_json_str = self.master_ai.generate_plan(requirements)
        
        tasks_path = self.project_path / "02_tasks.json"
        tasks_path.write_text(tasks_json_str)
        self.tasks = json.loads(tasks_json_str)
        
        # ワーカーの数だけペインを準備
        self.workspace.setup_worker_panes(num_workers=3) # 例: 3人

    def _execution_phase(self):
        print("Orchestrator: Execution phase started.")
        while not self._all_tasks_completed():
            # 実行可能なタスクを探す
            runnable_tasks = self._find_runnable_tasks()

            for task in runnable_tasks:
                worker_pane = self.workspace.get_idle_worker_pane()
                if worker_pane:
                    self._dispatch_task(task, worker_pane)
            
            time.sleep(5) # メインループのポーリング間隔

    def _dispatch_task(self, task: dict, pane):
        task_id = task["id"]
        task_type = task["task_type"]
        self.task_status[task_id] = "running"
        print(f"Dispatching task {task_id} ({task_type}) to pane {pane.id}")
        
        if task_type == "develop":
            # worktreeを作成し、開発タスクを実行
            self.git.create_worktree(f"worktrees/{task_id}", task["branch_name"])
            result = self.workspace.execute_task_in_pane(pane, task["prompt"])
            # (結果をファイルに保存し、コミットするロジック...)
            # self.git.commit(...)
            
        elif task_type == "review":
            # diffを取得してレビュータスクを実行
            diff = self.git.get_diff("main", task["target_branch"])
            review_prompt = f"以下のコード変更をレビューせよ。\n\n{diff}"
            result = self.workspace.execute_task_in_pane(pane, review_prompt)
            # (レビュー結果のハンドリング...)
        
        # (testタスクのロジックも同様)
        
        self.task_status[task_id] = "completed"
        self.workspace.set_pane_status_idle(pane.id)
        
    def _find_runnable_tasks(self):
        # 依存関係をチェックし、実行可能なタスクのリストを返す
        # self.tasks と self.task_status を見て判断
        return [] # (実装)
    
    def _all_tasks_completed(self):
        # 全てのタスクが完了したかチェック
        return False # (実装)

```

**2.5. `main.py` - エントリーポイント**

`click`を使って、洗練されたコマンドラインインターフェースを提供します。

```python
# main.py
import click
from pathlib import Path
from orchestrator import Orchestrator

@click.group()
def cli():
    pass

@cli.command()
@click.option('--project-name', required=True, help='Name of the project directory.')
def new(project_name):
    """Starts a new AI-driven development project."""
    project_path = Path(project_name)
    project_path.mkdir(exist_ok=True)
    
    try:
        orchestrator = Orchestrator(project_path)
        orchestrator.run()
    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)

if __name__ == '__main__':
    cli()
```

#### 3. 実行の流れ

1.  ユーザーがターミナルで `python main.py new --project-name my-cool-app` を実行。
2.  `main.py`が`Orchestrator`をインスタンス化。
3.  `Orchestrator`が`GitManager`を初期化 (`git init`)。
4.  `Orchestrator`が対話AIモジュールを呼び出し、ユーザーと対話して`01_requirements.md`を作成。
5.  `Orchestrator`が`MasterAI`を使って`02_tasks.json`を生成。
6.  `Orchestrator`が`WorkspaceManager`に指示を出し、tmuxセッションとワーカー用のペイン群をセットアップ。各ペインで`gemini`が起動し待機状態になる。
7.  `Orchestrator`のメイン実行ループが開始。
8.  実行可能な開発タスクを見つけ、`GitManager`に`worktree`の作成を指示。
9.  空いているワーカーペインに`WorkspaceManager`経由で開発プロンプトを`send-keys`。
10. `WorkspaceManager`は完了マーカーを監視し、AIの応答を取得して`Orchestrator`に返す。
11. `Orchestrator`は結果をファイルに保存させ、`GitManager`に`commit`を指示。
12. `Orchestrator`はタスクの完了を記録し、次の依存タスク（レビューやテスト）の実行準備に入る。
13. このサイクルが全てのタスク完了まで繰り返され、最終的に`main`ブランチに成果が統合される。

この実装ガイドは、複雑なシステムを構築するための出発点です。各モジュールを一つずつ丁寧に実装し、テストしていくことで、この野心的なプロジェクトを実現することが可能になります。


承知いたしました。インタフェース仕様の標準化は、このような複雑なシステムを堅牢に構築する上で極めて重要です。各コンポーネントがどのような「契約」に基づいて通信するかを明確に定義します。

---

### **インタフェース仕様補足: `ParallelXec-Agent`**

この仕様は、主要コンポーネント間のメソッドシグネチャと、それらを通じてやりとりされる主要なデータフォーマット（JSONスキーマ）を定義します。

#### 1. データフォーマット定義 (JSON Schema)

**1.1. `tasks.json` のスキーマ**

統括AIが生成し、Orchestratorが消費する、プロジェクトの設計図です。

*   **ファイルパス:** `(project_root)/02_tasks.json`
*   **形式:** タスクオブジェクトの配列

**タスクオブジェクト (`Task Object`) のスキーマ:**

```json
{
  "type": "object",
  "properties": {
    "id": { "type": "string", "description": "T01, T02... のような一意なタスクID" },
    "task_type": { "type": "string", "enum": ["develop", "review", "test"], "description": "タスクの種類" },
    "description": { "type": "string", "description": "人間が読むためのタスク概要" },
    "prompt": { "type": "string", "description": "AIワーカーに渡される具体的な指示プロンプト" },
    "depends_on": {
      "type": "array",
      "items": { "type": "string" },
      "description": "このタスクが依存するタスクIDのリスト"
    },
    "branch_name": { "type": "string", "description": "(develop, testタスク用) このタスクで作成するGitブランチ名" },
    "worktree_path": { "type": "string", "description": "(develop, testタスク用) このタスクで作成するワークツリーの相対パス" },
    "output_files": {
      "type": "array",
      "items": { "type": "string" },
      "description": "(develop, testタスク用) 生成または変更が期待されるファイルのリスト"
    },
    "review_target": {
      "type": "object",
      "properties": {
        "task_id": { "type": "string" },
        "branch_name": { "type": "string" }
      },
      "description": "(reviewタスク用) レビュー対象となる開発タスクの情報"
    },
    "test_target": {
      "type": "object",
      "properties": {
        "task_id": { "type": "string" },
        "branch_name": { "type": "string" }
      },
      "description": "(testタスク用) テスト対象となる開発タスクの情報"
    }
  },
  "required": ["id", "task_type", "description", "prompt", "depends_on"]
}
```

**1.2. `task_status.json` のスキーマ**

Orchestratorがプロジェクトの現在の進捗を管理するために使用します。

*   **ファイルパス:** `(project_root)/.state/task_status.json`
*   **形式:** `task_id`をキーとするオブジェクト

**ステータスオブジェクト (`Status Object`) のスキーマ:**

```json
{
  "type": "object",
  "patternProperties": {
    "^T[0-9]+$": {
      "type": "object",
      "properties": {
        "status": { "type": "string", "enum": ["pending", "running", "completed", "failed"], "description": "タスクの現在の状態" },
        "started_at": { "type": "string", "format": "date-time" },
        "completed_at": { "type": "string", "format": "date-time" },
        "result": { "type": "string", "description": "AIからの応答やエラーメッセージなど" }
      },
      "required": ["status"]
    }
  }
}
```

#### 2. コンポーネント間メソッドシグネチャ

**2.1. `Orchestrator` → `GitManager`**

```python
class GitManager:
    # ワークツリーを作成し、関連ブランチも作成する
    def setup_task_environment(self, worktree_path: str, branch_name: str, base_branch: str = "main") -> None: ...

    # ワークツリー内の変更をコミットする
    def commit_changes(self, worktree_path: str, commit_message: str) -> None: ...

    # 2つのブランチ間の差分を取得する
    def get_branch_diff(self, base_branch: str, compare_branch: str) -> str: ...

    # 成果物ブランチをターゲットブランチにマージする
    def merge_branch(self, target_branch: str, source_branch: str) -> None: ...

    # 不要になったワークツリーとブランチを削除する
    def cleanup_task_environment(self, worktree_path: str, branch_name: str) -> None: ...
```

**2.2. `Orchestrator` → `WorkspaceManager`**

```python
class WorkspaceManager:
    # 指定された数のワーカーペインを初期化し、待機状態にする
    def initialize_workspace(self, num_workers: int) -> None: ...

    # 現在待機中のワーカーペインを取得し、ビジー状態に設定する
    # 戻り値は、後で参照するための一意なID (pane.idなど)
    def acquire_idle_worker(self) -> str | None: ...

    # 指定されたワーカーペインでタスクを実行し、完了まで待機して結果を返す
    def run_task_in_worker(self, worker_id: str, prompt: str) -> str: ...

    # 指定されたワーカーペインを待機状態に戻す
    def release_worker(self, worker_id: str) -> None: ...
    
    # 指定されたワーカーペインのタイトルを更新する
    def update_worker_title(self, worker_id: str, title: str) -> None: ...
```

**2.3. `Orchestrator` → `BaseAgent` (およびそのサブクラス)**

エージェントは直接呼び出されるのではなく、`WorkspaceManager`を介して間接的に実行されます。Orchestratorの責務は、**各エージェントの役割に応じたプロンプトを構築すること**です。

**プロンプト構築メソッド (Orchestrator内に実装):**

```python
class Orchestrator:
    # ...
    def _build_master_plan_prompt(self, requirements_content: str) -> str:
        # 統括AIに計画を立てさせるためのプロンプトを生成
        # prompts/master_plan.txt テンプレートを使用
        ...
        return prompt

    def _build_develop_prompt(self, task: dict) -> str:
        # 開発ワーカーにコーディングさせるためのプロンプトを生成
        # taskオブジェクトの"prompt"フィールドをそのまま使用、または補足情報を追加
        ...
        return prompt

    def _build_review_prompt(self, task: dict, code_diff: str) -> str:
        # QAワーカーにレビューさせるためのプロンプトを生成
        # prompts/qa_review.txt テンプレートとコード差分を使用
        ...
        return prompt

    def _build_test_prompt(self, task: dict) -> str:
        # QAワーカーにテストを生成・実行させるためのプロンプトを生成
        # prompts/qa_test.txt テンプレートを使用
        ...
        return prompt
```

#### 3. 採用による効果

*   **責務の明確化:** 各モジュールがどのような入力（引数）を受け取り、どのような出力（戻り値）を返すかが明確になるため、並行して開発を進めやすくなります。
*   **型安全性:** `str`や`Path`のような型ヒントを活用することで、静的解析ツール（Mypyなど）による型チェックが可能になり、実行時エラーを未然に防ぎます。
*   **テスト容易性:** インタフェースが固定されているため、各コンポーネントの単体テストを容易に記述できます。例えば、`GitManager`をモック（偽物）に置き換えて`Orchestrator`のロジックをテストすることができます。
*   **拡張性:** 将来、`GitManager`の実装をGitHub APIを使うものに差し替えたり、`WorkspaceManager`がローカルのtmuxではなくクラウド上のコンテナを操作するように変更したりする場合でも、このインタフェース仕様に従っている限り、他のコンポーネントに影響を与えずに済みます。

このインタフェース仕様をプロジェクトの「憲法」として定めることで、開発プロセス全体に規律と安定性をもたらします。