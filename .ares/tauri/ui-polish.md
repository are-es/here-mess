# UI Polish — Desktop Tauri

## Spec

Batch of UI/UX fixes and features for the Hermes desktop Tauri app. Covers visual consistency, new interaction patterns, broken commands, and missing animations.

## Decisions

- Todo card: blue/purple accent border. Clarify card: amber/orange accent border.
- Slash commands split into "immediate" (send on click) and "fill" (populate textbox).
- Forward square animation: reconstruct from TUI test spec (width=6, one filled cell sweep).
- Cards width: 100% of composer box via shared parent container.

## Tasks

### UI Fixes

- [ ] Task 001: Session sidebar group name consistency
  - **Goal**: Sidebar session groups and bottom status bar show consistent project identifiers derived from the same source.
  - **Acceptance**: [ ] Both sidebar groups and bottom bar derive from session.cwd or equivalent / [ ] No mismatched labels (e.g. "HDD" vs "/mnt/hdd/ares-workspace")
  - **Files**: `apps/tauri/src/components/sidebar.tsx`, `apps/tauri/src/components/context-bar.tsx`
  - **Notes**: Trace where sidebar group names come from first (backend session info or frontend hardcoded). Bottom bar reads from `session.cwd`.

- [ ] Task 002: Todo/Clarify card visual fixes
  - **Goal**: Todo and Clarify cards have distinct accent colors, "Other" free-text option in Clarify, and matching width aligned with composer.
  - **Acceptance**: [ ] Todo card has blue/purple border tint / [ ] Clarify card has amber/orange border tint / [ ] Clarify modal has "Other" option that reveals text input / [ ] Both cards same width as composer textarea
  - **Files**: `apps/tauri/src/components/todo-dropdown.tsx`, `apps/tauri/src/components/clarify-modal.tsx`, `apps/tauri/src/styles/settings-extra.css`, `apps/tauri/src/components/composer.tsx`
  - **Notes**: Cards rendered inside composer div — ensure parent container constrains width. "Other" only in single-question mode (not batch).

- [ ] Task 003: Auto-hide completed todo
  - **Goal**: Todo card disappears when all tasks reach completed/cancelled status. Re-appears if new todos arrive.
  - **Acceptance**: [ ] activeCount === 0 → card hidden / [ ] New todo tool.complete with active items → card re-appears / [ ] No flash or layout shift on hide
  - **Files**: `apps/tauri/src/components/todo-dropdown.tsx`
  - **Notes**: Check `todos.filter(t => t.status !== 'completed' && t.status !== 'cancelled').length`. Instant hide is fine.

- [ ] Task 004: Tool call card styling (match TUI)
  - **Goal**: Tool call rows visually match TUI card style — distinct card with border, separated from thinking blocks.
  - **Acceptance**: [ ] Tool cards have visible border + background tint / [ ] Header: icon + name + context + duration / [ ] Expanded: "review diff" label / [ ] Different bg tint from thinking blocks
  - **Files**: `apps/tauri/src/components/tool-call-row.tsx`, `apps/tauri/src/styles/transcript.css`
  - **Notes**: Tool cards = slightly blue-tinted bg, thinking blocks = neutral. Border radius consistent with other cards.

### New Features

- [ ] Task 005: Forward square thinking animation
  - **Goal**: Replace static "thinking..." text with animated forward square spinner during live reasoning.
  - **Acceptance**: [ ] `▰▱▱▱▱` → `▱▰▱▱▱` sweep animation plays during streaming / [ ] Stops when assistant text arrives / [ ] Respects prefers-reduced-motion
  - **Files**: `apps/tauri/src/components/message-bubble.tsx`, `apps/tauri/src/styles/transcript.css`
  - **Notes**: Width=6, FILLED=`▰`, EMPTY=`▱`. JS interval 120ms or CSS animation. Only show when reasoning exists AND rawText is empty.

- [ ] Task 006: Prompt Queue (/q)
  - **Goal**: User can enqueue a prompt during active agent response via `/q <text>`. Card with Send/Edit buttons appears above composer.
  - **Acceptance**: [ ] `/q <text>` captures text into queue atom / [ ] Queue card renders above composer with Send (↑) and Edit (✎) buttons / [ ] Send dispatches without interrupting agent / [ ] Edit puts text back in textarea / [ ] Auto-sends on message.complete if agent finishes / [ ] Auto-send blocked on error or cancellation
  - **Files**: `apps/tauri/src/store/sessions.ts`, `apps/tauri/src/components/composer.tsx`, `apps/tauri/src/components/queue-card.tsx` (new), `apps/tauri/src/styles/settings-extra.css`
  - **Notes**: Single-prompt queue. New /q replaces existing. Listen to `message.complete` event for auto-send. Block auto-send if `$isStreaming` goes false due to error.

### Slash Commands

- [ ] Task 007: Slash command behavior split (immediate vs fill)
  - **Goal**: Slash commands split into "immediate send" (sent instantly on click) and "fill" (populate textbox for user to add args).
  - **Acceptance**: [ ] `/compress`, `/clear`, `/restart`, `/stop` send immediately on click / [ ] `/q`, skill names fill textbox / [ ] Command registry has `immediate` flag per entry
  - **Files**: `apps/tauri/src/store/commands.ts`, `apps/tauri/src/components/slash-autocomplete.tsx`
  - **Notes**: Add `immediate?: boolean` to SlashCommandItem. SlashAutocomplete checks flag on select.

- [ ] Task 008: Fix /compress command
  - **Goal**: `/compress` command works in desktop — creates a context compression request via gateway.
  - **Acceptance**: [ ] `/compress` sends compress request to backend / [ ] Agent receives and processes compression / [ ] No error about missing reference file
  - **Files**: Check backend `compress` tool/endpoint first, then frontend command definition in `store/commands.ts`
  - **Notes**: The TUI compress works via cavpon compress reference. Desktop may need a different approach (direct RPC call or just send "/compress" as text prompt).

### Verification

- [ ] Task 009: Full verification gate
  - **Goal**: All tasks verified — typecheck, tests, build, visual check.
  - **Acceptance**: [ ] `npm run typecheck` clean / [ ] `vitest` 59/59+ / [ ] `npm run build` clean / [ ] Manual tauri:dev visual check for all UI changes
  - **Files**: N/A
  - **Notes**: Run `NODE_ENV=development npx vitest run` (production React lacks act).
