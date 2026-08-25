# Roadmap: Read-Before-Write Enforcement

## Milestones
- [ ] Task 001: Blocking staleness guard
- [ ] Task 002: Wire into write_file_tool + patch_tool with overwrite opt-out
- [ ] Task 003: Config kill-switch + tests

---

### Task 001: Blocking staleness guard
- **Goal**: Add `_check_read_before_write(path, task_id) -> str | None` in
  `tools/file_tools.py`, next to `_check_file_staleness`. Same resolution,
  same tracker, but returns a blocking error string instead of a notice.
- **Acceptance Criteria**:
  - [ ] Existing file, no read stamp → block message naming `read_file`.
  - [ ] Read stamp present but mtime differs → re-read message.
  - [ ] File missing on disk → None (new-file create allowed).
  - [ ] Resolve/stat failure → None (downstream errors handle it).
  - [ ] No behavior change for `_check_file_staleness` (stays warn-only).
- **Technical Notes**:
  - Reuse `_resolve_path_for_task`, `_read_tracker`, `_read_tracker_lock`,
    `os.path.getmtime`. Do not duplicate tracker logic — read the stamp
    inside the same lock pattern as `_check_file_staleness` (file_tools.py:2112).
  - Keep mtime as freshness signal; no content hashing.

### Task 002: Wire into write_file_tool + patch_tool with overwrite opt-out
- **Goal**: Enforce the guard at both tool entry points; add explicit bypass.
- **Acceptance Criteria**:
  - [ ] `write_file_tool`: guard runs after sensitive/binary/protected/approval/
        cross-profile checks, BEFORE lock acquisition. Signature gains
        `overwrite: bool = False`.
  - [ ] `patch_tool` mode=replace: guard on the single target path. Signature
        gains `overwrite: bool = False`.
  - [ ] `patch_tool` mode=patch: guard per extracted V4A header path —
        `Add File:` exempt, `Update/Delete/Move` enforced (Move: check both
        endpoints). Uses the existing `_paths_to_check` / op-tagged lists from
        the traversal-scan loop (~line 2362–2380); extend that loop to record
        ops so enforcement knows which paths are new vs existing.
  - [ ] Bypass (`overwrite=True`) skips the block but still attaches the
        staleness warning to `_warning`.
  - [ ] Handler wrappers `_handle_write_file` / `_handle_patch`
        (file_tools.py:2765, 2792) pass through the new arg and its schema
        entry is added wherever tool schemas are declared.
- **Technical Notes**:
  - Insert guard calls before `ExitStack` lock acquisition in patch_tool —
    fail fast, no lock churn for doomed calls.
  - Do not touch `terminal`, `execute_code`, or plugin write paths.
  - Update tool description strings ("must read before writing an existing
    file") so models learn the contract from the schema.

### Task 003: Config kill-switch + tests
- **Goal**: Configurable default + regression coverage.
- **Acceptance Criteria**:
  - [ ] `config.yaml` key `file_tools.require_read_before_write` (default true)
        gates all guard calls; false = current warn-only behavior.
  - [ ] Tests in `tests/tools/test_file_read_guards.py` (extend existing file):
        block-unread-existing, allow-new-file, allow-after-read, block-after-
        external-mtime-change, overwrite-bypass-warns, v4a-add-exempt,
        v4a-update-blocked, config-off-passes-through.
  - [ ] `HERMES_PYTHON=/mnt/hdd/venv/bin/python scripts/run_tests.sh tests/tools/test_file_read_guards.py -q` green.
  - [ ] `python3 -m py_compile tools/file_tools.py` clean.
- **Technical Notes**:
  - Config read via the same resolved-config helper already used in this file
    (`_get_hermes_config_resolved`), cached per-call is fine.
  - Tests must manipulate the real `_read_tracker` via public helpers
    (`_update_read_timestamp`) or fixture resets (`clear_file_ops_cache`),
    never by poking private dicts directly where avoidable.
