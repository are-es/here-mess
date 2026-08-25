# PRD: Desktop Settings Expansion (Memory, Config, Model tabs)

## 1. Problem

The desktop Settings modal only covers desktop preferences (General,
Shortcuts, Diagnostics). Hermes backend state is unreachable from the app:
provider credentials, compression thresholds, auxiliary task models, and the
curated memory store all require editing `~/.hermes/config.yaml` /
`.env` / `memories/*.md` by hand.

## 2. Goal

Three new Settings tabs, one card per section, click-first (dropdowns and
toggles, never raw typed config paths):

1. **Model** — provider list from `model.options`; clicking a provider opens
   a modal card with credential fields matched to that provider's auth type.
2. **Config** — a hand-curated subset of backend settings exposed as
   dropdowns/toggles/inputs. Not a full config dump.
3. **Memory** — view the curated memory entries (`MEMORY.md` + `USER.md`),
   edit inline, add/remove entries.

## 3. Backend contract

### 3.1 Whitelisted `config.set` keys (new branch in server.py)

Routed through the existing `_write_config_key()`. Anything not in this
list still returns `unknown config key`.

| Key | Values |
| --- | --- |
| `compression.enabled` | bool |
| `compression.threshold` | float in [0.10, 0.95] |
| `compression.target_ratio` | float in [0.05, 0.60] |
| `compression.tail_mode` | `legacy` \| `lean` |
| `compression.protect_last_n` | int >= 0 |
| `compression.progress_notices` | bool |
| `auxiliary.<task>.provider` | string (slug or `auto`) |
| `auxiliary.<task>.model` | string |
| `auxiliary.<task>.base_url` | string |
| `auxiliary.<task>.api_key` | string (stored via secret path, see 3.4) |
| `memory.memory_char_limit` | int in [500, 40000] |
| `memory.user_char_limit` | int in [300, 20000] |

`<task>` whitelist: `vision`, `web_extract`, `compression`, `skills_hub`,
`approval`, `mcp`, `title_generation` (mirrors DEFAULT_CONFIG).

### 3.2 New RPC: `settings.snapshot`

Returns exactly the values the Config tab renders plus current model info:

```json
{
  "compression": {"enabled": true, "threshold": 0.50, "target_ratio": 0.20,
                   "tail_mode": "legacy", "protect_last_n": 20,
                   "progress_notices": false},
  "auxiliary": {"<task>": {"provider": "auto", "model": "", "base_url": "",
                             "has_api_key": false}},
  "memory": {"memory_char_limit": 2200, "user_char_limit": 1375},
  "model": {"model": "...", "provider": "..."}
}
```

API keys are NEVER returned; only `has_api_key` booleans.

### 3.3 New RPCs for Memory tab

Backed by `tools/memory_tool.py::load_on_disk_store()` (same lock, drift
detection, and char-limit enforcement as the agent's own writes):

- `memory.list` → `{ "entries": [{index, preview, chars}], "chars_used",
  "char_limit" }` per target (`memory` / `user`)
- `memory.write` → params `{target, action: add|replace|remove, content?,
  old_text?, new_content?}`; returns success/error from the store.

No direct file writes from Rust/renderer — all writes flow through the
store so backups and validation apply.

### 3.4 Model tab data sources (existing, no backend change)

- `model.options` (picker_hints=True) → providers with
  `authenticated`, `auth_type`, `key_env`
- `model.save_key` {slug, api_key} → saves via credential lifecycle
  (rotates stale mirrors), rejects oauth providers with a clear error
- `model.disconnect` {slug} → removes env + auth.json credentials
- OAuth providers (`auth_type` starting with `oauth_`): modal shows status
  badge + "configure via `hermes model` CLI" note. No device-flow in MVP.

## 4. Frontend

New files under `apps/tauri/src/`:

- `components/settings-model.tsx` — provider cards list; click →
  `provider-auth-modal.tsx` (api_key input + optional base_url field when
  the registry row carries `base_url_env_var`; oauth badge otherwise)
- `components/settings-config.tsx` — Compression card, Auxiliary cards
  (one per whitelisted task), Memory limits card. All controls are chips/
  dropdowns/number steppers wired to `config.set`.
- `components/settings-memory.tsx` — target tabs (Notes/User), entry
  cards with inline edit textarea, delete button, add form.
- `store/settings-backend.ts` — snapshot atom + fetch/save helpers.

Settings nav gains Model / Config / Memory entries below Shortcuts.

Design rules: token-only colors (no hardcoded hex), no emoji, no glass on
cards, hairline borders, one accent for active chip states, empty/loading/
error states per R-27.

## 5. Out of scope (MVP)

OAuth device-flow login from the desktop, arbitrary dotted-key editing,
config file raw editor, memory import/export, per-task extra_body JSON
editing.

## 6. Verification

- Python: `HERMES_PYTHON=/mnt/hdd/venv/bin/python scripts/run_tests.sh <path> -q`
- TS: `npm run typecheck --workspace apps/tauri && npm test --workspace apps/tauri && npm run build --workspace apps/tauri`
