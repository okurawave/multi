# System Architecture Design

## Purpose
Clarify the overall structure, technology selection, and roles of each module for ParallelXec-Agent.

## Implementation Details

### 1. Core Engine (Orchestrator)
- Central module for overall control and task management.
- Manages instructions to submodules, progress tracking, and error handling.

### 2. Project Management (Git Repository)
- Version and history management using Git.
- Automate branch operations, Pull Requests, and merges via Git MCP tool.

### 3. Work Environment (Git Worktree)
- Worktree structure enables simultaneous deployment of multiple work branches.
- Independent work directories for each task, enabling parallel work.

### 4. Execution Environment (tmux Session)
- Assign independent tmux sessions for each task, enabling parallel execution and monitoring.
- Orchestrator controls session management, log acquisition, and automatic restart.

### 5. Technology Selection & Integration
- **Python**: Main language for overall control and module integration. Rich libraries and flexibility.
- **libtmux**: Python library for tmux session management. API-based session creation, command injection, log acquisition.
- **watchdog**: File system change monitoring. Used for automatic detection and event-driven processing of Git Worktree and output directories.
- **subprocess**: External command execution and process management. Used for Git operations and CLI tool invocation.
- **Git**: Foundation for project history management, branch operations, Pull Requests. Operated via Git MCP tool and API.

#### Integration Method
- Orchestrator controls each module via Python.
- Session management with libtmux, file monitoring with watchdog, external command execution with subprocess.
- Git MCP tool is called via API for branch, PR, and merge automation.

### 6. Module Responsibility & Integration Flow
- Orchestrator manages overall progress and error handling.
- Git repository management is performed via Git MCP tool.
- Git Worktree separates directories for each task and monitors changes with watchdog.
- tmux sessions are created and managed with libtmux, separating execution environments for each task.
- Each module communicates via API/CLI and reports progress/status to Orchestrator.

## Prerequisites
- Deliverables from Phase 0 (requirements definition, task list) exist.

## Completion Criteria
- Architecture design is documented and roles of each module are clarified.

## References
- [`docs/about.md`](docs/about.md:1) "System Architecture"
- [`docs/how2.md`](docs/how2.md:1) "Directory Structure", "Main Components"
