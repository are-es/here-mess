# PRD: Hermes Tauri Desktop Shell (MVP)

Status: draft for approval
Owner: ARES
Target: Linux first (macOS / Windows deferred)
Location: `apps/tauri/` (new npm workspace member, side by side with `apps/desktop/`)

---

## 1. Problem

`apps/desktop/` is a mature but very heavy Electron application:

- `apps/desktop/electron/main.ts` is ~15,000 lines and owns backend supervision,
  multi-connection registry, SSH remotes, PTY terminals, self-update, HUD and
  overlay windows, quick entry, native OAuth, plugin installs, deep links.
- `apps/desktop/electron/preload.ts` exposes a `window.hermesDesktop` bridge with
  hundreds of capability methods; `apps/desktop/src/global.d.ts` types it across
  ~1,300 lines.
- 73 renderer modules reach `window.hermesDesktop` directly.

A straight Electron-to-Tauri port would therefore require reimplementing that
entire capability surface in Rust before anything runs. That is not a migration,
it is a rewrite with no intermediate proof point.

## 2. Goal

Ship a **small, honest, runnable** Tauri desktop shell for Hermes on Linux that
proves the stack end to end, and whose architecture makes adding the next
capability a local change instead of a refactor.

The Electron app is the **behavioural reference**, not the code to copy.

### In scope (MVP)

1. Tauri 2 application that starts a local Hermes backend by itself.
2. Session sidebar grouped by project path, with a Settings entry pinned bottom.
3. Chat transcript with live streaming.
4. Composer with: model dropdown, reasoning-effort control, context-window
   progress bar, and a PLAN / BUILD mode dropdown on the right.
5. Structured logging on both the Rust and renderer side.
6. Linux packaging (AppImage + deb) and a manual first-run verification pass.
7. Desktop-only Settings: theme switch, appearance preferences, and a
   diagnostics section. No Hermes backend configuration.

### Explicitly out of scope (MVP)

Remote / SSH / cloud connections, backend pooling per profile, multi-window,
HUD and pet overlays, quick entry, embedded terminal (PTY), file tree, preview
pane, review pane, self-update, plugin system, voice, deep links, i18n, native
OAuth, notifications, backend configuration UI (models, keys, profiles).

Theming is IN scope but narrow: a token-driven theme layer with a working
switcher. Only the desktop app's own appearance — nothing that writes to the
Hermes backend config.

Each of these must remain *addable* without reshaping the shell. None may be
stubbed with fake UI.

## 3. Non-goals

- Not a replacement for `apps/desktop/` in this phase. Both ship side by side.
- Not a feature-parity effort. Parity is a later, separately planned decision.
- No reimplementation of agent behaviour in Rust or React. The backend owns it.

---

## 4. Architecture

Three parties, mirroring the seam contract already documented in
`apps/desktop/AGENTS.md`:

```
┌──────────────────────── Tauri app (apps/tauri) ───────────────────────┐
│                                                                       │
│  Rust core (src-tauri)              Renderer (React + Vite)           │
│  ─────────────────────              ─────────────────────────         │
│  - process lifecycle                - navigation & presentation       │
│  - local backend supervision        - session/chat state              │
│  - ready-port detection             - composer & controls             │
│  - connection descriptor            - talks JSON-RPC over WS          │
│  - file logging                     - never touches Tauri directly    │
│                                       (goes through DesktopBridge)    │
└───────────────────────────────┬───────────────────────────────────────┘
                                │ HTTP + WebSocket (127.0.0.1)
                                ▼
                    hermes serve  (Python backend)
                    owns sessions, tools, model calls, streaming
```

### 4.1 Backend startup contract (copied behaviour, minimal implementation)

Verified from the Electron implementation:

