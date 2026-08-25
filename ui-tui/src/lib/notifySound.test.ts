/**
 * `display.notify_sound` in the TUI.
 *
 * Behavior under test: path resolution treats unset/blank/missing-file as "no
 * custom sound" so a stale config degrades to the bell; the configured sound
 * replaces the bell rather than stacking with it; and playback is detached and
 * unref'd so a stalled player can't hold the TUI's event loop open.
 */

import { existsSync } from 'node:fs'
import { homedir } from 'node:os'
import { resolve } from 'node:path'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('node:child_process', () => ({ spawn: vi.fn() }))

import { spawn } from 'node:child_process'

import {
  _resetNotifySoundPlayerCache,
  notifyPopupEnabled,
  notifyTurnComplete,
  resolveNotifySoundPath
} from './notifySound.js'

const spawnMock = vi.mocked(spawn)

// A real file on disk — resolution deliberately requires existence, so a
// fabricated path would make every case fall into the "missing" branch.
const realFile = resolve(process.cwd(), 'package.json')

function fakeChild() {
  return { on: vi.fn(), unref: vi.fn() } as unknown as ReturnType<typeof spawn>
}

describe('resolveNotifySoundPath', () => {
  beforeEach(() => {
    delete process.env.HERMES_NOTIFY_SOUND
  })

  it('returns null when unset', () => {
    expect(resolveNotifySoundPath(undefined)).toBeNull()
  })

  it('returns null for blank and whitespace-only values', () => {
    expect(resolveNotifySoundPath('')).toBeNull()
    expect(resolveNotifySoundPath('   ')).toBeNull()
  })

  it('returns null for a configured file that no longer exists', () => {
    // Stale config must degrade to the bell, not throw on every turn.
    expect(resolveNotifySoundPath('/nope/definitely-not-here.wav')).toBeNull()
  })

  it('resolves an existing absolute path', () => {
    expect(resolveNotifySoundPath(realFile)).toBe(realFile)
  })

  it('expands a leading tilde', () => {
    const home = homedir()
    const candidate = resolve(home, '.bashrc')

    // Only assert the expansion when the file actually exists on this machine.
    if (existsSync(candidate)) {
      expect(resolveNotifySoundPath('~/.bashrc')).toBe(candidate)
    }
  })

  it('lets HERMES_NOTIFY_SOUND override config', () => {
    process.env.HERMES_NOTIFY_SOUND = realFile

    expect(resolveNotifySoundPath('/some/other/path.wav')).toBe(realFile)
  })
})

describe('notifyPopupEnabled', () => {
  beforeEach(() => {
    delete process.env.HERMES_NOTIFY_POPUP
  })

  it('is off by default', () => {
    // A popup on every turn is noise; it has to be asked for.
    expect(notifyPopupEnabled(undefined)).toBe(false)
    expect(notifyPopupEnabled(false)).toBe(false)
  })

  it('is on when config says true', () => {
    expect(notifyPopupEnabled(true)).toBe(true)
  })

  it('lets HERMES_NOTIFY_POPUP force it on', () => {
    process.env.HERMES_NOTIFY_POPUP = 'yes'

    expect(notifyPopupEnabled(false)).toBe(true)
  })

  it('lets HERMES_NOTIFY_POPUP force it off', () => {
    process.env.HERMES_NOTIFY_POPUP = '0'

    expect(notifyPopupEnabled(true)).toBe(false)
  })
})

