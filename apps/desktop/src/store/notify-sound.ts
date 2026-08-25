/**
 * `display.notify_sound` — path to a custom turn-completion sound.
 *
 * One config key shared by every Hermes surface. On Desktop a non-empty path
 * replaces the synthesized cue bank; empty keeps the built-in variants. Synced
 * from config on every `refreshHermesConfig`, so editing config.yaml takes
 * effect without restarting the app.
 *
 * Display-only: reading or setting it never touches model context, so it is
 * prompt-cache safe.
 */

import { atom } from 'nanostores'

export const $notifySoundPath = atom<string>('')

export function setNotifySoundPathFromConfig(value: unknown): void {
  $notifySoundPath.set(typeof value === 'string' ? value.trim() : '')
}
