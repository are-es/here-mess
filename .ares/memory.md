# here-mess — Project Technical Memory

## Core Principles & Decisions
- **Repo Identity**: Fork `are-es/here-mess` at `/home/dolvin/here-mess/` (Branch: `feat/native-plan-mode`). Upstream remote is `upstream`. The installed copy IS the fork.
- **Interaction Modes**:
  - `Shift+Tab` toggles PLAN (explore & design) and BUILD (implementation & tests).
  - PLAN mode strictly permits writing only to planning docs (`.ares/prd.md`, `.ares/roadmap.md`, `.ares/<feature>/prd.md`, `.ares/<feature>/roadmap.md`).
- **Workspace Architecture**:
  - **Root Project Planning**: `.ares/prd.md` & `.ares/roadmap.md` (for initial/greenfield project scope).
  - **Feature Updates / Sub-Workspaces**: `.ares/<feature-name>/prd.md` & `roadmap.md` (only created when building incremental feature updates).
  - **Project Memory**: Centralized at `.ares/memory.md` (covers full codebase gotchas, decisions, and architecture).
  - **Code-Maps Graph**: `.ares/codemaps/` (`map.html`, `map.json`, `checksums.json`).
  - `.ares/` and `.trash/` are internal — never published.
- **Subagent Systems & Delegation**:
  - Simple markdown agent definitions at `~/.hermes/agents/` (`coder`, `reviewer`, `designer`, `debugger`).
  - `tools/delegate_tool.py` enforces Strict Path Scoping: subagents only write within specific target paths passed by Orchestrator.
- **Git Commit & Push Rule**:
  - Strict explicit user approval required before any `git commit` or `git push`.
- **Status Bar & UI Ergonomics**:
  - Frameless vertical height meter (` ▂▃▄▅▆▇█`) for context length monitoring.
  - Quick in-place `/restart` slash command with automatic session resume (`--resume <id>`).
  - Modal card model switcher for `Ctrl+E` with clean alias names and deterministic Enter/Esc confirmation.
  - 2-line status bar positioned BELOW the input box (line 1: model/context/mode/timer, line 2: path/session).

## Fork-Only Features (not upstream — protect during rebase)
- Native PLAN/BUILD interaction mode (`Shift+Tab`), scoped write enforcement in `agent/tool_executor.py` + `agent/agent_runtime_helpers.py` (`_PLAN_READ_ONLY_TOOLS`).
- `agent/verification_stop.py` + `agent/verify_hooks.py` (`verify_on_stop`).
- `plugins/codemaps/` (engine.py, visualizer.py, tools.py) — AST map + Vis.js graph.
- Agent definitions: `agent/agent_definition.py`, `agent/agent_registry.py`, `hermes_cli/agent_cmd.py`.
- `/restart` slash command, `Ctrl+E` model picker (CLI + TUI).
- Title generator anti-greeting delay (`agent/title_generator.py`, `_TRIVIAL_GREETINGS`, 3-turn delay).
- Terminal echo restore on exit (`stty sane echo icanon` in `cli.py::_reset_terminal_input_modes_on_exit`).

## Project Layout (key entry points)
```
run_agent.py          AIAgent — conversation loop (~12k LOC)
cli.py                HermesCLI — prompt_toolkit CLI (~11k LOC)
model_tools.py        tool orchestration, get_tool_definitions()
toolsets.py           TOOLSETS dict, _HERMES_CORE_TOOLS
agent/                prompt_builder, system_prompt, memory, compression,
                      title_generator, tool_executor, ssl_guard
hermes_cli/           subcommands, config.py, config_defaults.py,
                      commands.py (COMMAND_REGISTRY), curses_ui, skin_engine
tools/                one file per tool, auto-discovered via tools/registry.py
gateway/              messaging gateway + platforms/
ui-tui/               Ink (React) TUI  →  tui_gateway/ (Python JSON-RPC)
plugins/              codemaps (ours), memory/, model-providers/, ...
tests/                pytest suite
```
Config: `~/.hermes/config.yaml` (settings) + `~/.hermes/.env` (SECRETS ONLY). Logs: `hermes logs [--follow]`.

