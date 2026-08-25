# Roadmap: Hermes Tauri Desktop Shell (MVP)

PRD: `.ares/tauri/prd.md`

---

## Milestones

- [ ] Task 001: Tauri 2 workspace scaffold
- [ ] Task 002: Rust backend supervisor
- [ ] Task 003: Tauri commands + bridge layer
- [ ] Task 004: Gateway connection (React)
- [ ] Task 005: Session domain store
- [ ] Task 006: Sidebar UI
- [ ] Task 007: Transcript view
- [ ] Task 008: Composer (text + submit)
- [ ] Task 009: Composer controls (model, effort, context bar, PLAN/BUILD)
- [ ] Task 010: Settings panel (desktop preferences: theme, appearance, diagnostics)
- [ ] Task 011: Logging + error handling
- [ ] Task 012: Linux packaging + verification

---

### Task 001: Tauri 2 workspace scaffold

**Goal**: A runnable Tauri 2 app with Vite + React + TypeScript that opens a
blank window, passes typecheck and clippy, and is recognized by the root npm
workspace.

**Files**:
- Create: `apps/tauri/package.json`
- Create: `apps/tauri/vite.config.ts`
- Create: `apps/tauri/tsconfig.json`
- Create: `apps/tauri/src/main.tsx`
- Create: `apps/tauri/src/App.tsx`
- Create: `apps/tauri/src/index.html`
- Create: `apps/tauri/src-tauri/Cargo.toml`
- Create: `apps/tauri/src-tauri/tauri.conf.json`
- Create: `apps/tauri/src-tauri/src/main.rs`
- Create: `apps/tauri/src-tauri/src/lib.rs`
- Modify: `package.json` (workspace already includes `apps/*`, no change needed)

**Acceptance Criteria**:
- [ ] `npm install --workspace apps/tauri` succeeds
- [ ] `npm run typecheck --workspace apps/tauri` passes
- [ ] `cargo clippy -- -D warnings` passes in `apps/tauri/src-tauri`
- [ ] `npm run dev --workspace apps/tauri` opens a window with "Hermes" title
- [ ] CSP in `tauri.conf.json` is explicit (no `unsafe-eval`, `connect-src`
      limited to `self` and `http://ipc.localhost`)

**Technical Notes**:
- Tauri 2, not 1. Reference config: `apps/bootstrap-installer/src-tauri/tauri.conf.json`
- Reference Rust deps: `apps/bootstrap-installer/src-tauri/Cargo.toml` (tokio,
  serde, tracing, tracing-appender, dirs, which, anyhow, thiserror)
- `withGlobalTauri: false` — use `@tauri-apps/api` imports, not the global
- Window: 1200x800, min 900x600, centered, decorations on, transparent off
- Vite dev server on port 5176 (5174 is Electron, 5175 is bootstrap-installer)

---

### Task 002: Rust backend supervisor

**Goal**: The Rust core can spawn `hermes serve`, detect the ready port, mint
and inject the session token, health-check both HTTP and WS legs, and tear down
the process group on exit.

**Files**:
- Create: `apps/tauri/src-tauri/src/backend/mod.rs`
- Create: `apps/tauri/src-tauri/src/backend/spawn.rs`
- Create: `apps/tauri/src-tauri/src/backend/ready.rs`
- Create: `apps/tauri/src-tauri/src/backend/shutdown.rs`
- Create: `apps/tauri/src-tauri/src/backend/types.rs`
- Modify: `apps/tauri/src-tauri/src/lib.rs` (register backend module)

**Interfaces**:
- Consumes: nothing from earlier tasks
- Produces: `BackendSupervisor` struct with:
  - `async fn start(config: BackendConfig) -> Result<BackendConnection>`
  - `async fn stop(&self) -> Result<()>`
  - `fn status(&self) -> BackendStatus`
  - `fn logs(&self, limit: usize) -> Vec<String>`
  - `fn on_progress(&self, cb: impl Fn(BackendProgress) + Send + 'static) -> CancelToken`

**Acceptance Criteria**:
- [ ] `cargo test` passes for ready-line parsing (both `HERMES_BACKEND_READY`
      and `HERMES_DASHBOARD_READY` variants, per `backend-ready.ts:6`)
- [ ] `cargo test` passes for ready-file JSON parsing
      (`{"port": N}`, per `hermes_cli/web_server.py:18694`)
- [ ] `cargo test` passes for token minting (32 bytes base64url)
- [ ] Spawn uses `Command::new("hermes")` with args
      `["serve", "--host", "127.0.0.1", "--port", "0"]`
