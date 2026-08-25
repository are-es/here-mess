# Roadmap: ARES Desktop Shell UI Refinements & Features

## Milestones
- [ ] Task 001: 2-Tier Hierarchical Model Picker (Provider list -> Model list with back button)
- [ ] Task 002: Context Meter Responsive Fix & Proactive Usage/Breakdown Refresh
- [ ] Task 003: Tactical Command & Skill Palette Card/Modal with Sub-Navbar Tabs (`Commands` & `Skills`)
- [ ] Task 004: Full Keyboard Shortcuts Suite Wiring (`Shift+Tab`, `Ctrl+P`, `Ctrl+K`, `Ctrl+N`, `Ctrl+L`, `Ctrl+B`, `Ctrl+,`, `Esc`)
- [ ] Task 005: Collapsible Workspace Sidebar (Header toggle + `Ctrl+B` + icon-rail/hide state)
- [ ] Task 006: Workspace Path Indicator & Native OS Folder Picker for New Sessions
- [ ] Task 007: Comprehensive Vitest, Clippy & Cargo Test Suite Verification

---

### Task 001: 2-Tier Hierarchical Model Picker
- **Goal**: In `model-dropdown.tsx`, implement two-tier selection:
  - Tier 1: Show configured providers (OpenAI, Anthropic, OpenRouter, Nous, etc.) with model count badges.
  - Tier 2: Selecting a provider opens its model list with a `‹ Back` header button.
- **Acceptance Criteria**:
  - [ ] Opening dropdown shows providers first.
  - [ ] Clicking a provider reveals only its models.
  - [ ] Clicking `‹ Back` returns to the provider view.
  - [ ] Selecting a model applies `config.set` and updates active session.

### Task 002: Context Meter Responsive Fix & Proactive Usage/Breakdown Refresh
- **Goal**:
  - Anchor `.context-popover` to `right: 0; left: auto; max-width: min(320px, calc(100vw - 32px))` in `composer.css`.
  - Add active `refreshUsage()` in `sessions.ts` on session switch, resume, and stream finish.
- **Acceptance Criteria**:
  - [ ] Context popover never overflows the viewport on narrow windows.
  - [ ] Progress ring advances and updates percentage/tokens accurately.

### Task 003: Tactical Command & Skill Palette Card/Modal with Sub-Navbar Tabs
- **Goal**:
  - Add `⚡ Actions` trigger card in composer and support `Ctrl+K` / `/`.
  - Open palette modal with top search input and sub-navbar `[ Commands ]` / `[ Skills ]`.
  - Tab 1: All Hermes slash commands (`/new`, `/clear`, `/compress`, `/title`, `/fork`, `/save`, `/diff`, `/yolo`, etc.).
  - Tab 2: Full `~/.hermes/skills/` catalog (`cavpon`, `codemaps`, `ai-researcher`, `scrapling`, `impeccable`, `openhue`, etc.).
  - Clicking/Enter on any item auto-injects command or `/skill <name>` into composer and focuses textarea.
- **Acceptance Criteria**:
  - [ ] Modal opens via button click, `/` prefix, or `Ctrl+K`.
  - [ ] Sub-navbar seamlessly switches between Commands and Skills.
  - [ ] Real-time search filters items in the active tab.
  - [ ] Item selection auto-injects text into the composer.

### Task 004: Full Keyboard Shortcuts Suite Wiring
- **Goal**: Wire all default and custom shortcuts via capture-phase listener:
  - `Shift+Tab` / `Ctrl+M`: Toggle Plan/Build mode.
  - `Ctrl+P` / `Alt+M`: Toggle 2-tier Model Picker.
  - `Ctrl+K`: Toggle Command & Skill Palette modal.
  - `Ctrl+N`: New session creation.
  - `Ctrl+L`: Focus composer textarea.
  - `Ctrl+B`: Toggle sidebar collapse.
  - `Ctrl+,`: Toggle settings modal.
  - `Escape`: Cancel stream / close popovers / clear query.
- **Acceptance Criteria**:
  - [ ] All 8 shortcuts execute their respective actions reliably.
  - [ ] Editable via Settings Shortcuts tab.

### Task 005: Collapsible Workspace Sidebar
- **Goal**: Add collapse/expand toggle to Sidebar header and support `Ctrl+B`.
- **Acceptance Criteria**:
  - [ ] Sidebar collapses smoothly to icon-rail or zero width.
  - [ ] Transcript and composer expand to fill available space.
  - [ ] Preference persists across app reloads.

### Task 006: Workspace Path Indicator & Native OS Folder Picker for New Sessions
- **Goal**:
  - Display monospaced current workspace directory path under composer box.
  - Add `+ Open Folder` button in New Session flow calling native folder dialog via Tauri bridge.
- **Acceptance Criteria**:
  - [ ] Current session `workdir` is clearly visible under composer.
  - [ ] Picking a new folder creates a session bound to that folder path.

### Task 007: Comprehensive Verification & Test Suite
- **Goal**: Validate all frontend unit tests, typechecks, Rust clippy, and cargo test suites.
- **Acceptance Criteria**:
  - [ ] `npm test` 100% pass.
  - [ ] `tsc` & `vite build` clean with 0 warnings/errors.
  - [ ] `cargo clippy` and `cargo test` pass cleanly.