| Concern | Electron reference | Tauri MVP decision |
| --- | --- | --- |
| Spawn command | `apps/desktop/electron/main.ts:10459` — `hermes [--profile X] serve --host 127.0.0.1 --port 0` | Same, `--profile` only when configured |
| Port discovery | stdout regex `^HERMES_(?:BACKEND\|DASHBOARD)_READY port=(\d+)` — `apps/desktop/electron/backend-ready.ts:6` | Same regex, stdout only. Ready-file path (`HERMES_DESKTOP_READY_FILE`, `hermel_cli/web_server.py:18678`) is a Windows concern — skipped |
| Auth token | main process mints 32 random bytes base64url and injects `HERMES_DASHBOARD_SESSION_TOKEN` (`main.ts:10457`); backend honours it at `hermes_cli/web_server.py:499` | Same: Rust mints the token, injects the env var |
| Env pinning | `HERMES_HOME`, `TERMINAL_CWD`, `HERMES_DESKTOP=1` (`main.ts:10516-10538`) | Same three, plus nothing else |
| HTTP base | `http://127.0.0.1:<port>` (`main.ts:10634`) | Same |
| WebSocket | `ws://127.0.0.1:<port>/api/ws?token=<token>` (`main.ts:10236`) | Same |
| Readiness proof | HTTP health wait **and** a WebSocket probe before declaring ready (`main.ts:10234-10240`) | Same two-leg check. A passing HTTP probe with a failing WS leg is the classic false positive |
| Shutdown | POSIX: signal the whole process group, `process.kill(-pid, 'SIGTERM')`, fall back to the direct child (`apps/desktop/electron/backend-child.ts:58`) | Same, via `libc::killpg`; child spawned in its own process group |
| Cold-start budget | 90s default, 45s floor (`backend-ready.ts:16`) | Same numbers |
| Restart storms | Latched failure state so retries do not respawn in a loop (`main.ts:10371-10384`) | Same: one latched error, cleared only by explicit user retry |

Deliberately **not** carried over in MVP: runtime bootstrap/install, legacy
`dashboard --no-open` fallback, update mutual-exclusion locking, orphan reaping
across app restarts, per-profile backend pool, remote resolution.

### 4.2 The bridge boundary (the anti-rot rule)

The single hardest-won lesson from the Electron app is that direct
`window.hermesDesktop` calls scattered through feature code make the native
surface impossible to evolve. The Tauri app therefore defines one interface:

```ts
// apps/tauri/src/bridge/types.ts
export interface DesktopBridge {
  connectBackend(): Promise<BackendConnection>
  backendStatus(): Promise<BackendStatus>
  backendLogs(limit?: number): Promise<string[]>
  retryBackend(): Promise<BackendConnection>
  onBackendProgress(cb: (p: BackendProgress) => void): () => void
}
```

Rules, enforced by review and by a lint-style test:

- Feature components and stores depend on `DesktopBridge` only.
- `window.__TAURI__` / `@tauri-apps/api` imports are allowed **only** inside
  `apps/tauri/src/bridge/`.
- Adding a native capability = one Rust module + one bridge method + one feature
  module. No shell surgery.

### 4.3 Reuse policy

| Reuse | Do | Do not |
| --- | --- | --- |
| `@hermes/shared` (`apps/shared/`) | Use `JsonRpcGatewayClient` verbatim — it already owns request ids, timeouts, abort, event fan-out, connect-timeout (`apps/shared/src/json-rpc-gateway.ts:95`) | Fork a second WebSocket client |
| Backend RPC contract | Call the same methods the Electron renderer calls | Invent new RPC methods |
| Electron renderer components | Port individual **pure** components later, deliberately, one at a time | Copy `apps/desktop/src` wholesale and prune |
| Design language | Follow the token/primitive discipline in `apps/desktop/DESIGN.md` (one button component, tokenized strokes, no card-in-card, real empty/error/loading states) | Ship a second ad-hoc design system, or generic AI-dashboard filler |

### 4.4 Backend RPC surface used by the MVP

All verified present in `tui_gateway/`:

