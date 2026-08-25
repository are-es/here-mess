# Roadmap: Desktop Settings Expansion (Memory, Config, Model tabs)

PRD: `.ares/settings_expansion/prd.md`

---

## Milestones

- [ ] Task 001: Fix model-dropdown label + provider slug mapping
- [ ] Task 002: Backend `config.set` whitelist + `settings.snapshot` RPC
- [ ] Task 003: Backend `memory.list` / `memory.write` RPCs
- [ ] Task 004: Frontend Model settings tab + auth modal
- [ ] Task 005: Frontend Config settings tab
- [ ] Task 006: Frontend Memory settings tab
- [ ] Task 007: Tests + full verification gate

---

### Task 001: Fix model-dropdown label + provider slug mapping

**Goal**: The composer pill always shows the real model name (never
"default" when a model is configured), and tier-1 provider rows key on the
payload's actual field names.

**Files**:
- Modify: `apps/tauri/src/components/model-dropdown.tsx`

**Acceptance Criteria**:
- [ ] Label reads `session.info.model`, falling back to the top-level
      `model` field returned by `model.options`, then "default"
- [ ] Provider groups map `p.slug ?? p.id`; count badge and tier-2 list
      still work for both shapes
- [ ] Current provider row shows an active marker using `res.provider`
- [ ] typecheck + vitest pass

**Technical Notes**: payload shape verified at
`hermes_cli/inventory.py:277` (`{"providers": [...], "model", "provider"}`);
rows carry `slug` not `id`.

---

### Task 002: Backend `config.set` whitelist + `settings.snapshot` RPC

**Goal**: Whitelisted dotted keys persist via `_write_config_key()`;
the Config tab reads one snapshot RPC.

**Files**:
- Modify: `tui_gateway/server.py` (`config.set`: new whitelisted branch
  before the final `unknown config key` error)
- Modify: `tui_gateway/methods_config.py` (new `settings.snapshot` handler)

**Acceptance Criteria**:
- [ ] `config.set {"key": "compression.threshold", "value": 0.6}` persists
      to config.yaml; float clamped to [0.10, 0.95]
- [ ] Booleans coerced; ints validated; unknown task/key rejected 4002
- [ ] `auxiliary.<task>.api_key` writes are stored but NEVER echoed in any
      response or log
- [ ] `settings.snapshot` returns the PRD §3.2 shape, `has_api_key`
      booleans only
- [ ] Existing keys (theme/density/model/...) unchanged

**Technical Notes**: whitelist as module-level frozenset pairs;
`(section, key)` validation before calling `_write_config_key`.
Register nothing extra — methods_config auto-registers via HandlerRegistry.

---

### Task 003: Backend `memory.list` / `memory.write` RPCs

**Goal**: Desktop reads and mutates the curated memory store safely.

**Files**:
- Create: `tui_gateway/methods_memory.py`
- Modify: `tui_gateway/server.py` (import + register)

**Acceptance Criteria**:
- [ ] `memory.list {}` → entries for both targets with previews, char
      counts, limits
- [ ] `memory.write {target:"user", action:"add", content:"..."}` appends
      through MemoryStore (lock + drift check apply)
- [ ] replace requires matching `old_text`; remove deletes entry
- [ ] Oversized content returns the store's char-limit error, no crash
- [ ] No secret scanning bypass: reuse store's own validation path

**Technical Notes**: build store per request with
`load_on_disk_store()` from `tools/memory_tool.py`. Handler pattern copies
methods_config.py (HandlerRegistry + register()).

---

### Task 004: Frontend Model settings tab + auth modal

**Goal**: Provider cards; click opens credential modal matched to auth type.

**Files**:
- Create: `apps/tauri/src/components/settings-model.tsx`
- Create: `apps/tauri/src/components/provider-auth-modal.tsx`
- Modify: `apps/tauri/src/components/settings.tsx` (nav + tab)
- Create: `apps/tauri/src/styles/settings-model.css`

**Acceptance Criteria**:
- [ ] Lists providers from `model.options` with authenticated status dot,
      model count, current marker
- [ ] api_key providers: modal has password input (+ base_url input when
      row carries base_url env var) → Save calls `model.save_key`,
      Disconnect calls `model.disconnect`
- [ ] oauth_* providers: modal shows auth-type badge and CLI hint text,
      no fake login button
- [ ] Loading / empty / gateway-closed states rendered
- [ ] Saved state refreshes the list without manual reload

---

### Task 005: Frontend Config settings tab

**Goal**: Curated backend settings as click-only controls, one card per
group.

**Files**:
- Create: `apps/tauri/src/components/settings-config.tsx`
- Create: `apps/tauri/src/store/settings-backend.ts`
- Modify: `apps/tauri/src/components/settings.tsx` (nav + tab)
- Create: `apps/tauri/src/styles/settings-config.css`

**Acceptance Criteria**:
- [ ] Compression card: enabled toggle-chip, threshold dropdown
      (0.3/0.4/0.5/0.6/0.7/0.75/0.8), target ratio dropdown, tail_mode
      chips, protect_last_n stepper
- [ ] Auxiliary cards (vision, web_extract, compression, skills_hub,
      approval, mcp, title_generation): provider dropdown, model input,
      base_url input, api_key password input (write-only, shows set/unset)
- [ ] Memory card: two number steppers for char limits
- [ ] Every change fires `config.set` immediately; failures show inline
      error text and revert control state
- [ ] Values load from `settings.snapshot`; gateway-closed disables all
      controls

---

### Task 006: Frontend Memory settings tab

**Goal**: Browse/edit curated memory with inline editing.

**Files**:
- Create: `apps/tauri/src/components/settings-memory.tsx`
- Modify: `apps/tauri/src/components/settings.tsx` (nav + tab)
- Create: `apps/tauri/src/styles/settings-memory.css`

**Acceptance Criteria**:
- [ ] Target switcher (Notes / User) renders each entry as its own card
      with char count vs limit meter
- [ ] Edit: click entry → textarea + Save/Cancel; Save calls
      `memory.write` replace with original text as old_text
- [ ] Delete button with confirm state (second click confirms)
- [ ] Add form at bottom (textarea), disabled over char limit with
      remaining-bytes hint
- [ ] Store errors surface verbatim (limit exceeded etc.)

---

### Task 007: Tests + full verification gate

**Goal**: All suites green.

**Files**:
- Create: `apps/tauri/src/components/settings-model.test.tsx`
- Create: `apps/tauri/src/components/settings-config.test.tsx`
- Create: `apps/tauri/src/components/settings-memory.test.tsx`
- Create: `tests/test_gateway_settings_rpc.py` (or extend existing suite)
- Modify: `apps/tauri/src/components/settings.test.tsx` (nav additions)

**Acceptance Criteria**:
- [ ] Vitest covers: tab rendering, config.set fire-on-change, memory
      add/edit/remove flows, modal auth-type branching
- [ ] Python tests cover: whitelist accepts/rejects, snapshot shape,
      memory.list/write round-trip on a temp HERMES_HOME
- [ ] `npm run typecheck && npm test && npm run build` pass
- [ ] Rust untouched; cargo suites unaffected
