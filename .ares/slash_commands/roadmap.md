# Roadmap: Slash Commands & Autocomplete

## Milestones
- [ ] Task 001: Slash commands store & `commands.catalog` fetcher
- [ ] Task 002: Autocomplete popover component for `Composer`
- [ ] Task 003: Slash command execution & dispatcher
- [ ] Task 004: Styling & keyboard navigation tests

---

### Task 001: Slash commands store & `commands.catalog` fetcher
- **Goal**: Fetch registered commands and skills from gateway `commands.catalog` and store in `$commandsCatalog` atom.
- **Acceptance Criteria**:
  - [ ] `$commandsCatalog` holds built-in commands and user/system skills
  - [ ] Auto-refreshes when gateway connects
- **Technical Notes**:
  - Files: `apps/tauri/src/store/commands.ts`

---

### Task 002: Autocomplete popover component for `Composer`
- **Goal**: Build `SlashAutocomplete` overlay in `Composer` that triggers on `/` prefix.
- **Acceptance Criteria**:
  - [ ] Detects `/` at start of input and filters candidates
  - [ ] Arrow up/down moves selection index
  - [ ] Tab or Enter selects command into textarea
  - [ ] Escape dismisses
- **Technical Notes**:
  - Files: `apps/tauri/src/components/slash-autocomplete.tsx`, `apps/tauri/src/components/composer.tsx`

---

### Task 003: Slash command execution & dispatcher
- **Goal**: Handle slash command submit: `/clear`, `/compress`, `/plan`, `/build`, `/title`, `/skill <name>`, etc.
- **Acceptance Criteria**:
  - [ ] `/clear` clears transcript messages
  - [ ] `/plan` / `/build` switches interaction mode
  - [ ] `/title <title>` renames active session
  - [ ] `/compress` and skill commands forward to gateway appropriately
- **Technical Notes**:
  - Files: `apps/tauri/src/store/sessions.ts`

---

### Task 004: Styling & keyboard navigation tests
- **Goal**: Add token-only styling in `composer.css` and comprehensive tests.
- **Acceptance Criteria**:
  - [ ] Tests verify autocomplete filtering and keybind navigation
  - [ ] `npm test` passes 100%
- **Technical Notes**:
  - Files: `apps/tauri/src/styles/composer.css`, `apps/tauri/src/components/composer.test.tsx`
