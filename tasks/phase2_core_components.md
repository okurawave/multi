# タスクID: phase2_core_components

## タイトル
コアコンポーネント実装

## 目的
ParallelXec-Agentの主要モジュール（vcs.py, workspace.py, agents.py, orchestrator.py, main.py）の実装

## 実装内容
- 各モジュールの役割と責務に沿った実装
- GitManager, WorkspaceManager, BaseAgent, Orchestratorクラスの設計・実装
- 必要な外部ライブラリの導入  
  - click  
  - libtmux  
  - pyyaml  
  - python-dotenv  
  - prompt_toolkit  
  - watchdog  
- ディレクトリ構造とファイル配置の明示

## 前提条件
フェーズ1のアーキテクチャ設計が完了していること

## 完了条件
主要モジュールのソースコードが作成され、動作可能な状態であること

## 参考
- docs/how2.md「主要コンポーネント」「ディレクトリ構造」「実装ガイド」