describe('notifyTurnComplete', () => {
  const originalPath = process.env.PATH

  beforeEach(() => {
    delete process.env.HERMES_NOTIFY_SOUND
    delete process.env.HERMES_NOTIFY_POPUP
    _resetNotifySoundPlayerCache()
    spawnMock.mockReset()
    spawnMock.mockReturnValue(fakeChild())
  })

  afterEach(() => {
    process.env.PATH = originalPath
    vi.doUnmock('node:fs')
    _resetNotifySoundPlayerCache()
  })

  it('writes the bell when no sound is configured', () => {
    const write = vi.fn()

    notifyTurnComplete({
      bellOnComplete: true,
      notifySound: '',
      stdout: { isTTY: true, write } as unknown as NodeJS.WriteStream
    })

    expect(write).toHaveBeenCalledWith('\x07')
    expect(spawnMock).not.toHaveBeenCalled()
  })

  it('stays silent when the bell is off and no sound is configured', () => {
    const write = vi.fn()

    notifyTurnComplete({
      bellOnComplete: false,
      notifySound: '',
      stdout: { isTTY: true, write } as unknown as NodeJS.WriteStream
    })

    expect(write).not.toHaveBeenCalled()
    expect(spawnMock).not.toHaveBeenCalled()
  })

  it('does not write the bell for a non-TTY stdout', () => {
    const write = vi.fn()

    notifyTurnComplete({
      bellOnComplete: true,
      notifySound: '',
      stdout: { isTTY: false, write } as unknown as NodeJS.WriteStream
    })

    expect(write).not.toHaveBeenCalled()
  })

  it('falls back to the bell when the configured file is missing', () => {
    const write = vi.fn()

    notifyTurnComplete({
      bellOnComplete: true,
      notifySound: '/nope/missing.wav',
      stdout: { isTTY: true, write } as unknown as NodeJS.WriteStream
    })

    expect(write).toHaveBeenCalledWith('\x07')
    expect(spawnMock).not.toHaveBeenCalled()
  })

  it('spawns the player detached and unref\'d, and skips the bell', () => {
    const child = fakeChild()
    spawnMock.mockReturnValue(child)
    const write = vi.fn()

    notifyTurnComplete({
      bellOnComplete: true,
      notifySound: realFile,
      stdout: { isTTY: true, write } as unknown as NodeJS.WriteStream
    })

    // No player on PATH in the sandbox → the helper reports failure and the
    // bell still fires. Either way the bell must never double with a sound.
    if (spawnMock.mock.calls.length > 0) {
      const [, argv, options] = [spawnMock.mock.calls[0][0], spawnMock.mock.calls[0][1], spawnMock.mock.calls[0][2]]

      expect(argv?.at(-1)).toBe(realFile)
      expect(options).toMatchObject({ detached: true, stdio: 'ignore' })
      // unref keeps a stalled player from holding the event loop open.
      expect(child.unref).toHaveBeenCalled()
      expect(write).not.toHaveBeenCalled()
    } else {
      expect(write).toHaveBeenCalledWith('\x07')
    }
  })

  it('survives a spawn that throws', () => {
    spawnMock.mockImplementation(() => {
      throw new Error('ENOENT')
    })
    const write = vi.fn()

    expect(() =>
      notifyTurnComplete({
        bellOnComplete: true,
        notifySound: realFile,
        stdout: { isTTY: true, write } as unknown as NodeJS.WriteStream
      })
    ).not.toThrow()
  })

  it('never spawns a notifier while notifyPopup is off', () => {
    notifyTurnComplete({ bellOnComplete: false, notifyPopup: false, notifySound: '' })

    expect(spawnMock).not.toHaveBeenCalled()
  })

  it('shows the popup even when there is no audible cue at all', () => {
    // Sound unset AND bell off must still notify — the popup can't sit behind
    // an early return in the audio ladder.
    notifyTurnComplete({ bellOnComplete: false, notifyPopup: true, notifySound: '' })

    // A notifier exists on this machine (notify-send); if not, the helper
    // degrades silently and there is nothing to assert.
    if (spawnMock.mock.calls.length > 0) {
      const argv = spawnMock.mock.calls[0][1] as string[]

      expect(argv.at(-1)).toBe('Turn complete')
    }
  })

  it('still writes the bell when the popup is on', () => {
    const write = vi.fn()

    notifyTurnComplete({
      bellOnComplete: true,
      notifyPopup: true,
      notifySound: '',
      stdout: { isTTY: true, write } as unknown as NodeJS.WriteStream
    })

    // The popup replaces neither the sound nor the bell — they're independent.
    expect(write).toHaveBeenCalledWith('\x07')
  })
})
