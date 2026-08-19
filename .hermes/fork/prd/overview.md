---
feature: here-mess-fork-features
doc: overview
status: new
updated_at: 2026-08-19T14:30:00+07:00
---

# Feature Overview: Here-Mess Fork Innovations & Custom Architecture

## 1. Problem Statement
Upstream Hermes is designed as a generalized agent core, but power users and local orchestrators need:
1. Safe exploration & architectural design mode (**Scoped PLAN Mode**).
2. Frictionless model switching during multi-stage coding workflows (**Ctrl+E Alt-Tab Switcher** & **Interactive Alias Manager**).
3. Zero-repetition context length scaling for multiplexed custom endpoints (**Provider-Level 1M Context Engine**).
4. Sub-workspace feature tracking without global clutter (`.hermes/<feature>/`).
5. Bulletproof operational stability against directory renames, venv re-launches, and config false-positives.

## 2. Implemented Capabilities
- **Scoped PLAN Mode**: Enforces inspect-before-mutate, restricts file mutations to planning artifacts, supports live mid-turn mode switching via `Shift+Tab`.
- **Interactive Model Alias Manager (`hermes model alias`)**: Native curses UI dashboard for managing aliases with seamless redirection to the upstream provider picker.
- **Alt-Tab Style Model Switcher (`Ctrl+E`)**: Horizontal popup pill rotation in the CLI composer for instant model switching.
- **Provider-Level & Global Context Fallback**: Automatic 1M context inheritance across all models in a custom provider.
- **Resilient Self-Healing Relaunch & SSL Guards**: Dynamic CA bundle resolution and wrapper priority for error-free session resumption.