- [ ] Env vars injected: `HERMES_HOME`, `TERMINAL_CWD`, `HERMES_DESKTOP=1`,
      `HERMES_DASHBOARD_SESSION_TOKEN`
- [ ] Child is spawned in its own process group (`setsid` / `CREATE_NEW_PROCESS_GROUP`)
- [ ] Shutdown sends `SIGTERM` to `-pgid`, falls back to direct child on failure
      (mirrors `backend-child.ts:58-83`)
- [ ] Cold-start timeout: 90s default, 45s floor
      (mirrors `backend-ready.ts:16-19`)
- [ ] Progress events emitted for phases: `resolve`, `spawn`, `wait_ready`,
      `health_check`, `ready`, `failed`
- [ ] Latched failure: once `start()` fails, subsequent calls return the same
      error until `retry()` is called (mirrors `main.ts:10371`)

**Technical Notes**:
- HTTP readiness: `GET /api/status` with the token as Bearer, timeout 5s
- WS readiness: open `ws://127.0.0.1:<port>/api/ws?token=<token>`, wait for
  first frame or open event, timeout 10s. A passing HTTP + failing WS is a
  failure (mirrors `main.ts:10234-10240`)
- `HERMES_HOME` resolution: `dirs::home_dir()` / `.hermes` (same as
  `hermes_constants.get_hermes_home()`). If `HERMES_HOME` env is set, use it.
- Binary resolution: `which::which("hermes")`, then check
  `~/.local/bin/hermes`. If not found, return a named `BinaryNotFound` error
  with the searched paths.
- Log the spawn command line, resolved `HERMES_HOME`, chosen port, and every
  phase transition. Never log the session token.

---

### Task 003: Tauri commands + bridge layer

**Goal**: The renderer communicates with the Rust backend through a typed
`DesktopBridge` interface. Tauri `invoke` calls are confined to one bridge
module. Adding a native capability later = one Rust command + one bridge method.

**Files**:
- Create: `apps/tauri/src-tauri/src/commands.rs`
- Create: `apps/tauri/src/bridge/types.ts`
- Create: `apps/tauri/src/bridge/tauri-bridge.ts`
- Create: `apps/tauri/src/bridge/index.ts`
- Modify: `apps/tauri/src-tauri/src/lib.rs` (register commands)
- Modify: `apps/tauri/src/App.tsx` (inject bridge via context)

**Interfaces**:
- Consumes: `BackendSupervisor` from Task 002
- Produces:
  - Rust commands: `backend_connect`, `backend_status`, `backend_logs`,
    `backend_retry`
  - TS interface `DesktopBridge` (see PRD §4.2)
  - React context `BridgeProvider` + hook `useBridge()`

**Acceptance Criteria**:
- [ ] `cargo clippy` passes
- [ ] `npm run typecheck` passes
- [ ] `window.__TAURI__` / `@tauri-apps/api` imports appear ONLY in
      `apps/tauri/src/bridge/` (enforced by a test or grep assertion)
- [ ] `backend_connect` returns a `BackendConnection` with `baseUrl`, `wsUrl`,
      `token`, `port`
- [ ] `backend_status` returns `idle | starting | ready | failed` with optional
      error and phase
- [ ] `backend_logs` returns the last N log lines
- [ ] Progress events are forwarded from Rust to the renderer via Tauri events
      (`app.emit` / `listen`)

**Technical Notes**:
- Tauri 2 commands use `#[tauri::command]` with `async fn` and `State<BackendSupervisor>`
- TS bridge uses `import { invoke } from '@tauri-apps/api/core'`
- Progress events use `import { listen } from '@tauri-apps/api/event'`
- The bridge module is the ONLY place that imports from `@tauri-apps/api`

---

### Task 004: Gateway connection (React)

**Goal**: After the backend is ready, the renderer opens a WebSocket to the
gateway using `@hermes/shared`'s `JsonRpcGatewayClient`, tracks connection
state, and shows appropriate boot/reconnect/error screens.

**Files**:
- Create: `apps/tauri/src/store/gateway.ts`
- Create: `apps/tauri/src/store/boot.ts`
- Create: `apps/tauri/src/components/boot-screen.tsx`
- Create: `apps/tauri/src/components/reconnect-banner.tsx`
- Modify: `apps/tauri/src/App.tsx` (wire boot flow)

