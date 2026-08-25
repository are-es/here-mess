# Notes — Desktop Tauri

## [2026-08-25 08:18] Session Sidebar Group Name Inconsistency [specced → ui-polish.md Task 001]
**Want**: Session sidebar groups show short labels (HDD, PAAP, HOME) but the bottom status bar shows full path (/mnt/hdd/ares-workspace). These should be consistent — either both show short names or both show paths, or the sidebar groups should derive from the actual project/cwd path rather than arbitrary labels.
**Rationale**: Visual inconsistency confuses which project/context the user is in. Sidebar says "HDD" but bottom bar says a different path.
**Constraints**: Sidebar group names come from session metadata. Bottom bar reads from session.cwd or gateway state. Fix should derive both from the same source.
**Open**: Where do current sidebar group names come from — hardcoded in frontend or from backend session info? Need to trace the data source before fixing.
**Status**: captured

## [2026-08-25 08:20] Prompt Queue (/q) [specced → ui-polish.md Task 006]
**Want**: During active AI response, user types `/q <prompt>` to enqueue a prompt. Queued prompt appears above the composer textarea as a card with Send (up arrow) and Edit (pencil) buttons. Send button dispatches the prompt immediately without interrupting the running agent. Edit button puts the prompt text back into the composer textarea for modification. If user takes no action, the queued prompt auto-sends when the agent finishes its current response (on message.complete event). Only one prompt can be queued at a time; new /q replaces existing queue.
**Rationale**: CLI supports `/q` for queuing prompts during streaming. Desktop currently forces user to wait until agent finishes before sending next prompt. This creates dead time between turns.
**Constraints**: Must not interrupt running agent. Must work with streaming state. Queue card UI should be compact and non-intrusive (above composer, below context bar). Auto-send must not trigger on agent error or user cancellation — only on successful completion.
**Open**: Should /q work from slash autocomplete or only typed manually? Should queue persist across session switch? Should there be a max queue length or just single-prompt?
**Status**: captured

## [2026-08-25 08:22] Forward Square Thinking Animation [specced → ui-polish.md Task 005]
**Want**: Replace the static "Thought process (thinking...)" text in desktop message-bubble with a forward square animation identical to TUI: `▰▱▱▱▱` → `▱▰▱▱▱` → ... → `▱▱▱▱▰` → loop. Filled block (`▰`) sweeps forward across empty cells (`▱`), one cell per frame, fixed width (e.g. 6 cells), no bounce.
**Rationale**: Current desktop shows static text "thinking..." which gives no visual feedback that reasoning is actively streaming. TUI forward-square spinner provides clear motion feedback without being distracting.
**Constraints**: Must animate only while `isLiveReasoning` is true (reasoning streaming, no assistant text yet). Must stop when assistant text arrives. CSS-only or lightweight JS interval (no heavy animation libs). Must respect `prefers-reduced-motion`. Same frame spec as TUI: `FORWARD_SQUARE_WIDTH=6`, one `▰` per frame, sweep forward.
**Open**: TUI thinking.tsx file is 0 bytes (likely wiped by crash). Need to reconstruct frames from test spec: `FILLED='▰'`, `EMPTY='▱'`, width=6, frames = each position 0..5.
**Status**: captured

## [2026-08-25 08:30] Todo/Clarify Card Visual Fixes [specced → ui-polish.md Task 002]
**Want**: (1) Todo card must not blend with background — needs distinct visual treatment (border, background tint, or elevation). (2) Todo card and Clarify card must use different accent colors to be visually distinguishable. (3) Clarify modal must support free-text "Other" input option in addition to predefined choices. (4) Todo and Clarify cards must have equal width, aligned flush with the composer textarea — no floating or orphaned sizing.
**Rationale**: From screenshot: TODO card at bottom is nearly invisible against the same-toned background. Clarify and Todo use identical styling making them indistinguishable. Clarify only offers predefined choices with no way to type a custom answer. Card widths don't match the text box, creating visual misalignment.
**Constraints**: Todo card gets a distinct color (e.g. muted blue/purple border). Clarify card gets a different accent (e.g. amber/orange). "Other" option adds a text input below choices when selected. Cards must use `width: 100%` or match composer box width exactly. All changes in `settings-extra.css` (clarify, todo styles) and component files.
**Open**: What accent colors for each? Should "Other" be a persistent option or only when `clarify.questions` is empty (single-question mode)?
**Status**: captured

## [2026-08-25 08:31] Auto-hide Completed Todo [specced → ui-polish.md Task 003]
**Want**: Todo card must automatically hide/disappear when all tasks reach completed or cancelled status. No need for manual dismissal — if 0 active tasks remain, card vanishes from the UI.
**Rationale**: Leaving a fully-completed todo card visible is visual noise. User doesn't need to see it after everything is done.
**Constraints**: Check active count (status !== 'completed' && status !== 'cancelled'). If activeCount === 0, hide entire card. Should re-appear if new todos arrive.
**Open**: Should there be a brief delay/fade before hiding, or instant disappear?
**Status**: captured

## [2026-08-25 08:36] Tool Call Card Styling (match TUI) [specced → ui-polish.md Task 004]
**Want**: Tool call rows in desktop transcript must look like TUI tool cards — distinct card with border/background, visually separated from thinking/reasoning blocks. Header: icon + tool name + context path + duration, collapsed by default. Expanded body: review diff section with unified diff display. Must NOT merge visually with thinking collapse — tool cards and thinking blocks are separate entities with different styling.
**Rationale**: Currently desktop tool rows blend into thinking blocks (screenshot shows them merging). TUI has clean card boundaries. Desktop should match that clarity.
**Constraints**: Use existing `.tool-call` CSS class with added border, background tint, rounded corners. Header layout: chevron + icon badge + tool name (mono) + context path (mono, muted) + duration (right-aligned). Expanded: "review diff" label + unified diff with +/- line highlighting. Different background tint from thinking blocks (e.g. tool cards = slightly blue-tinted bg, thinking = neutral).
**Open**: Should diff lines use syntax coloring (green for add, red for remove) or monochrome with +/- prefix only?
**Status**: captured

## [2026-08-25 08:38] Slash Command Behavior + /compress Fix [specced → ui-polish.md Task 007+008]
**Want**: (1) Fix /compress command — currently broken because compress reference file missing from cavpon skill. (2) Slash command click behavior must be split into two modes: "immediate send" commands (compress, clear history, etc.) are sent instantly on click without populating textbox. "Fill" commands (slash skill names, /q, etc.) populate the textbox for user to add arguments before sending.
**Rationale**: /compress click triggers agent to search for non-existent cavpon compress reference, wasting tokens and time. All slash commands currently put text in textbox even when no additional input is needed — unnecessary extra step for simple commands.
**Constraints**: Immediate-send commands: `/compress`, `/clear`, `/restart`, `/stop`. Fill commands: `/q`, skill names, any command that takes arguments. Command registry in `store/commands.ts` needs an `immediate: boolean` flag per command. Slash autocomplete component checks flag on selection — immediate = call prompt submit directly, fill = set textarea value.
**Open**: Where does the compress reference file live? Need to check cavpon skill references/ directory.
**Status**: captured
