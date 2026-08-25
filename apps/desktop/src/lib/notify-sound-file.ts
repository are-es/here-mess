/**
 * Custom turn-completion sound from `display.notify_sound`.
 *
 * When the user points that config key at an audio file, it REPLACES the
 * synthesized cue bank in `lib/completion-sound.ts` on every `message.complete`.
 * Empty (the default) leaves the built-in variants in charge, so nothing about
 * the existing sound design changes unless the user opts in.
 *
 * Why a data URL instead of `file://`: the renderer runs under a CSP that does
 * not grant it filesystem origin access, so `new Audio('file:///…')` is blocked.
 * The hardened Electron FS bridge (`readDesktopFileDataUrl`) is the same path
 * the composer uses for local images, and it works identically when the active
 * agent is remote.
 *
 * The decoded data URL is cached per path — re-reading and re-base64ing a sound
 * file on every finished turn would be pure waste, and the file is small enough
 * that one copy in memory is cheaper than the repeated IPC round trip.
 */

import { readDesktopFileDataUrl } from '@/lib/desktop-fs'
import { $notifySoundPath } from '@/store/notify-sound'

// path → data URL, or null when the read failed (missing/unreadable file).
// A failed read is cached too: without that, a stale config path would fire an
// IPC read on every single turn forever.
const cache = new Map<string, null | string>()

/** Test seam: drop the memoized data URLs. */
export function __resetNotifySoundCache(): void {
  cache.clear()
}

async function dataUrlFor(path: string): Promise<null | string> {
  const cached = cache.get(path)

  if (cached !== undefined) {
    return cached
  }

  try {
    const dataUrl = (await readDesktopFileDataUrl(path)) || null

    cache.set(path, dataUrl)

    return dataUrl
  } catch {
    cache.set(path, null)

    return null
  }
}

/**
 * Play the configured file. Resolves true when playback started, false when
 * there is no configured path, the file is unreadable, or the element refused
 * to play — the caller then falls back to the synthesized cue.
 */
export async function playNotifySoundFile(): Promise<boolean> {
  const path = $notifySoundPath.get().trim()

  if (!path) {
    return false
  }

  const dataUrl = await dataUrlFor(path)

  if (!dataUrl) {
    return false
  }

  try {
    const audio = new Audio(dataUrl)

    // Autoplay policy can reject until the window has seen a gesture; that is
    // a legitimate "no cue this time", not an error worth surfacing.
    await audio.play()

    return true
  } catch {
    return false
  }
}