**Interfaces**:
- Consumes: `DesktopBridge` from Task 003, `JsonRpcGatewayClient` from
  `apps/shared/src/json-rpc-gateway.ts`
- Produces:
  - `$gateway: WritableAtom<JsonRpcGatewayClient | null>`
  - `$gatewayState: ReadableAtom<'idle' | 'connecting' | 'open' | 'closed' | 'error'>`
  - `connectGateway(baseUrl, token): Promise<void>`
  - `requestGateway<T>(method, params): Promise<T>`

**Acceptance Criteria**:
- [ ] After `backend_connect` returns, the app opens a WS to
      `ws://127.0.0.1:<port>/api/ws?token=<token>`
- [ ] `gatewayState` transitions: `idle → connecting → open`
- [ ] On WS close, `gatewayState` goes to `closed` and a reconnect banner shows
- [ ] On WS error, `gatewayState` goes to `error` and the boot screen shows the
      error with a Retry button
- [ ] `requestGateway` rejects with a clear error when the gateway is not open
- [ ] `gateway.ready` event is consumed (no action needed yet, but the handler
      exists)

**Technical Notes**:
- Use `JsonRpcGatewayClient` from `@hermes/shared` directly — do NOT write a
  second WS client
- `connectTimeoutMs: 15_000` (matches `DEFAULT_CONNECT_TIMEOUT_MS` in
  `apps/shared/src/json-rpc-gateway.ts:93`)
- `requestTimeoutMs: 120_000` (matches `:89`)
- State atoms use nanostores (same as Electron renderer)
- Boot screen: progress text from Rust, then "Connecting to Hermes..." during
  WS handshake, then transition to the main shell

---

### Task 005: Session domain store

**Goal**: The renderer can list sessions grouped by project, create a session,
resume a session, and track the active session's runtime info and usage.

**Files**:
- Create: `apps/tauri/src/store/sessions.ts`
- Create: `apps/tauri/src/store/projects.ts`
- Create: `apps/tauri/src/types/hermes.ts` (subset of
  `apps/desktop/src/types/hermes.ts` — only the types the MVP uses)

**Interfaces**:
- Consumes: `requestGateway` from Task 004
- Produces:
  - `$sessions: WritableAtom<SessionInfo[]>`
  - `$projectTree: WritableAtom<ProjectTreeNode[]>`
  - `$activeSessionId: WritableAtom<string | null>`
  - `$activeSessionInfo: ReadableAtom<SessionRuntimeInfo | null>`
  - `$usage: ReadableAtom<UsageStats | null>`
  - `refreshProjectTree(): Promise<void>`
  - `createSession(cwd?: string): Promise<string>` (returns stored_session_id)
  - `resumeSession(storedId: string): Promise<void>`
  - Event handlers for `session.info`, `session.usage`, `message.start`,
    `message.delta`, `message.complete`, `tool.start`, `tool.complete`, `error`

**Acceptance Criteria**:
- [ ] `refreshProjectTree()` calls `projects.tree` and populates `$projectTree`
- [ ] `createSession()` calls `session.create` with `source: "tauri"` and
      returns the `stored_session_id`
- [ ] `resumeSession()` calls `session.resume` and sets `$activeSessionId`
- [ ] `session.info` events update `$activeSessionInfo` (model, effort,
      interaction_mode, running)
- [ ] `session.usage` events update `$usage` (context_used, context_max,
      context_percent)
- [ ] `message.delta` events append to the active session's transcript buffer
- [ ] `message.complete` events finalize the assistant turn

**Technical Notes**:
- `SessionInfo` subset: `id`, `title`, `cwd`, `last_active`, `started_at`,
  `message_count`, `preview`, `source` — copy the interface shape from
  `apps/desktop/src/types/hermes.ts:477` but only these fields
- `ProjectTreeNode` shape mirrors `SidebarProjectTree` from
  `apps/desktop/src/app/chat/sidebar/projects/workspace-groups.ts:45`:
  `id`, `label`, `path`, `repos[].{id, label, path, groups[].{id, label, sessions}}`
- `session.create` params from `tui_gateway/methods_session.py:14`: `cols: 96`,
  `source: "tauri"`, optional `cwd`, `model`, `provider`, `reasoning_effort`, `fast`
- `session.resume` params from `:358`: `session_id`, `cols: 96`, `source: "tauri"`
- `prompt.submit` params from `tui_gateway/methods_prompt.py:268`: `session_id`, `text`
- `config.set` for model/effort/mode from `tui_gateway/server.py:11976`

---

