# PRD: Read-Before-Write Enforcement

## Problem

Today the file tools only *warn* when the agent writes a file it never
read (`_check_file_staleness` returns a notice string). The write still
proceeds. Result: the agent can blind-overwrite a file with guessed
content, clobbering external edits or producing garbage diffs. Warnings
are ignorable noise; the model ignores them constantly.

## Goal

Hard-block destructive writes on files that were not inspected first:

1. **New file** (does not exist on disk): write allowed without prior read.
2. **Existing file, never read this session**: write/patch BLOCKED with an
   error telling the agent to `read_file` first.
3. **Read earlier, but file changed on disk since the read** (external edit,
   git pull, sibling agent): write/patch BLOCKED, re-read required.
4. **Read and unchanged**: proceed as today.

## Scope

### Where

Tool layer only — `tools/file_tools.py`:

- `write_file_tool` (full overwrite path)
- `patch_tool` mode=`replace` (targeted rewrite of existing content)
- `patch_tool` mode=`patch` (V4A):
  - `*** Add File:` targets → exempt (new file semantics)
  - `*** Update File:` / `*** Delete File:` / `*** Move File:` destinations
    on existing files → must have been read

Not enforced (documented limitation):

- `terminal` heredoc/echo redirections. Shell escapes exist by design;
  blocking them would break legit scripting. This is a guardrail against
  the *model's* lazy habits via its primary write tools, not a sandbox.
- `execute_code` / plugin file writes.

### Existing machinery to reuse

Everything needed is already there:

- `_read_tracker[task_id]["read_timestamps"][resolved_path]` — populated by
  `read_file_tool`, refreshed after every successful write via
  `_update_read_timestamp`. Per-task, lock-protected, capped.
- `_check_file_staleness()` (file_tools.py:2112) — already distinguishes
  "never read" vs "modified since read". Currently returns warning strings.
- `file_state.check_stale()` — cross-agent registry, separate concern,
  stays as-is.

### Design

Convert `_check_file_staleness` into a blocking variant:

```
_check_read_before_write(path, task_id) -> str | None   # error text or None
```

Rules inside:

- resolve fails / can't stat → allow (let downstream produce its own error)
- not `os.path.isfile(resolved)` → allow (new-file create)
- no read stamp AND file exists → BLOCK:
  `"Blocked: '<path>' exists but was never read this session. Call read_file(path) before writing."`
- read stamp present, current mtime != stored mtime → BLOCK:
  `"Blocked: '<path>' changed on disk since last read (external edit). Re-read before writing."`
- otherwise None.

Call sites insert one guard call right after the existing sensitive-path /
cross-profile checks (fail fast before acquiring locks).

Escape hatch:

- New optional arg `overwrite: bool = False` on `write_file_tool` and
  `patch_tool` — mirrors the existing `cross_profile` soft-guard pattern:
  default blocked, explicit opt-out after user direction. Response still
  attaches the staleness `_warning` so the bypass is visible in output.
- Config kill-switch in `config.yaml`:
  `file_tools.require_read_before_write: true|false` (default **true**).
  Read via `_get_hermes_config_resolved()` pattern already used in this file.

### Non-goals

- No content hashing (mtime is what the whole tracker already uses; keep
  one source of truth).
- No `.trash/` auto-snapshot here — separate feature, orthogonal.
- No changes to shell-layer `file_operations.py` — enforcement belongs at
  the tool boundary where intent ("I am editing X") is declared.

## Acceptance Criteria

- [ ] Writing an existing unread file errors with a read-first message.
- [ ] Creating a brand-new file works with zero reads.
- [ ] Editing a file after reading works silently (no extra noise).
- [ ] External mtime change between read and write blocks the write.
- [ ] V4A `Update/Delete/Move` on unread existing files blocked; `Add File`
      exempt.
- [ ] `overwrite=True` bypasses both block cases, keeps the warning.
- [ ] Config flag `false` restores current warn-only behavior.
- [ ] Consecutive edits by the same task do NOT false-positive (timestamps
      refresh after each write — existing behavior).
