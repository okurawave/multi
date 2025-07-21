# タスクID: phase4_interface_spec

## タイトル
インターフェース仕様実装

## 目的
ParallelXec-Agentの主要コンポーネント間のインターフェース仕様（メソッドシグネチャ・データフォーマット・JSONスキーマ）の明文化

## 実装内容

### 1. JSONスキーマ定義
#### tasks.json
- タスク一覧管理用JSON
- スキーマ例:
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": { "type": "string" },
      "title": { "type": "string" },
      "description": { "type": "string" },
      "status": { "type": "string", "enum": ["pending", "in_progress", "done", "error"] }
    },
    "required": ["id", "title", "status"]
  }
}
```

#### task_status.json
- タスク進捗・状態管理用JSON
- スキーマ例:
```json
{
  "type": "object",
  "properties": {
    "taskId": { "type": "string" },
    "status": { "type": "string", "enum": ["pending", "in_progress", "done", "error"] },
    "progress": { "type": "number", "minimum": 0, "maximum": 100 },
    "message": { "type": "string" }
  },
  "required": ["taskId", "status", "progress"]
}
```

### 2. Orchestrator→各コンポーネント間メソッドシグネチャ設計

#### Orchestrator→GitManager
- `fetchLatestMain(): Promise<void>`
- `createFeatureBranch(issueId: string, description: string): Promise<string>`
- `mergeMainToFeature(featureBranch: string): Promise<void>`
- `createPullRequest(featureBranch: string): Promise<string>`
- `deleteBranch(branchName: string): Promise<void>`

#### Orchestrator→WorkspaceManager
- `setupWorkspace(config: WorkspaceConfig): Promise<void>`
- `updateFile(path: string, content: string): Promise<void>`
- `readFile(path: string): Promise<string>`
- `runTests(): Promise<TestResult[]>`

#### Orchestrator→BaseAgent
- `executeTask(task: Task): Promise<TaskResult>`
- `getStatus(taskId: string): Promise<TaskStatus>`

### 3. プロンプト構築メソッド設計
- `buildPrompt(task: Task, context: Context): string`
- `buildReviewPrompt(diff: string, testResult: TestResult): string`
- `buildMergePrompt(prInfo: PullRequestInfo): string`

### 4. 設計方針
- 型安全性: TypeScript等の型定義を活用し、インターフェース・データ構造の一貫性を担保
- テスト容易性: 各メソッドは単体テスト可能な設計とし、モック化しやすい構造を推奨
- 拡張性: 新規コンポーネント追加や仕様変更時も既存インターフェースへの影響を最小化

## 前提条件
- コアコンポーネント・AIエージェント設計が完了していること

## 完了条件
- インターフェース仕様が明文化され、各コンポーネント間の連携方法が明確になっていること

## 参考
- [docs/how2.md](../docs/how2.md)「インターフェース仕様補足」