### Task 006: Sidebar UI

**Goal**: A sidebar showing sessions grouped by project path, with collapsible
groups, active row highlighting, relative timestamps, and Settings pinned at the
bottom.

**Files**:
- Create: `apps/tauri/src/components/sidebar.tsx`
- Create: `apps/tauri/src/components/sidebar-group.tsx`
- Create: `apps/tauri/src/components/sidebar-row.tsx`
- Create: `apps/tauri/src/styles/sidebar.css`

**Interfaces**:
- Consumes: `$projectTree`, `$sessions`, `$activeSessionId`, `createSession`,
  `resumeSession` from Task 005
- Produces: `<Sidebar />` component

**Acceptance Criteria**:
- [ ] `+ New Session` button at top creates a session and selects it
- [ ] Projects render as collapsible groups with a chevron
- [ ] Sessions within a group show title (or "Untitled") + relative time
      (e.g. "3min", "2h", "yesterday")
- [ ] Active session row is visually distinct
- [ ] Clicking a session row resumes it
- [ ] `Home` bucket (no project) renders at the bottom of the project list
- [ ] Settings entry is pinned to the sidebar footer
- [ ] Collapse state persists in `localStorage`
- [ ] Empty project group shows a zero count, not hidden

**Technical Notes**:
- Relative time: `Intl.RelativeTimeFormat` or a simple helper (no library)
- Collapse state key: `hermes.tauri.sidebar.collapsed.<projectId>`
- Width: 260px fixed, resizable deferred to post-MVP
- No search, no sort, no filters in MVP
- Follow `apps/desktop/DESIGN.md` token discipline: no raw colors, no
  card-in-card, no native `title=` on buttons

---

### Task 007: Transcript view

**Goal**: A scrollable transcript showing user and assistant turns, with live
streaming of assistant output, collapsed tool calls, and a sticky-to-bottom
scroll behavior.

**Files**:
- Create: `apps/tauri/src/components/transcript.tsx`
- Create: `apps/tauri/src/components/message-bubble.tsx`
- Create: `apps/tauri/src/components/tool-call-row.tsx`
- Create: `apps/tauri/src/styles/transcript.css`

**Interfaces**:
- Consumes: active session messages from `$messages` (derived from the
  transcript buffer in Task 005), `$activeSessionId`
- Produces: `<Transcript />` component

**Acceptance Criteria**:
- [ ] User messages render right-aligned or left-aligned with distinct styling
- [ ] Assistant messages render with markdown: code fences (with copy button),
      lists, tables, inline code
- [ ] Live streaming appends tokens to the current assistant bubble without
      re-rendering the entire transcript
- [ ] Tool calls render as one collapsed row per call (name + brief summary),
      expandable on click
- [ ] Reasoning content, if present, renders as a collapsed section
- [ ] Scroll sticks to bottom during streaming; scrolls up when the user
      scrolls up; a "scroll to bottom" button appears when not at bottom
- [ ] Empty transcript shows a centered prompt: "Start a conversation"

**Technical Notes**:
- Markdown rendering: use `react-markdown` + `remark-gfm` (same approach as
  Electron renderer, no custom parser)
- Code block syntax highlighting: `shiki` (already in Electron deps)
- Streaming: the `message.delta` handler appends to a ref-backed buffer;
  React state updates are batched per animation frame to avoid layout thrash
