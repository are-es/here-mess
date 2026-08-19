---
feature: here-mess-fork-features
doc: technical
status: new
updated_at: 2026-08-19T14:30:00+07:00
---

# Technical Architecture & File Map

## 1. Key Component Modifications

| Component | Target File | Purpose |
|---|---|---|
| **Model Switcher Hotkey** | `cli.py` | Implements `_model_switcher_state`, `Ctrl+E` keybinding rotation, and clean pill rendering. |
| **Alias Manager CLI** | `hermes_cli/alias_cmd.py` | Curses radiolist UI for dashboard, CRUD operations, and core model picker bridge. |
| **Model Subcommand Parser** | `hermes_cli/subcommands/model.py` | Registers `hermes model alias` and `hermes alias` subcommands. |
| **Context Length Engine** | `agent/model_metadata.py` | Adds `agent.default_context_length` fallback resolution. |
| **Provider Config Resolver** | `hermes_cli/config.py` | Implements provider-level `default_context_length` fallback and CWD warning false-positive fix. |
| **Session Relaunch Engine** | `hermes_cli/relaunch.py` | Prioritizes `~/.local/bin/hermes` wrapper for robust venv execution. |
| **SSL Guard Self-Healing** | `agent/ssl_guard.py` | Detects and corrects stale `SSL_CERT_FILE` references post directory rename. |
| **Scoped Mode Tool Executor** | `agent/tool_executor.py` | Enforces scoped path whitelist during PLAN mode execution. |

## 2. Test Verification Matrix
- `tests/hermes_cli/test_alias_cmd.py`: Tests alias CRUD operations and persistence.
- `tests/agent/test_default_context_length.py`: Tests provider-level and global context inheritance.
- `tests/hermes_cli/test_deprecated_cwd_warning.py`: Validates non-false-positive CWD warning logic.
- `tests/hermes_cli/test_relaunch.py`: Validates binary resolution priority.
