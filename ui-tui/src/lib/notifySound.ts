/**
 * Turn-completion cues for the TUI: audio file and/or OS desktop notification.
 *
 * `display.notify_sound` names an audio file; when set it replaces the terminal
 * bell on `message.complete`. `display.notify_popup` independently asks for an
 * OS desktop notification on the same event. The TUI runs in Node (ink), so
 * both go through system commands the way the Python side does — there is no
 * WebAudio or Notification API here, and shelling out keeps the dependency list
 * untouched.
 *
 * Contract: fire-and-forget and never throw. A missing file, absent player,
 * absent notifier, or a stalled audio device must not delay the transcript or
 * wedge the event loop, so children are detached, unref'd, and their streams
 * discarded.
 */

import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { homedir, platform } from 'node:os'
import { isAbsolute, resolve } from 'node:path'

// Probed once per process. `undefined` = not probed, `null` = nothing found.
let cachedPlayer: null | string[] | undefined
let cachedNotifier: null | string[] | undefined

/** Linux/macOS player ladder. PulseAudio/PipeWire first (they handle mp3/ogg
 *  and modern routing), ALSA's WAV-only `aplay` next, ffplay last since it is
 *  the heaviest to spawn. */
const LINUX_PLAYERS: Array<[string, string[]]> = [
  ['paplay', []],
  ['pw-play', []],
  ['aplay', []],
  ['ffplay', ['-nodisp', '-autoexit', '-loglevel', 'quiet']]
]

/** What the popup says. Matches agent/notify_sound.py so every surface reports
 *  turn completion identically. */
const POPUP_TITLE = 'Hermes'
const POPUP_BODY = 'Turn complete'

const which = (bin: string): boolean => {
  const dirs = (process.env.PATH ?? '').split(platform() === 'win32' ? ';' : ':')

  return dirs.some(dir => dir && existsSync(resolve(dir, bin)))
}

const probePlayer = (): null | string[] => {
  if (platform() === 'darwin') {
    return which('afplay') ? ['afplay'] : null
  }

  if (platform() === 'win32') {
    return which('powershell.exe') ? ['powershell.exe', '-NoProfile', '-Command'] : null
  }

  for (const [bin, args] of LINUX_PLAYERS) {
    if (which(bin)) {
      return [bin, ...args]
    }
  }

  return null
}

/** Notifier ladder. macOS prefers terminal-notifier when present because
 *  osascript notifications are attributed to Script Editor, but osascript
 *  always exists so it is the guaranteed floor. Linux has one universal answer
 *  (notify-send, from libnotify). */
const probeNotifier = (): null | string[] => {
  if (platform() === 'darwin') {
    if (which('terminal-notifier')) {
      return ['terminal-notifier']
    }

    return which('osascript') ? ['osascript', '-e'] : null
  }

  if (platform() === 'win32') {
    return which('powershell.exe') ? ['powershell.exe', '-NoProfile', '-Command'] : null
  }

  return which('notify-send') ? ['notify-send'] : null
}

/**
 * Absolute path for a configured `notify_sound`, or null when there is nothing
 * playable. Returns null (not an error) for unset/blank/missing-file so a
 * stale config path degrades to the bell instead of logging on every turn.
 */
export const resolveNotifySoundPath = (configured?: string): null | string => {
  const raw = (process.env.HERMES_NOTIFY_SOUND ?? configured ?? '').trim()

  if (!raw) {
    return null
  }

  const expanded = raw.startsWith('~/') ? resolve(homedir(), raw.slice(2)) : raw
  const path = isAbsolute(expanded) ? expanded : resolve(expanded)

  return existsSync(path) ? path : null
}

/** Whether `display.notify_popup` (or the env override) asks for a popup. */
export const notifyPopupEnabled = (configured?: boolean): boolean => {
  const env = process.env.HERMES_NOTIFY_POPUP

  if (env !== undefined) {
    return ['1', 'true', 'yes', 'on'].includes(env.trim().toLowerCase())
  }

  return configured === true
}

