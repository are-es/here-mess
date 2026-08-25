# PRD: Circular Context Meter & Consolidated Inspector Popover

## 1. Overview
Replace the linear context progress bar with a high-precision circular progress gauge in the desktop shell composer controls. When hovered or clicked, a consolidated inspector card displays the total fixed prefix footprint (System prompt + Major blocks + Tool schemas unified into summary lines) and active conversation context.

## 2. Requirements

### 2.1 Circular Progress Meter (UI)
- SVG circular ring (diameter 22–24px) with background track and dynamic stroke offset matching `context_percent`.
- Threshold color coding:
  - `< 60%`: `--accent` (`#3b82f6` / cyan)
  - `60% - 85%`: `--accent-amber` (`#f59e0b`)
  - `> 85%`: `--danger` (`#ef4444`)
- Inline label next to circle displaying compact numbers: `${used_tokens} / ${max_tokens}` (e.g. `100k/1M`).

### 2.2 Consolidated Inspector Card (Unified Summary)
- Trigger on mouse enter / click with click-outside dismiss.
- **Card Layout**:
  - **Header**: Used / Max tokens (`100k / 1M (10%)`) + Active Model tag.
  - **Fixed Prompt Prefix (Consolidated Totals)**:
    - `System Prompt`: Total bytes & KB (`50.9 KB`) with inline breakdown tag (`Skills: 4.2 KB | Memory: 3.9 KB | Profile: 4.6 KB`).
    - `Tool Schemas`: Unified total size & count (`45.0 KB (18 tools)`).
    - `Total Fixed Prefix`: Combined byte weight (`94.7 KB`).
  - **Active Session**:
    - `Conversation History`: Estimated tokens & message count.
    - `Context Limit`: Total capacity and utilization gauge.

### 2.3 Gateway Data Binding
- Use `session.context_breakdown` and `session.prompt_size` from gateway to populate exact byte counts and token counts.

## 3. Non-Functional Constraints
- Pure token CSS custom properties.
- Zero extra external NPM dependencies.
- Fast render response (<30ms).
