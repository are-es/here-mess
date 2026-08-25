# Hermes Desktop (moved)

This app lives in its own repository now:

    /mnt/hdd/ares-workspace/tauri-desktop

- `app/`   — Tauri 2 + React desktop shell
- `shared/` — local `@hermes/shared` package

Runtime still resolves the installed `hermes` binary from `~/.hermes/bin`,
`~/.local/bin`, or `PATH`, so the shell works with any Hermes Agent install.
Build outputs: `.deb` and `.AppImage` via `npm run dist`.

Kept out of this fork so `hermes update` (autostash of untracked files) can
never touch it again. The old copy in this directory was removed when the
standalone repo was created; nothing here is buildable anymore.
