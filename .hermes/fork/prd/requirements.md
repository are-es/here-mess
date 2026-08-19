---
feature: here-mess-fork-features
doc: requirements
status: new
updated_at: 2026-08-19T14:30:00+07:00
---

# Feature Requirements: Here-Mess Modular Architecture

## P0: Core Functional Requirements
1. **Interactive Model Alias CLI (`hermes model alias`)**:
   - MUST display all defined aliases and a `➕ [+ Create New Alias]` item on the home dashboard.
   - MUST redirect to the core `select_provider_and_model` picker upon alias name input.
   - MUST persist valid alias definitions under `model_aliases.<name>` in `config.yaml`.
2. **Alt-Tab Model Switcher Hotkey (`Ctrl+E`)**:
   - MUST cycle through configured aliases on successive `Ctrl+E` presses.
   - MUST render clean, concise pill labels without verbose provider strings.
   - MUST support left/right navigation and Enter to commit.
3. **Provider-Level Context Length**:
   - `custom_providers[i].context_length` MUST automatically apply to all child models missing an explicit override.
   - `agent.default_context_length` MUST serve as the universal fallback before hardcoded defaults.
4. **Scoped PLAN Mode & Live Steering**:
   - Whitelist allowed write paths: `.hermes/**/prd/**`, `.hermes/**/roadmap/**`, `memory.md`, `.ares/**`, and root plan files.
   - Live mid-stream mode toggle must steer active turns immediately via `queue_redirect()`.
