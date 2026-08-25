# Roadmap: Circular Context Meter & Consolidated Inspector Popover

## Milestones
- [ ] Task 001: Gateway prompt breakdown / size RPC support
- [ ] Task 002: Circular SVG Gauge & Consolidated Popover Inspector (`ContextBar`)
- [ ] Task 003: Compact popover styling in `composer.css`
- [ ] Task 004: Unit tests & verification

---

### Task 001: Gateway prompt breakdown / size RPC support
- **Goal**: Ensure gateway exposes unified system prompt & tool schema breakdown via `session.prompt_size` or enriched `session.context_breakdown`.
- **Acceptance Criteria**:
  - [ ] Gateway returns system prompt size, major blocks, prompt tiers, and tool schema totals
- **Technical Notes**:
  - Files: `tui_gateway/methods_session.py`, `hermes_cli/prompt_size.py`

---

### Task 002: Circular SVG Gauge & Consolidated Popover Inspector (`ContextBar`)
- **Goal**: Refactor `ContextBar` component to render circular progress gauge + popover card with consolidated totals.
- **Acceptance Criteria**:
  - [ ] Circular SVG ring dynamically computes `stroke-dashoffset` from `$usage.context_percent`
  - [ ] Label displays `100k/1M`
  - [ ] Hover/click opens compact popover showing:
    - Token header: `${used} / ${max} (${percent}%)`
    - System prompt total with inline major blocks summary
    - Tool schemas total (single consolidated line)
    - Combined fixed prefix total
    - Active conversation tokens
- **Technical Notes**:
  - Files: `apps/tauri/src/components/context-bar.tsx`, `apps/tauri/src/types/hermes.ts`

---

### Task 003: Compact popover styling in `composer.css`
- **Goal**: Style the circular context meter and popover card using project tokens.
- **Acceptance Criteria**:
  - [ ] Token-based styles, clean popover arrow, monospaced number alignments
  - [ ] Positioned cleanly above composer controls
- **Technical Notes**:
  - Files: `apps/tauri/src/styles/composer.css`

---

### Task 004: Unit tests & verification
- **Goal**: Verify test suite and TypeScript clean.
- **Acceptance Criteria**:
  - [ ] `npm test` passes in `apps/tauri`
  - [ ] Typecheck clean