- Tool call collapse: default collapsed, expandable, shows tool name + first
  80 chars of args (matching the backend's `context` field convention)

---

### Task 008: Composer (text + submit)

**Goal**: A multiline text input that submits turns via `prompt.submit`, supports
cancel, and disables appropriately during backend states.

**Files**:
- Create: `apps/tauri/src/components/composer.tsx`
- Create: `apps/tauri/src/styles/composer.css`

**Interfaces**:
- Consumes: `requestGateway` from Task 004, `$activeSessionId` from Task 005,
  `$gatewayState` from Task 004
- Produces: `<Composer />` component

**Acceptance Criteria**:
- [ ] Multiline textarea, auto-growing up to 200px
- [ ] `Enter` submits, `Shift+Enter` inserts newline
- [ ] Submit calls `prompt.submit` with `{ session_id, text }`
      (params from `tui_gateway/methods_prompt.py:268`)
- [ ] While a turn runs (`$activeSessionInfo.running === true`), send button
      becomes stop; stop calls `session.interrupt`
- [ ] Composer is disabled when gateway is not open, with a reason shown
- [ ] `Esc` cancels an in-flight turn
- [ ] Submit clears the textarea

**Technical Notes**:
- No file attachments, no voice, no slash commands in MVP
- Textarea uses `contentEditable` or a plain `<textarea>` — plain textarea
  is simpler and sufficient for MVP
- Submit timeout: use `requestGateway` with the default 120s timeout

---

### Task 009: Composer controls (model, effort, context bar, PLAN/BUILD)

**Goal**: The composer row includes a model dropdown, effort dropdown,
context-window progress bar, and PLAN/BUILD mode dropdown.

**Files**:
- Create: `apps/tauri/src/components/composer-controls.tsx`
- Create: `apps/tauri/src/components/model-dropdown.tsx`
- Create: `apps/tauri/src/components/context-bar.tsx`
- Create: `apps/tauri/src/components/mode-dropdown.tsx`

**Interfaces**:
- Consumes: `requestGateway` from Task 004, `$activeSessionInfo` and `$usage`
  from Task 005
- Produces: `<ComposerControls />` component

**Acceptance Criteria**:
- [ ] Model dropdown calls `model.options` to populate, then `config.set` with
      `key: "model"` and `value: "<provider>/<model>"` on selection
      (params from `tui_gateway/server.py:11981`)
- [ ] Effort dropdown offers at least: `low`, `medium`, `high`, `ultra`;
      calls `config.set` with `key: "reasoning"` and `value: "<level>"`
      (params from `:12380`)
- [ ] Context bar renders `context_used / context_max` with a visual fill;
      unfilled portion is visibly empty (not a connected solid rule);
      percentage shown as text
      (data from `UsageStats` at `apps/desktop/src/types/hermes.ts:705`)
- [ ] PLAN/BUILD dropdown reads current mode from `session.info`'s
      `interaction_mode` field; on change calls `config.set` with
      `key: "interaction_mode"`, `value: "plan" | "build" | "toggle"`
      (params from `tui_gateway/server.py:12351`)
- [ ] All controls disable when gateway is not open
- [ ] Model pill shows current model name (truncated if long) with a chevron

**Technical Notes**:
- `model.options` response shape: `ModelOptionsResponse` at
  `apps/desktop/src/types/hermes.ts:438` — `providers[]` with `models[]`
- `session.info` carries `interaction_mode` as a string ("plan" or "build")
- Context bar: `█` for filled, `░` for empty (matching the Ink status bar
  convention at `apps/desktop/src/lib/statusbar.tsx:41`, but with visible
  empty glyphs instead of the connected-rule bug)
- Effort values verified from `tui_gateway/server.py:12463`:
  `parse_reasoning_effort()` accepts `low`, `medium`, `high`, `ultra`

---

### Task 010: Settings panel (desktop preferences)

**Goal**: A desktop-app settings overlay with General (theme, appearance) and
Diagnostics (backend status, log tail) sections. This panel configures the app
itself — it never writes Hermes backend config.

**Files**:
- Create: `apps/tauri/src/components/settings.tsx`
- Create: `apps/tauri/src/components/settings-general.tsx`
- Create: `apps/tauri/src/components/settings-diagnostics.tsx`
- Create: `apps/tauri/src/store/preferences.ts`
- Create: `apps/tauri/src/styles/tokens.css`
- Create: `apps/tauri/src/styles/settings.css`

**Interfaces**:
- Consumes: `DesktopBridge` from Task 003 (for `backendStatus`, `backendLogs`,
  `retryBackend`)
- Produces:
  - `<Settings />` overlay component
  - `$preferences: WritableAtom<Preferences>` where
    `Preferences = { theme: 'dark' | 'light' | 'system'; fontSize: 'sm' | 'md' | 'lg'; density: 'compact' | 'comfortable'; reduceMotion: boolean }`
  - `setPreference<K extends keyof Preferences>(key: K, value: Preferences[K]): void`

**Acceptance Criteria**:

General section:
- [ ] Theme selector (`dark` / `light` / `system`) applies immediately with no
      reload; `system` follows `prefers-color-scheme`
- [ ] Font size selector (`sm` / `md` / `lg`) changes transcript and composer
      text size
- [ ] Density selector (`compact` / `comfortable`) changes sidebar row height
      and transcript spacing
- [ ] Reduce-motion toggle disables the transcript fade transition
- [ ] Every preference persists in `localStorage` and survives an app restart
- [ ] Preferences apply via CSS custom properties on `:root` — no component
      re-mount, no inline styles scattered through features

Diagnostics section:
- [ ] Shows backend status (idle / starting / ready / failed) with the current
      phase when starting
- [ ] Shows the last 100 log lines in a scrollable monospace area
- [ ] Shows `HERMES_HOME` path and the resolved `hermes` binary path
      (read-only text, not editable fields)
- [ ] Retry button calls `bridge.retryBackend()`

Shell:
- [ ] Settings opens from the sidebar footer; closes with `Esc`, a close button,
      or a backdrop click
- [ ] Section navigation is a left rail inside the overlay (General,
      Diagnostics)
- [ ] No model defaults, no API keys, no profile switching, no `config.set`
      calls anywhere in this panel

**Technical Notes**:
- Route overlay, not a full page (per `apps/desktop/DESIGN.md:53`)
- Theme implementation: `tokens.css` declares every color/space/radius as a CSS
  custom property under `[data-theme="dark"]` and `[data-theme="light"]`; the
  store writes `document.documentElement.dataset.theme`. No component may
  hardcode a color — this is what makes a third theme a CSS-only change later.
- `system` theme subscribes to
  `window.matchMedia('(prefers-color-scheme: dark)')` and updates live
- Preference storage key: `hermes.tauri.preferences` (one JSON blob)
- Log view uses the `LogView` visual convention: no background, hairline
  border, tight padding, small mono
- Diagnostics is read-only in MVP. The binary-path override named in PRD §9 is
  a later task, not this one.

---

### Task 011: Logging + error handling

**Goal**: Structured logging on both sides, one renderer error boundary, and
boot failure recovery with retry.

**Files**:
- Create: `apps/tauri/src/components/error-boundary.tsx`
- Modify: `apps/tauri/src-tauri/src/backend/spawn.rs` (ensure all paths log)
- Modify: `apps/tauri/src/App.tsx` (wrap in error boundary)

**Interfaces**:
- Consumes: `DesktopBridge` from Task 003 (for forwarding renderer errors to
  Rust log)
- Produces: `<ErrorBoundary />` component, renderer-to-Rust error forwarding

**Acceptance Criteria**:
- [ ] Rust logs to `<HERMES_HOME>/logs/tauri-desktop.log` via tracing-appender
- [ ] Rust logs: spawn command, HERMES_HOME, port, phase transitions, WS state
      changes, RPC failures, child exit code/signal
- [ ] Session token is never logged
- [ ] Renderer error boundary catches uncaught React errors, shows a recovery
      screen with the error message and a Reload button
- [ ] Renderer errors are forwarded to the Rust log via a bridge method
- [ ] Boot failure screen shows the error, the log tail, and a Retry button
      that calls `bridge.retryBackend()`

**Technical Notes**:
- Tracing subscriber: `tracing_subscriber::fmt` with `env_filter` for
  `RUST_LOG` override, file appender for persistent logs
- Error boundary: standard React `componentDidCatch` pattern
- Renderer-to-Rust forwarding: a `log_renderer_error` Tauri command that
  writes to the same tracing subscriber

---

### Task 012: Linux packaging + verification

**Goal**: The app builds as AppImage and deb, launches from the packaged binary,
starts the backend, and completes one real turn.

**Files**:
- Modify: `apps/tauri/src-tauri/tauri.conf.json` (bundle targets)
- Create: `apps/tauri/src-tauri/icons/` (app icons)
- Modify: `apps/tauri/package.json` (build/dist scripts)

**Acceptance Criteria**:
- [ ] `npm run build --workspace apps/tauri` produces a release build
- [ ] `npm run dist --workspace apps/tauri` produces AppImage and deb in
      `apps/tauri/src-tauri/target/release/bundle/`
- [ ] AppImage launches, backend starts, sidebar loads, one turn streams
- [ ] deb installs and runs on a clean Ubuntu 22.04+ system
- [ ] Process group is killed when the app exits (verified via `ps aux`)
- [ ] No orphaned `hermes serve` processes after app exit
- [ ] Log file is written to `<HERMES_HOME>/logs/tauri-desktop.log`

**Technical Notes**:
- Bundle targets: `["appimage", "deb"]` in `tauri.conf.json`
- App icon: at least `32x32.png`, `128x128.png`, `128x128@2x.png`, `icon.png`
  (reuse from `apps/desktop/assets/` if available)
- Build scripts: `dev` (vite dev + tauri dev), `build` (vite build + tauri build),
  `dist` (tauri build --bundles appimage,deb)
- Verification is manual for MVP: no E2E automation in this phase