/** Launch `argv` without waiting on it. False when the spawn failed. */
const spawnDetached = (bin: string, argv: string[]): boolean => {
  try {
    const child = spawn(bin, argv, { detached: true, stdio: 'ignore' })
    // Swallow spawn errors: an ENOENT here must not become an unhandled
    // 'error' event that crashes the TUI.
    child.on('error', () => {})
    child.unref()
  } catch {
    return false
  }

  return true
}

/** Play `path`. Returns false when no player is available. */
const play = (path: string): boolean => {
  if (cachedPlayer === undefined) {
    cachedPlayer = probePlayer()
  }

  if (!cachedPlayer) {
    return false
  }

  const [bin, ...args] = cachedPlayer
  // PowerShell needs the file interpolated into a script, not appended as an
  // argument. Doubling single quotes is PowerShell's literal escape, so a path
  // containing an apostrophe can't break out of the string.
  const argv = bin.toLowerCase().startsWith('powershell')
    ? [...args, `(New-Object Media.SoundPlayer '${path.replace(/'/g, "''")}').PlaySync()`]
    : [...args, path]

  return spawnDetached(bin, argv)
}

/** Show the OS desktop notification. Returns false when no notifier exists. */
const popup = (): boolean => {
  if (cachedNotifier === undefined) {
    cachedNotifier = probeNotifier()
  }

  if (!cachedNotifier) {
    return false
  }

  const [bin, ...args] = cachedNotifier
  const head = bin.toLowerCase()

  if (head.startsWith('powershell')) {
    // Windows Forms balloon tip — no module install needed, unlike BurntToast.
    const script =
      'Add-Type -AssemblyName System.Windows.Forms; ' +
      '$n = New-Object System.Windows.Forms.NotifyIcon; ' +
      '$n.Icon = [System.Drawing.SystemIcons]::Information; ' +
      '$n.Visible = $true; ' +
      `$n.ShowBalloonTip(5000, '${POPUP_TITLE}', '${POPUP_BODY}', ` +
      '[System.Windows.Forms.ToolTipIcon]::Info); ' +
      'Start-Sleep -Seconds 6; $n.Dispose()'

    return spawnDetached(bin, [...args, script])
  }

  if (head === 'osascript') {
    return spawnDetached(bin, [...args, `display notification "${POPUP_BODY}" with title "${POPUP_TITLE}"`])
  }

  if (head === 'terminal-notifier') {
    return spawnDetached(bin, [...args, '-title', POPUP_TITLE, '-message', POPUP_BODY])
  }

  // notify-send. `-a` attributes the popup to Hermes; `low` urgency keeps it
  // from interrupting fullscreen / do-not-disturb.
  return spawnDetached(bin, [...args, '-a', POPUP_TITLE, '-u', 'low', POPUP_TITLE, POPUP_BODY])
}

/**
 * Emit the turn-completion cues.
 *
 * Audio: the configured sound when playable, otherwise the terminal bell. The
 * sound REPLACES the bell — a user who configured a sound asked for that, not
 * for both. The popup is orthogonal and driven only by `notifyPopup`, so audio
 * and visual cues can be enabled independently.
 */
export const notifyTurnComplete = (opts: {
  bellOnComplete: boolean
  notifyPopup?: boolean
  notifySound?: string
  stdout?: NodeJS.WriteStream
}): void => {
  if (notifyPopupEnabled(opts.notifyPopup)) {
    popup()
  }

  const path = resolveNotifySoundPath(opts.notifySound)

  if (path && play(path)) {
    return
  }

  if (opts.bellOnComplete && opts.stdout?.isTTY) {
    opts.stdout.write('\x07')
  }
}

/** Test seam: clear the memoized player and notifier probes. */
export const _resetNotifySoundPlayerCache = (): void => {
  cachedPlayer = undefined
  cachedNotifier = undefined
}
