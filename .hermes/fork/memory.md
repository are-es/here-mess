# Project Memory & Architecture Gotchas: Here-Mess Fork

## Critical Operational Rules
1. **Interactive Alias CLI**: Must use built-in curses (`hermes_cli.curses_ui.curses_radiolist`) to avoid external dependencies like `questionary` in clean environments.
2. **Model Switcher UX**: `Ctrl+E` pills must render only the short alias identifier (`▶ 1. fast ◀`), stripping long provider substrings to preserve composer screen real estate.
3. **Context Length Inheritance**:
   - `custom_providers[i].default_context_length` (or `context_length`) applies across all models on that endpoint.
   - `agent.default_context_length` in `config.yaml` provides the ultimate fallback before hardcoded static values.
4. **Session Resume & Binary Priority**:
   - `resolve_hermes_bin()` must prioritize `~/.local/bin/hermes` to guarantee execution inside the managed virtualenv.
5. **CWD Deprecation Guard**:
   - `warn_deprecated_cwd_env_vars()` must check whether `terminal.cwd` exists in `config.yaml` to avoid flagging runtime bridged `TERMINAL_CWD` exports as stale `.env` variables.
