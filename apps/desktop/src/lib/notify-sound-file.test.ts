/**
 * `display.notify_sound` on Desktop.
 *
 * Behavior under test: a configured file replaces the synthesized cue bank; an
 * unreadable path or a blocked autoplay falls back to it instead of going
 * silent; and the decoded data URL is cached per path so a finished turn never
 * re-reads the file over IPC.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

const readDesktopFileDataUrl = vi.fn()

vi.mock('@/lib/desktop-fs', () => ({ readDesktopFileDataUrl }))

import { __resetNotifySoundCache, playNotifySoundFile } from '@/lib/notify-sound-file'
import { $notifySoundPath, setNotifySoundPathFromConfig } from '@/store/notify-sound'

const DATA_URL = 'data:audio/wav;base64,UklGRg=='

/** Stub the Audio constructor; `play` resolves or rejects per the argument. */
function stubAudio(play: () => Promise<void>) {
  const created: string[] = []

  vi.stubGlobal(
    'Audio',
    class {
      constructor(src: string) {
        created.push(src)
      }

      play = play
    }
  )

  return created
}

describe('setNotifySoundPathFromConfig', () => {
  beforeEach(() => {
    $notifySoundPath.set('')
  })

  it('stores a configured string path', () => {
    setNotifySoundPathFromConfig('/sounds/done.wav')

    expect($notifySoundPath.get()).toBe('/sounds/done.wav')
  })

  it('trims surrounding whitespace', () => {
    setNotifySoundPathFromConfig('  /sounds/done.wav  ')

    expect($notifySoundPath.get()).toBe('/sounds/done.wav')
  })

  it('treats non-strings as unset', () => {
    // config.yaml is hand-edited; a number or null must not become a path.
    setNotifySoundPathFromConfig(42)
    expect($notifySoundPath.get()).toBe('')

    setNotifySoundPathFromConfig(null)
    expect($notifySoundPath.get()).toBe('')

    setNotifySoundPathFromConfig(undefined)
    expect($notifySoundPath.get()).toBe('')
  })
})

describe('playNotifySoundFile', () => {
  beforeEach(() => {
    __resetNotifySoundCache()
    $notifySoundPath.set('')
    readDesktopFileDataUrl.mockReset()
    vi.unstubAllGlobals()
  })

  it('reports false when no path is configured, without touching the filesystem', async () => {
    await expect(playNotifySoundFile()).resolves.toBe(false)
    expect(readDesktopFileDataUrl).not.toHaveBeenCalled()
  })

  it('treats a whitespace-only path as unset', async () => {
    $notifySoundPath.set('   ')

    await expect(playNotifySoundFile()).resolves.toBe(false)
    expect(readDesktopFileDataUrl).not.toHaveBeenCalled()
  })

  it('plays the decoded file and reports true', async () => {
    $notifySoundPath.set('/sounds/done.wav')
    readDesktopFileDataUrl.mockResolvedValue(DATA_URL)
    const created = stubAudio(() => Promise.resolve())

    await expect(playNotifySoundFile()).resolves.toBe(true)
    expect(created).toEqual([DATA_URL])
  })

  it('reports false when the file cannot be read', async () => {
    $notifySoundPath.set('/sounds/gone.wav')
    readDesktopFileDataUrl.mockRejectedValue(new Error('ENOENT'))

    await expect(playNotifySoundFile()).resolves.toBe(false)
  })

  it('reports false when the bridge returns an empty payload', async () => {
    $notifySoundPath.set('/sounds/done.wav')
    readDesktopFileDataUrl.mockResolvedValue('')

    await expect(playNotifySoundFile()).resolves.toBe(false)
  })

  it('reports false when autoplay policy rejects playback', async () => {
    $notifySoundPath.set('/sounds/done.wav')
    readDesktopFileDataUrl.mockResolvedValue(DATA_URL)
    stubAudio(() => Promise.reject(new Error('NotAllowedError')))

    // A blocked autoplay must let the caller fall back to the synthesized cue.
    await expect(playNotifySoundFile()).resolves.toBe(false)
  })

  it('reads the file once and reuses the decoded data URL', async () => {
    $notifySoundPath.set('/sounds/done.wav')
    readDesktopFileDataUrl.mockResolvedValue(DATA_URL)
    stubAudio(() => Promise.resolve())

    await playNotifySoundFile()
    await playNotifySoundFile()
    await playNotifySoundFile()

    expect(readDesktopFileDataUrl).toHaveBeenCalledTimes(1)
  })

  it('caches a failed read so a stale path stops hitting IPC every turn', async () => {
    $notifySoundPath.set('/sounds/gone.wav')
    readDesktopFileDataUrl.mockRejectedValue(new Error('ENOENT'))

    await playNotifySoundFile()
    await playNotifySoundFile()

    expect(readDesktopFileDataUrl).toHaveBeenCalledTimes(1)
  })

  it('reads again when the configured path changes', async () => {
    readDesktopFileDataUrl.mockResolvedValue(DATA_URL)
    stubAudio(() => Promise.resolve())

    $notifySoundPath.set('/sounds/one.wav')
    await playNotifySoundFile()

    $notifySoundPath.set('/sounds/two.wav')
    await playNotifySoundFile()

    expect(readDesktopFileDataUrl).toHaveBeenCalledTimes(2)
    expect(readDesktopFileDataUrl).toHaveBeenLastCalledWith('/sounds/two.wav')
  })
})
