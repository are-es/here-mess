# PRD: Slash Commands & Autocomplete in Desktop Composer

## 1. Overview
Bring full CLI/TUI slash command parity to the Tauri desktop composer (`/skill <name>`, `/compress`, `/clear`, `/model`, `/plan`, `/build`, `/title`, `/usage`, etc.) with a floating autocomplete palette when typing `/`.

## 2. Requirements

### 2.1 Autocomplete Menu (UI)
- Triggered when composer text starts with `/`.
- Filters available commands and skills in real-time as the user types.
- Keyboard navigation:
  - `ArrowUp` / `ArrowDown`: navigate command list
  - `Tab` / `Enter`: insert command or execute
  - `Escape`: dismiss menu
- List items display:
  - Command trigger (e.g. `/compress`, `/skill`, `/clear`, `/plan`, `/build`, `/model`)
  - Command description / category badge

### 2.2 Command Catalog & Skills Discovery
- Fetch command catalog from gateway via `commands.catalog` RPC on boot/focus.
- Include all registered skills from gateway as autocomplete targets (e.g. `/cavpon`, `/impeccable`, `/antislop-ui`, `/grounded-citations`, etc.).

### 2.3 Command Execution Flow
- **Local Shell Actions**:
  - `/clear`: clears local transcript view and resets history on gateway
  - `/plan`: switches mode to PLAN
  - `/build`: switches mode to BUILD
  - `/title <new_title>`: renames active session
- **Gateway Slash Execution**:
  - `/compress`: triggers context compression pipeline
  - `/skill <name>` or `/<skill-name>`: submits skill load directive to agent turn
  - Other slash commands: dispatched via gateway `slash.exec` / `prompt.submit`

## 3. Non-Functional Constraints
- Responsive floating popover above composer with clean token styling.
- Zero layout jitter when typing.
