# Roadmap: TUI UX Polish, WhatsApp Bubble Chat & Ares Skins

## Milestones
- [x] Task 001: Implement TUI In-Place Session Restart Protocol (Exit Code 43)
- [x] Task 002: Implement Direct Model Stage Selection for Ctrl+E in ModelPicker
- [x] Task 003: Implement WhatsApp-Style Bubble Chat Layout (Right User, Left Ares Box with 'ares [HH:MM]' Header, Unboxed Dark Gray Reasoning with Inline '▰▱▱▱' Spinner)
- [x] Task 004: Create 'ares' (Ice Blue/Slate) and 'ares-pink' Skins with Banner Art from xxxx.yaml
- [x] Task 005: Implement Compact Stacked RGB Slim Context Gauge, '༄' Separator, & Remove Idle 'ready' Text
- [x] Task 006: Implement Symmetrical CWD & Title Badges with Responsive 2-Line Footer Wrapping
- [x] Task 007: Rebuild Bundle & Verify End-to-End Tests

---

### Task 001: Implement TUI In-Place Session Restart Protocol (Exit Code 43)
- **Goal**: Enable `/restart` in TUI to seamlessly relaunch the process and restore the active session.
- **Acceptance Criteria**:
  - [ ] `/restart` command in `ui-tui/src/app/slash/commands/session.ts` calls `process.exit(43)`.
  - [ ] `hermes_cli/main.py` catches exit code `43`, reads `active_session_file`, and triggers `relaunch(["chat", "--tui", "--resume", sid])`.
  - [ ] Exit summary banner is omitted for code 43 to avoid noisy outputs during restart.
  - [ ] Python unit tests verify the exit code 43 handling in `tests/hermes_cli/`.
- **Technical Notes**:
  - Files: `ui-tui/src/app/slash/commands/session.ts`, `hermes_cli/main.py`.

---

### Task 002: Implement Direct Model Stage Selection for Ctrl+E in ModelPicker
- **Goal**: Make `Ctrl+E` immediately open the model selection list instead of the provider selector.
- **Acceptance Criteria**:
  - [ ] `OverlayState['modelPicker']` updated to accept `{ refresh?: boolean; initialStage?: 'provider' | 'model' }`.
  - [ ] `ModelPicker` component initialises `stage` state using `initialStage || 'provider'`.
  - [ ] `useInputHandlers.ts` sets `patchOverlayState({ modelPicker: { initialStage: 'model' } })` on `Ctrl+E`.
  - [ ] `Ctrl+O` retains the default `provider` stage workflow.
  - [ ] Tests in `ui-tui/src/__tests__/modelPicker.test.ts` pass.
- **Technical Notes**:
  - Files: `ui-tui/src/app/interfaces.ts`, `ui-tui/src/components/modelPicker.tsx`, `ui-tui/src/components/appOverlays.tsx`, `ui-tui/src/app/useInputHandlers.ts`.

---

### Task 003: Implement WhatsApp-Style Bubble Chat Layout
- **Goal**: Render user prompts aligned right in a bubble box and Ares responses aligned left inside a rounded box with `ares [HH:MM]` header, keeping reasoning as unboxed dark gray text above it with inline `▰▱▱▱` spinner.
- **Acceptance Criteria**:
  - [ ] User message rendered with `alignSelf="flex-end"` inside a rounded border box (`borderColor={t.color.border}`).
  - [ ] Ares assistant response rendered with `alignSelf="flex-start"` inside a rounded border box (`borderColor={t.color.accent}` or `t.color.border`).
  - [ ] Header above Ares box displays `ares [HH:MM]` timestamp label.
  - [ ] Reasoning/thinking rendered unboxed with dark gray color (`color={t.color.muted}`, `dim={true}`) and live `▰▱▱▱` spinner inline next to thinking header.
  - [ ] Native per-action reasoning trail preserved (no forced single-turn merge).
  - [ ] Tests in `messageLine.test.ts` and `thinkingLiveCollapse.test.tsx` pass.
- **Technical Notes**:
  - Files: `ui-tui/src/components/messageLine.tsx`, `ui-tui/src/components/thinking.tsx`.

---

### Task 004: Create 'ares' and 'ares-pink' Skins
- **Goal**: Add two customized skins in `~/.hermes/skins/` using the banner art & logo from `xxxx.yaml`.
- **Acceptance Criteria**:
  - [ ] `~/.hermes/skins/ares.yaml`: Light blue / ice cyan primary (`#00f2fe`) paired with deep slate, custom ASCII banner logo & hero from `xxxx.yaml`.
  - [ ] `~/.hermes/skins/ares-pink.yaml`: Vibrant pink (`#ff70a6`), sakura magenta, and custom ASCII banner logo & hero.
  - [ ] Registered and listable via `/skin`.
- **Technical Notes**:
  - Files: `/home/dolvin/.hermes/skins/ares.yaml`, `/home/dolvin/.hermes/skins/ares-pink.yaml`.

---

### Task 005: Implement Compact Stacked RGB Slim Context Gauge, '༄' Separator, & Remove Idle 'ready' Text
- **Goal**: Render context telemetry with compact width (6–8 chars max), 3-stop RGB gradient slim bar, top token fraction, right-side percentage, '༄' separator glyph, and drop idle `ready` placeholder.
- **Acceptance Criteria**:
  - [ ] Replace ` │ ` separator with ` ༄ ` formatted in subtle border/muted tone.
  - [ ] Remove `ready` string during idle state in `StatusRule`.
  - [ ] Implement `RgbSlimContextGauge` with bounded width (6–8 characters).
  - [ ] Top row renders `120k/1m` in `t.color.muted` dim text.
  - [ ] Bottom row renders thin characters (`━` filled, `┄` unfilled) with multi-stop sRGB interpolation (Green `#48bb78` → Yellow `#ecc94b` → Red `#f56565`), followed by `{pct}%`.
  - [ ] Unit tests in `statusRule.test.ts` pass.
- **Technical Notes**:
  - Files: `ui-tui/src/components/appChrome.tsx`, `ui-tui/src/__tests__/statusRule.test.ts`.

---

### Task 006: Implement Symmetrical CWD & Title Badges with Responsive 2-Line Footer Wrapping
- **Goal**: Render CWD and Title pill badges symmetrically relative to `tui_statusbar` and auto-wrap footer into 2 lines on narrow terminal widths.
- **Acceptance Criteria**:
  - [ ] Symmetrical placement in `appLayout.tsx`:
    - `tui_statusbar: bottom` → badges render above prompt box.
    - `tui_statusbar: top` → badges render below prompt box.
  - [ ] CWD and Session Title render as pill badges with `backgroundColor` and padding.
  - [ ] Responsive wrapping: when `cols < 80` or space is constrained, split status bar into 2 lines (Line 1: Model + Context Gauge + Mode; Line 2: Timers / Metadata / Badges).
- **Technical Notes**:
  - Files: `ui-tui/src/components/appLayout.tsx`, `ui-tui/src/components/appChrome.tsx`.

---

### Task 007: Rebuild Bundle & Verify End-to-End Tests
- **Goal**: Verify typescript types, build clean production bundle, and run vitest suite.
- **Acceptance Criteria**:
  - [ ] `npm run typecheck` passes with zero errors.
  - [ ] `npm run build` generates clean `dist/entry.js`.
  - [ ] Vitest unit tests pass.
- **Technical Notes**:
  - Run via `ui-tui/` directory.
