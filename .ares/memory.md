# here-mess — Project Technical Memory

## Core Principles & Decisions
- **Repo Identity**: Fork `are-es/here-mess` at `/home/dolvin/here-mess/` (Branch: `feat/native-plan-mode`).
- **Interaction Modes**:
  - `Shift+Tab` toggles PLAN (explore & design) and BUILD (implementation & tests).
  - PLAN mode strictly permits writing only to planning docs (`.ares/prd.md`, `.ares/roadmap.md`, `.ares/<feature>/prd.md`, `.ares/<feature>/roadmap.md`).
- **Workspace Architecture**:
  - **Root Project Planning**: `.ares/prd.md` & `.ares/roadmap.md` (for initial/greenfield project scope).
  - **Feature Updates / Sub-Workspaces**: `.ares/<feature-name>/prd.md` & `roadmap.md` (only created when building incremental feature updates).
  - **Project Memory**: Centralized at `.ares/memory.md` (covers full codebase gotchas, decisions, and architecture).
  - **Code-Maps Graph**: `.ares/codemaps/` (`map.html`, `map.json`, `checksums.json`).
- **Subagent Systems & Delegation**:
  - Simple markdown agent definitions at `~/.hermes/agents/` (`coder`, `reviewer`, `designer`, `debugger`).
  - `tools/delegate_tool.py` enforces Strict Path Scoping: subagents only write within specific target paths passed by Orchestrator.
- **Git Commit & Push Rule**:
  - Strict explicit user approval required before any `git commit` or `git push`.
- **Status Bar & UI Ergonomics**:
  - Frameless vertical height meter (` ▂▃▄▅▆▇█`) for context length monitoring.
  - Quick in-place `/restart` slash command with automatic session resume (`--resume <id>`).
  - Modal card model switcher for `Ctrl+E` with clean alias names and deterministic Enter/Esc confirmation.
