# Interface Specification (Phase 4)

## 1. JSON Schema Definitions

### tasks.json
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

### task_status.json
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

## 2. Orchestrator Component Method Signatures

### Orchestrator→GitManager
- `fetchLatestMain(): Promise<void>`
- `createFeatureBranch(issueId: string, description: string): Promise<string>`
- `mergeMainToFeature(featureBranch: string): Promise<void>`
- `createPullRequest(featureBranch: string): Promise<string>`
- `deleteBranch(branchName: string): Promise<void>`

### Orchestrator→WorkspaceManager
- `setupWorkspace(config: WorkspaceConfig): Promise<void>`
- `updateFile(path: string, content: string): Promise<void>`
- `readFile(path: string): Promise<string>`
- `runTests(): Promise<TestResult[]>`

### Orchestrator→BaseAgent
- `executeTask(task: Task): Promise<TaskResult>`
- `getStatus(taskId: string): Promise<TaskStatus>`

## 3. Prompt Construction Methods
- `buildPrompt(task: Task, context: Context): string`
- `buildReviewPrompt(diff: string, testResult: TestResult): string`
- `buildMergePrompt(prInfo: PullRequestInfo): string`

## 4. Design Principles
- Type safety: Use TypeScript type definitions to ensure consistency of interfaces and data structures
- Testability: Each method should be designed for unit testing and easy mocking
- Extensibility: Minimize impact on existing interfaces when adding new components or changing specifications

## References
- [docs/how2.md](../docs/how2.md)
