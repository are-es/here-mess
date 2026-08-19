# here-mess Project Architecture & Memory

## Core Principles & Decisions
- **Repo Identity**: Fork `are-es/here-mess` at `/home/dolvin/here-mess/` (Branch: `feat/native-plan-mode`).
- **Code-Maps Plugin**: Standalone plugin at `plugins/codemaps/` (symlinked to `~/.hermes/plugins/codemaps`).
  - Uses AST engine ignoring tests/fixtures to keep graphs tight and responsive.
  - Interactive Vis.js 3D Sphere Balloon Visualizer at `map.html` with Deep Obsidian Technical Grid theme (`#08080a`, `#060608`).
  - Live auto-sync polling loop hot-reloads graph from `map.json` every 3s.
  - Template locked at `skills/software-development/codemaps/templates/map-template.html`.
- **Planning Convention (2-File Rule)**:
  - Scoped PLAN mode strictly writes to `.ares/<feature>/prd.md` and `.ares/<feature>/roadmap.md` (plus optional `preview/` HTML files).
  - No separate memory files in feature folders; technical memory is unified here in `.ares/codemaps/memory.md`.
- **Navigation Efficiency**:
  - `tools/file_tools.py` (`read_file` & `search_files`) schema prompts guide agents to inspect Table of Contents via `search_files(pattern='^#{1,3} .*')` before reading large files by targeted `offset`/`limit`.
- **Subagent Delegation Guardrails**:
  - `tools/delegate_tool.py` enforces Strict Path Scoping: subagents must only write to specific paths declared in task/context.
