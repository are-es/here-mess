# PRD: ARES Desktop Shell Complete Redesign, Shortcuts & Issue Inventory

## 1. Vision & Identity
Transform the ARES desktop shell into a world-class, high-craft developer terminal engine. Eliminate all AI slop (no decorative emoji, no generic purple gradients, no floating pills). Deliver a high-density, sharp, monochrome-base UI with precise micro-interactions, circular context meter, interactive command/skill launcher, and configurable keyboard shortcuts.

---

## 2. Issues & Changes Log

### Item 001: 2-Tier Hierarchical Model Picker
- **Status**: Recorded
- **Requirement**: Klik Model dropdown menampilkan daftar Provider dulu (Anthropic, OpenAI, OpenRouter, Nous, dll) dengan badge jumlah model. Klik salah satu Provider baru menampilkan daftar Model di bawah provider tersebut, lengkap dengan tombol `‹ Back`.

### Item 002: Context Meter Popover Viewport Clipping
- **Status**: Recorded
- **Requirement**: Ubah anchor `.context-popover` jadi `right: 0; left: auto;` dan batasi `max-width: min(320px, calc(100vw - 32px))` serta `max-height: calc(100vh - 120px)` supaya tidak terpotong saat ukuran window kecil/sempit.

### Item 003: Context Meter Progress Bar Active Refresh
- **Status**: Recorded
- **Requirement**: Proaktif memanggil RPC `session.usage` dan `session.context_breakdown` saat session aktif, di-resume, atau setelah selesai stream agar radial SVG gauge dan persentase langsung update secara real-time.

### Item 004: Global Keyboard Shortcuts (`Shift+Tab` & Rebinding)
- **Status**: Recorded
- **Requirement**: Intersepsi `Shift+Tab` pada capture phase dengan `stopPropagation` & `stopImmediatePropagation` agar tidak memicu focus-cycling tombol browser, serta dukung rebinding di tab Settings Shortcuts.

### Item 005: Collapsible Workspace Sidebar
- **Status**: Recorded
- **Requirement**: Tambah tombol toggle collapse di sidebar header / floating icon toggle saat collapsed, plus shortcut `Ctrl+B` (atau `Cmd+B`). Saat collapsed, lebar sidebar menyusut jadi strip icon ramping (atau sembunyi total) sehingga ruang chat & composer jadi lebih lega.

### Item 006: Workspace Path Display & Native Folder Picker on New Session
- **Status**: Recorded
- **Requirement**:
  1. Di dalam session aktif: Tampilkan active working directory path (misal `~/here-mess` atau `/mnt/hdd/...`) di bawah textbox composer secara ringkas & monospaced.
  2. Path bersifat fixed per-session.
  3. Ganti path dilakukan saat bikin New Session: Ada tombol/card `+ Open Folder / Browse` yang memicu native OS file manager dialog (Tauri folder picker). Folder yang dipilih otomatis menjadi `workdir` session baru tersebut dan terkelompok di project tree sidebar.

### Item 007: Full Keyboard Shortcut Suite Wiring & Verification
- **Status**: Recorded
- **Requirement**: Pastikan seluruh shortcut ter-wiring dan berfungsi nyata:
  - `Shift+Tab` / `Ctrl+M`: Toggle Mode (Plan / Build)
  - `Ctrl+P` / `Alt+M`: Quick Model Picker (langsung buka modal/dropdown provider & model)
  - `Ctrl+K`: Open Command & Skill Palette Popup
  - `Ctrl+N`: New Session (auto-focus atau open folder prompt)
  - `Ctrl+L`: Focus composer textarea
  - `Ctrl+B`: Toggle collapse sidebar
  - `Ctrl+,`: Buka Settings modal
  - `Escape`: Interrupt streaming / Dismiss popups / Clear slash query

### Item 008: Command & Skill Palette Popup Card with Sub-Navbar
- **Status**: Recorded
- **Requirement**:
  1. **Trigger**: Card / tombol `⚡ Actions / Commands` di sebelah kiri controls composer (atau shortcut `Ctrl+K` / typing `/`).
  2. **Popup Modal / Palette**:
     - Search input di bagian atas (auto-focus, instant filtering).
     - **Sub-Navbar Tabs**: `[ Commands ]` dan `[ Skills ]`.
     - **Tab Commands**: Menampilkan seluruh perintah CLI Hermes lengkap (`/new`, `/clear`, `/compress`, `/title`, `/fork`, `/undo`, `/save`, `/diff`, `/export`, `/reboot`, `/history`, `/stop`, `/yolo`, dll) beserta deskripsi singkat.
     - **Tab Skills**: Menampilkan seluruh katalog skills di `~/.hermes/skills/` (misal `cavpon`, `codemaps`, `ai-researcher`, `scrapling`, `impeccable`, `openhue`, `security`, `github-workflow`, dll) beserta kategori dan deskripsi.
  3. **Auto-Inject**: Klik pada item command atau skill akan otomatis meng-inject teks perintah tersebut ke dalam textarea composer dan memfokuskan kursor.
  4. **Keyboard Nav**: Arrow Up/Down navigasi, Tab switch tab/select, Enter auto-inject, Escape close.

---

## 3. Pending Incoming Problems
*(Siap mencatat masalah/perubahan berikutnya dari user)*
