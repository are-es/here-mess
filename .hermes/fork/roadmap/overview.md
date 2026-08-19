# Roadmap Overview: Here-Mess Custom Feature Set

## Completed Tasks

### Task 001: Native PLAN/BUILD Interaction Mode & Live Mid-Response Steering
- Status: **DONE**
- Implemented in: `cli.py`, `run_agent.py`, `agent/tool_executor.py`, `agent/agent_runtime_helpers.py`

### Task 002: Provider-Level & Global 1M Context Length Inheritance
- Status: **DONE**
- Implemented in: `hermes_cli/config.py`, `agent/model_metadata.py`
- Test suite: `tests/agent/test_default_context_length.py`

### Task 003: Interactive Model Alias Dashboard (`hermes model alias`)
- Status: **DONE**
- Implemented in: `hermes_cli/alias_cmd.py`, `hermes_cli/subcommands/model.py`
- Test suite: `tests/hermes_cli/test_alias_cmd.py`

### Task 004: Alt-Tab Model Switcher Hotkey (`Ctrl+E`)
- Status: **DONE**
- Implemented in: `cli.py` (with clean short alias pill formatting)

### Task 005: Environment Stability & False-Positive Bug Fixes
- Status: **DONE**
- Fixed: Stale CA bundle self-healing (`agent/ssl_guard.py`), binary relaunch priority (`hermes_cli/relaunch.py`), CWD deprecation warning false-positive (`hermes_cli/config.py`).
- Test suite: `tests/hermes_cli/test_deprecated_cwd_warning.py`, `tests/hermes_cli/test_relaunch.py`