## Upstream Sync
- `hermes update` ABORTS the rebase on the first conflict and resets. Do not use it mid-rebase. Run `git rebase upstream/main` manually and resolve conflict-by-conflict.
- Recurring conflict sites:
  - `hermes_cli/config_defaults.py` — `_config_version` literal.
  - `hermes_cli/config_migrations.py` — `MIGRATIONS` registry; renumber our migrations above upstream's.
  - `hermes_cli/commands.py` — `/restart` CommandDef (ours is session-scoped, upstream's is gateway-only).
  - `cli.py` — modal widget wiring (command palette vs model switcher).

## Prompt Budget (context economy)
- Context-file priority in `agent/prompt_builder.py::build_context_files_prompt` is `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`, FIRST MATCH WINS. `.hermes.md` exists specifically to occupy that slot so the 83KB upstream `AGENTS.md` (~21k tokens/call) is not injected. Deleting `.hermes.md` silently re-injects `AGENTS.md`.
- `.ares/memory.md` is NOT auto-injected — it is read on demand with `read_file`.
- Context files are capped (default 20,000 chars, `context_file_max_chars`) with HEAD 0.7 / TAIL 0.2 truncation (`CONTEXT_TRUNCATE_HEAD_RATIO` / `_TAIL_RATIO`, `agent/prompt_builder.py:1425`). The MIDDLE is silently dropped. `~/.hermes/SOUL.md` is 23,330 chars — sections ~§21-§24 (Private Files, Context7, Browser Rules, Execution Workflow) are currently being cut.
- Tool schemas cost ~14-20k tokens/call. Disable unused toolsets with `hermes tools`.
- `session_search` scroll windows dump full `tool_calls` including multi-KB base64 `call_id` values. Use `window<=3` or a targeted `query=`.

## Pitfalls (hit in this repo)
- `scripts/run_tests.sh` without `HERMES_PYTHON=/mnt/hdd/venv/bin/python` → "no virtualenv with pytest found".
- Duplicate skill directory names anywhere under `~/.hermes/skills/` → "Failed to load skill". One directory per skill name.
- Unbounded `rglob`/`glob` over a repo freezes. Use `os.walk` with in-place `dirnames[:]` pruning plus a depth bound (see `plugins/codemaps/engine.py`, `tools.py`).
- `\033[K` in spinner/display code leaks as literal `?[K` under `patch_stdout`. Space-pad instead.
- Tool schema descriptions must not name tools from other toolsets — the model hallucinates calls to unavailable tools. Add cross-refs dynamically in `get_tool_definitions()`.
- Stale `SSL_CERT_FILE` breaks auxiliary calls — self-heal lives in `agent/ssl_guard.py`.
- `except Exception: pass` around helper calls hides `NameError` from missing imports (bit us in `plugins/codemaps/tools.py` with `IGNORED_DIRS`).

## Settings Expansion (Memory / Config / Model tabs) — 2026-08-24
- **PRD/Roadmap**: `.ares/settings_expansion/`.
- **Model dropdown label fix** (`model-dropdown.tsx`): label precedence
  `session.info.model → model.options top-level model → "default"`; provider
  rows key on `slug ?? id`; active provider gets a `current` marker.
- **Backend whitelist** (`tui_gateway/server.py`): `_SETTINGS_WHITELIST`
  frozenset + new branch in `config.set` before the final `unknown config key`
  error. Covers `compression.*`, `auxiliary.<task>.*`, `memory.*_char_limit`.
  api_key writes are stored but never echoed. Constants near `_STATUSBAR_MODES`.
- **`settings_snapshot`**: handled as a `config.get` key (methods_config.py,
  after `mtime`). Returns compression/auxiliary/memory/model; only
  `has_api_key` booleans, never secrets.
- **Memory RPCs**: `tui_gateway/methods_memory.py` — `memory.list`,
  `memory.write` (add/replace/remove via `load_on_disk_store()`, so locking +
  drift detection apply). Registered in server.py's split-module import list.
- **Frontend tabs**: `settings-model.tsx` (+provider auth modal; oauth shows
  CLI hint, no fake login), `settings-config.tsx` (click-only rows),
  `settings-memory.tsx` (per-entry cards, inline edit, two-click delete,
  add form with remaining-bytes guard), store `store/settings-backend.ts`,
  styles `styles/settings-extra.css` (imported from global.css).
- **Tests**: `tests/test_gateway_settings_rpc.py` (18 tests) +
  `settings-{model,config,memory}.test.tsx`. Vitest total 56/56.
- **Vitest quirk**: bare `npx vitest run` fails with `React.act is not a
  function` — production React build lacks `act`. Use
  `NODE_ENV=development npx vitest run`.
- **Pre-existing failures**: `tests/test_tui_gateway_server.py` has 11 fails
  on clean HEAD too (verified twice via git stash) — NOT caused by this work.
- **Crash lesson (2026-08-24)**: PC restart truncated ~22 tracked files to
  0 bytes (server.py, methods_config.py, config_defaults.py, file_tools.py...).
  Recovery = `git checkout -- <files>`; untracked work survived. After any hard
  crash, check for empty tracked files before running anything.

## TUI notify-vs-render race fix (2026-08-26)
- Symptom: turn-completion popup/sound fired before Ink committed the final
  transcript, so the notification appeared 1-2s before the visible response
  ("frozen" feel). Root cause: `message.complete` handler spawned the cue
  synchronously; the final-message markdown parse + syntax highlight + Yoga
  layout block that same commit.
- Fix: `ui-tui/src/app/createGatewayEventHandler.ts` (~line 1438) defers
  `notifyTurnComplete` via `requestIdleCallback` (timeout 500ms), fallback
  `setTimeout(cue, 150)`. Verified: typecheck, notifySound vitest 19/19,
  build. Fork-only change — protect during rebase.