| Purpose | Method | Source |
| --- | --- | --- |
| Create session | `session.create` (params: `cols`, `source`, `cwd`, `profile`, `model`, `provider`, `reasoning_effort`, `fast`) | `tui_gateway/methods_session.py:14` |
| Flat session list | `session.list` | `tui_gateway/methods_session.py:165` |
| Resume session | `session.resume` (`session_id`, `cols`, `source`) | `tui_gateway/methods_session.py:358` |
| Send a turn | `prompt.submit` (`session_id`, `text`) | `tui_gateway/methods_prompt.py:268` |
| Context usage | `session.usage` | `tui_gateway/methods_session.py:1537` |
| Project tree (grouped sidebar) | `projects.tree` (`preview_limit`, `profile`) | `tui_gateway/methods_config.py:117` |
| Sessions inside a project | `projects.project_sessions` (`project_id`) | `tui_gateway/methods_config.py:145` |
| Model catalog | `model.options` | `tui_gateway/methods_complete.py:469` |
| Model / effort / mode writes | `config.set` with `key` in `model`, `reasoning`, `interaction_mode` | `tui_gateway/server.py:11976`, mode branch at `:12351` |

Streaming events consumed (names from `apps/shared/src/json-rpc-gateway.ts:1`):
`gateway.ready`, `session.info`, `session.usage`, `message.start`,
`message.delta`, `message.complete`, `tool.start`, `tool.complete`, `error`.

Two contract facts that shape the UI:

- **PLAN / BUILD is session-scoped**, not global. `config.set` with
  `key: "interaction_mode"` accepts `build`, `plan`, or `toggle`, writes
  `session["interaction_mode"]`, mutates the live agent, and emits `session.info`
  (`tui_gateway/server.py:12351-12378`). The dropdown must therefore render from
  `session.info`, never from local optimistic state alone.
- **Context percentage is backend-reported.** `UsageStats` carries
  `context_used`, `context_max`, `context_percent`
  (`apps/desktop/src/types/hermes.ts:705`). The progress bar renders those
  numbers; it never computes its own estimate. It also must render empty space
  as visibly empty — the Ink status bar currently draws unfilled context with a
  solid connected rule (`ui-tui/src/components/appChrome.tsx:278`), which reads
  as "full" at 5%. Do not repeat that.

---

## 5. UI specification

Two references were supplied by the user:

- A composer mock (`/home/dolvin/Desktop/Desain tanpa judul.png`) for the input
  area shape.
- A DeepSeek-style desktop screenshot for the sidebar model: sessions grouped
  under project folders, relative timestamps, active row highlighted, Settings
  pinned at the bottom.

The Electron sidebar (profiles, connections, worktree lanes, kanban lanes, pins,
unread, cost sorts) is explicitly **too dense** for this MVP.

### 5.1 Layout

```
┌───────────────────┬──────────────────────────────────────────────────┐
│ + New Session     │                                                  │
│                   │   transcript (scroll, sticky-to-bottom)          │
│ ▸ paap            │                                                  │
│     hai      3min │                                                  │
│ ▾ ares-workspace  │                                                  │
│     setup    now  │                                                  │
│     hai     29min │                                                  │
│     test-…    3h  │                                                  │
│ ▸ (no folder)     │                                                  │
│                   ├──────────────────────────────────────────────────┤
│                   │  ┌────────────────────────────────────────────┐  │
│                   │  │ Message the agent                          │  │
│                   │  ├────────────────────────────────────────────┤  │
│ ⚙ Settings        │  │ model ▾  effort ▾  [███░░░░] 34%   PLAN ▾ ⏎│  │
└───────────────────┴──┴────────────────────────────────────────────┴──┘
```

### 5.2 Sidebar

- Header: `+ New Session`.
- Body: one collapsible group per project, sourced from `projects.tree`.
  Group label = project label; a session with no project falls in the backend's
  `Home` bucket (`NO_PROJECT_ID = "__no_project__"`,
  `apps/desktop/src/app/chat/sidebar/projects/workspace-groups.ts:119`).
- Row: session title (or `Untitled`) + relative time from `last_active`.
- Active row is visually held; collapse state persists in `localStorage`.
- Footer: `Settings`, pinned bottom.
- Grouping is **read from the backend**, never recomputed in the renderer.
  `projects.tree` is authoritative (`tui_gateway/methods_config.py:117`).

### 5.3 Transcript

User and assistant turns, streamed. Tool calls render as one compact collapsed
row per call (`tool.start` → `tool.complete`), expandable. Reasoning, if
present, is a collapsed section. Markdown: code fences with a copy action,
lists, tables. No animation beyond a fade.

