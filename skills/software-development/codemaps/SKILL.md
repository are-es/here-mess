---
name: codemaps
description: "Use when starting work in any project to discover architecture, symbol connections, and technical memory. Triggers code_maps tool."
---

# Code-Maps Architecture & Project Discovery Protocol

This skill governs how AI agents navigate, understand, and document the structure of any software project using the native `code_maps` tool, standardized Vis.js Balloon templates, and persistent workspace memory.

---

## 1. Core Purpose

Instead of wasting thousands of tokens reading raw source files one by one with `search_files` or `read_file` on every session startup, agents must use **Code-Maps** as the primary architectural map of the project.

---

## 2. Standard Operating Procedure (SOP)

### Phase 1: Project Discovery & Map Check (Cold Start)
Whenever you start a new task or explore a project:
1. **Search for Existing Map (Passive Read-Only)**:
   - Check if a codemaps directory exists in the workspace (e.g. `./codemaps/`, `./.ares/codemaps/`, `./.hermes/<feature>/codemaps/`).
   - You may call `code_maps(action="scan")` ONLY to discover existing maps.
2. **Strict Generation Guardrails**:
   - **Case A: Map Already Exists**:
     - **DO NOT REBUILD OR SCAN RAW FILES**.
     - Read the summary, inspect `map.json` / `memory.md`, or use `code_maps(action="query", query="...")`.
   - **Case B: No Map Exists & No Explicit User Command**:
     - **DO NOT AUTOMATICALLY CREATE A CODEMAPS DIRECTORY**.
     - Continue your normal task using standard exploration tools. Do not pollute the repository with unrequested map files.
   - **Case C: Explicit User Command (`/codemaps`, "bikin codemaps", "petakan project")**:
     - Only when explicitly commanded by the user, invoke `code_maps(action="scan")` on an active codebase to generate `map.json`, `map.html`, `checksums.json`, and `memory.md`.

---

### Phase 2: HTML Visualizer Template Standard
Whenever generating or customizing `map.html`, agents **MUST** follow the official template at `templates/map-template.html`:
- **UI Theme**: Deep Obsidian Technical Grid (`#08080a`, `#060608` with subtle 32px dotted grid lines).
- **Node Geometry**: Vis.js 3D Sphere Balloons rendered via embedded SVG radial gradients with specular reflection arcs (Cyan for Files, Purple for Classes, Emerald for Functions).
- **Interaction Engine**:
  - Full Pan, Zoom in/out, and Physics Dragging (`zoomView: true, dragView: true, dragNodes: true`).
  - Active Selection Focus: Selected node and its direct connections stay bright; unconnected nodes fade to deep matte dim.
  - Auto-Sync Polling: Live fetch of `map.json` every 3s to hot-reload graph without page refreshes.

---

### Phase 3: Targeted Querying During Execution
When you need to understand dependencies, callers, or definitions:
- **DO NOT** run blind grep/regex across the whole repository.
- Call `code_maps(action="query", query="<symbol_name>")`.
- Trace the relationships directly from the pre-computed AST knowledge graph.

---

### Phase 4: Post-Implementation Sync & Memory Preservation
Whenever you complete a major feature, modify core engines, or resolve tricky bugs in BUILD mode:
1. **Sync Incremental Diff**:
   - Run `code_maps(action="update")`.
   - The engine will verify file checksums via `checksums.json`. If no files changed, it completes in 0.01s. If files changed, it automatically updates `map.json` and regenerates the 3D Sphere Balloon visualizer (`map.html`).
2. **Persist Architecture Gotchas**:
   - If you discovered non-obvious workarounds, API signatures, or environment quirks, save them to the project memory:
     ```json
     code_maps(action="memory_save", note="<concrete gotcha or decision rationale>")
     ```

---

## 3. Directory & Scope Isolation Rules

- **Code-Maps Directory**: Holds `map.json`, `map.html`, `checksums.json`, and `memory.md`. Configurable via `output_folder` in `plugin.yaml` or `agent.folder` in config.
- **Context Planning Directory**: Holds `prd.md`, `roadmap.md`, and `preview/` files.
- **Engine-Only Principle**: Code-maps strictly extracts executable source code. It never clutters the graph with test fixtures, documentation, or temporary builds.

---

## 4. Verification Checklist

- [ ] Ran `code_maps(action="scan")` before reading raw source files.
- [ ] Checked `map.html` matches `templates/map-template.html` visual standard.
- [ ] Read `memory.md` for existing project decisions.
- [ ] Used `code_maps(action="query")` for fast symbol lookups.
- [ ] Ran `code_maps(action="update")` after modifying core codebase files.
- [ ] Saved any newly discovered gotchas with `code_maps(action="memory_save")`.
