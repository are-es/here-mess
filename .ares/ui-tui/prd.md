# PRD: TUI UX Polish, WhatsApp Bubble Chat Layout & Ares Skins

## 1. Executive Summary
This comprehensive upgrade refactors the Hermes visual identity and conversation presentation:
1. **Chat Bubble Layout (WhatsApp Style)**:
   - **User Prompts**: Right-aligned conversation bubble with background/border box.
   - **Ares Responses**: Left-aligned conversation bubble with header label `ares [HH:MM]` and distinct border styling.
   - **Reasoning / Thoughts**: Kept step-by-step per-action (default multi-step trail preserved) as clean, subdued, dark-gray text (`dim={true}`, `color={t.color.muted}`) with inline square forward spinner `▰▱▱▱` next to active `Thinking`.
2. **Dedicated Skins (`ares` default & `ares-pink`)**:
   - `ares.yaml` (Default): Ice blue / cyan primary accent paired with deep slate & subtle bronze highlights, incorporating custom `banner_logo` & `banner_hero` from `xxxx.yaml`.
   - `ares-pink.yaml`: Sakura / cyberpunk pink palette paired with lavender and dark magenta contrasts.
3. **Core UX & Telemetry Improvements**:
   - `/restart` with exit code 43 automatic relaunch & session restore.
   - `Ctrl+E` direct model selection stage.
   - Compact stacked RGB slim context gauge (6-8 chars, multi-stop gradient `Green` → `Yellow` → `Red`, top fraction, side percentage).
   - Separator glyph `༄` across status bar and symmetrical CWD/Title background pills.

## 2. Problem Statement & User Value
- **Issue 1 (Chat Readability & Visual Flow)**: Standard terminal transcripts look flat and monotonic. Structuring user prompts on the right and agent responses on the left inside bounded containers (WhatsApp chat pattern) creates immediate conversational clarity.
- **Issue 2 (Ares Skin System)**: Users need branded, aesthetic skin options (`ares` default cyan/slate and `ares-pink` vibrant pinky) that include custom ASCII hero art and unique spinner wings.
- **Issue 3 (Reasoning Stream)**: Preserving the step-by-step reasoning trail per action while rendering it unboxed in darker gray typography with the live `▰▱▱▱` spinner inline.

## 3. Scope & Requirements
- **R1: WhatsApp-Style Bubble Chat**:
  - `User Prompt`: `alignSelf="flex-end"` container with `borderStyle="round"` (or subtle background pill).
  - `Ares Response`: `alignSelf="flex-start"` container with rounded border, header `ares [HH:MM]`.
  - `Reasoning / Thinking`: Unboxed, rendered as darker gray text (`color={t.color.muted}` dim) with `▰▱▱▱` spinner adjacent to the live thinking header, preserving native per-action segmentation.
- **R2: Custom Skins**:
  - `~/.hermes/skins/ares.yaml` (Default): Ice cyan (`#00f2fe`), dark slate (`#1e293b`), custom ASCII banner hero/logo.
  - `~/.hermes/skins/ares-pink.yaml`: Neon pink (`#ff70a6`), violet (`#70d6ff`), sakura magenta accents.
- **R3: Status Bar & Telemetry**:
  - `RgbSlimContextGauge` (top: `120k/1m`, bottom: gradient bar `━━━━━━┈┈┈┈` + `12%`).
  - Delimiter ` ༄ ` across status rule.
  - Responsive 2-line wrap on `cols < 80`.
  - Omit idle `ready` placeholder.
  - CWD & Session Title with background pills placed symmetrically (above prompt in bottom status bar mode; below in top mode).
- **R4: Navigation & Process Contracts**:
  - `Ctrl+E` opens model stage directly.
  - `/restart` exits with code 43 for clean auto-relaunch.

## 4. Architecture & Implementation Design
- `ui-tui/src/components/messageLine.tsx`: WhatsApp bubble layout with left/right flex alignments and header timestamp.
- `ui-tui/src/components/thinking.tsx`: Subdued dark gray reasoning without container box, inline `▰▱▱▱` spinner during live thought phases.
- `ui-tui/src/components/appChrome.tsx`: `RgbSlimContextGauge`, ` ༄ ` separator, 2-line responsive status rule.
- `ui-tui/src/components/appLayout.tsx`: Symmetrical background badges for CWD and Title.
- `~/.hermes/skins/ares.yaml` & `~/.hermes/skins/ares-pink.yaml`: Theme YAML definitions with banner art.