### 5.4 Composer

- Multiline input, `Enter` submits, `Shift+Enter` newline, `Esc` cancels an
  in-flight turn.
- Left controls: model dropdown (`model.options` → `config.set model`),
  effort dropdown (`config.set reasoning`).
- Middle: context bar rendered from `session.usage` / `session.info.usage`.
- Right: PLAN / BUILD dropdown (`config.set interaction_mode`) then send.
- While a turn runs, send becomes stop.

### 5.5 States (all real, none decorative)

| State | Requirement |
| --- | --- |
| Backend starting | Progress text naming the current phase, from Rust progress events |
| Backend failed | The actual error, the log tail, and a working Retry |
| Gateway reconnecting | Non-blocking banner; composer disabled with the reason shown |
| No sessions yet | Names the next action (`New Session`), not "No data" |
| Empty project group | Group renders with a zero count, not hidden silently |
| Turn error | The backend's error text, with the partial output preserved |

---

## 6. Logging

Per the project logging mandate:

- Rust: `tracing` + `tracing-appender` to `<HERMES_HOME>/logs/tauri-desktop.log`,
  mirroring the dependency set already proven in
  `apps/bootstrap-installer/src-tauri/Cargo.toml:48`.
- Log: spawn command line, resolved `HERMES_HOME`, chosen port, readiness phase
  transitions, WS state changes, RPC failures, child exit code and signal.
- Never log the session token, API keys, or prompt content.
- Renderer errors go through one error boundary and are forwarded to the Rust log
  via a bridge method.

## 7. Security

- Backend binds `127.0.0.1` only, with a per-run random token. Both properties
  are inherited from the backend contract, not invented here.
- Tauri CSP is explicit and narrow, extended from the precedent in
  `apps/bootstrap-installer/src-tauri/tauri.conf.json:30` to allow
  `connect-src` to the loopback HTTP/WS origin.
- No filesystem, shell, or dialog capability is enabled until a feature needs it.
- `.ares/` and `.trash/` are never bundled.

## 8. Verification

| Layer | Command |
| --- | --- |
| Rust | `cargo test` + `cargo clippy -- -D warnings` in `apps/tauri/src-tauri` |
| TypeScript | `npm run typecheck --workspace apps/tauri` |
| Renderer unit | `npm run test --workspace apps/tauri` (vitest) |
| Python (untouched, regression guard) | `HERMES_PYTHON=/mnt/hdd/venv/bin/python scripts/run_tests.sh tests/tui_gateway -q` |
| Manual | Launch, backend comes up, create a session, send a turn, stream a reply, switch model, switch PLAN/BUILD, watch context bar move, restart app and resume a session |

The MVP is "done" only when a real turn streams from a real backend in the
packaged Linux build. A screenshot of a mock is not the deliverable.

## 9. Risks

| Risk | Mitigation |
| --- | --- |
| `hermes` not on PATH in a GUI launch (the Electron login-shell PATH problem, `main.ts:10449`) | Resolve the binary explicitly; if not found, fail with a named error and a Settings field for the path |
| Cold Python start exceeds the wait | Keep the 90s budget and show phase progress so it does not look hung |
| Orphaned backend after an unclean exit | Process-group kill on exit; MVP accepts no cross-restart reaping and says so |
| Session identity confusion (stored id vs runtime id) — a recurring Electron bug class | Store both explicitly from `session.create` / `session.resume`, and route session-scoped RPCs by runtime id only |
| Scope creep back into Electron parity | Out-of-scope list in this PRD is binding; new capability needs its own PRD entry |

## 10. Open decisions

Resolved:

1. **Settings scope**: desktop-app preferences only. No Hermes backend
   configuration (no model defaults, no key management, no profile switching,
   no config.yaml writes). Theme selection, appearance, and a diagnostics
   section are the MVP surface. Backend settings stay in the CLI / existing
   Electron app.
2. **Profile selector**: not in MVP. The app uses the `default` profile.

Still open:

3. Which themes ship in MVP beyond the built-in dark? A light theme, or dark
   only with the switch present for later?

