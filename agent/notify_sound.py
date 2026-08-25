"""Turn-completion notification, shared by every Hermes surface.

Two knobs, both under ``display``:

* ``notify_sound`` — path to an audio file. Set it and every surface plays it
  when a turn finishes; empty falls back to the terminal bell
  (``display.bell_on_complete``) exactly as before.
* ``notify_popup`` — opt-in OS desktop notification on the same event. Off by
  default: a popup on every turn is noise when the user is already watching the
  terminal, so it has to be asked for.

The two are independent. Sound with no popup, popup with no sound, both, or
neither — the surfaces read each key on its own.

Why a module instead of inlining ``subprocess.Popen`` at each call site: three
surfaces need this (classic CLI, the TUI's Python gateway, and any headless
caller), both probes are platform-dependent, and neither may block the surface
that just finished a turn. Keeping it here means one resolver, one player
ladder, one notifier ladder, one fire-and-forget contract.

Design notes:

* **Non-blocking by contract.** Both helpers spawn a detached child and return
  immediately. A stalled audio device or a hung notification daemon can never
  wedge the UI thread.
* **No new dependency.** Playback goes through whichever system player exists
  (``paplay``/``pw-play``/``aplay``/``ffplay``/``afplay``/PowerShell) and
  popups through whichever notifier exists (``notify-send``,
  ``terminal-notifier``/``osascript``, PowerShell), each probed once per
  process. ``sounddevice`` is deliberately not used: importing it triggers a
  macOS TCC permission prompt (see ``tools/voice_mode.py``) and pulls numpy
  into surfaces that don't otherwise need it.
* **Silent on failure.** A missing file, absent player, or absent notifier
  degrades (to the bell, or to nothing) and logs at debug. A notification cue
  must never raise into the turn-completion path.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Optional

logger = logging.getLogger(__name__)

__all__ = [
    "notify_popup",
    "notify_popup_enabled",
    "notify_sound",
    "notify_sound_path",
    "notify_turn_complete",
    "resolve_notify_sound_path",
]

# Cached argv templates, resolved on first use. ``None`` means "not probed
# yet"; an empty list means "probed, nothing available".
_player: Optional[list[str]] = None
_notifier: Optional[list[str]] = None

# What the OS popup says. Kept here so every surface reports turn completion
# identically instead of each inventing its own wording.
POPUP_TITLE = "Hermes"
POPUP_BODY = "Turn complete"


def _config_display(config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Return the ``display`` config section, or ``{}`` when unreadable."""
    if config is None:
        try:
            from hermes_cli.config import load_config_readonly

            config = load_config_readonly()
        except Exception:
            return {}
    display = (config or {}).get("display") if isinstance(config, dict) else None

    return display if isinstance(display, dict) else {}


def resolve_notify_sound_path(config: Optional[dict[str, Any]] = None) -> Optional[str]:
    """Absolute path from ``display.notify_sound``, or ``None``.

    ``None`` covers every "no custom sound" case: key unset, blank, or the
    configured file does not exist. Callers treat ``None`` as "fall back to the
    terminal bell" rather than an error — a stale path in config must not turn
    every finished turn into a warning.

    ``HERMES_NOTIFY_SOUND`` overrides config (handy for a one-off run or a
    test), and ``~`` / ``$VARS`` expand in both.
    """
    raw = os.environ.get("HERMES_NOTIFY_SOUND")
    if raw is None:
        value = _config_display(config).get("notify_sound")
        raw = value if isinstance(value, str) else ""
    raw = (raw or "").strip()
    if not raw:
        return None

    path = os.path.abspath(os.path.expanduser(os.path.expandvars(raw)))
    if not os.path.isfile(path):
        logger.debug("notify_sound: configured file not found: %s", path)
        return None

    return path


# Backwards-friendly short alias for call sites that read better without the
# ``resolve_`` prefix.
notify_sound_path = resolve_notify_sound_path


def notify_popup_enabled(config: Optional[dict[str, Any]] = None) -> bool:
    """True when ``display.notify_popup`` asks for an OS desktop notification.

    Off by default — a popup on every finished turn is noise when the user is
    already looking at the terminal. ``HERMES_NOTIFY_POPUP`` overrides config
    for a single run (``1``/``true``/``yes``/``on`` enable it).
    """
    raw = os.environ.get("HERMES_NOTIFY_POPUP")
    if raw is None:
        value = _config_display(config).get("notify_popup")
        if isinstance(value, bool):
            return value
        raw = value if isinstance(value, str) else ""

    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _probe_notifier() -> list[str]:
    """First available desktop-notification command as an argv prefix, or ``[]``.

    Each entry is a prefix; ``_notify_argv`` appends the title/body in whatever
    shape that tool expects, since none of them agree. Linux has one universal
    answer (``notify-send``, part of libnotify, present on every freedesktop
    desktop). macOS prefers ``terminal-notifier`` when installed because
    ``osascript`` notifications are attributed to Script Editor, but osascript
    always exists so it is the guaranteed floor.
    """
    system = platform.system()

    if system == "Darwin":
        if shutil.which("terminal-notifier"):
            return ["terminal-notifier"]

        return ["osascript", "-e"] if shutil.which("osascript") else []

    if system == "Windows":
        return _powershell_player("powershell.exe") or _powershell_player("powershell")

    if shutil.which("notify-send"):
        return ["notify-send"]

    # WSL2 has no notification daemon of its own; borrow the Windows host's.
    if system == "Linux" and _is_wsl2():
        return _powershell_player("powershell.exe")

    return []


def _notify_argv(notifier: list[str], title: str, body: str) -> list[str]:
    """Full argv for ``notifier`` showing ``title``/``body``.

    Every backend wants a different shape, so the translation lives in one
    place rather than smeared across the probe.
    """
    head = notifier[0].lower()

    if head.startswith("powershell"):
        # BurntToast isn't installed by default, so use the Windows Forms
        # balloon tip — available on every Windows box with .NET, no module
        # install. Doubled single quotes are PowerShell's literal escape.
        safe_title = title.replace("'", "''")
        safe_body = body.replace("'", "''")
        script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Information; "
            "$n.Visible = $true; "
            f"$n.ShowBalloonTip(5000, '{safe_title}', '{safe_body}', "
            "[System.Windows.Forms.ToolTipIcon]::Info); "
            "Start-Sleep -Seconds 6; $n.Dispose()"
        )
        return [*notifier, script]

    if head == "osascript":
        # AppleScript string literals escape with a backslash, not a doubled
        # quote — using the PowerShell rule here would break the script.
        safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
        safe_body = body.replace("\\", "\\\\").replace('"', '\\"')
        return [*notifier, f'display notification "{safe_body}" with title "{safe_title}"']

    if head == "terminal-notifier":
        return [*notifier, "-title", title, "-message", body]

    # notify-send. `-a` sets the app name so the popup is attributed to Hermes,
    # and `low` urgency keeps it from interrupting fullscreen/do-not-disturb.
    return [*notifier, "-a", POPUP_TITLE, "-u", "low", title, body]


def notify_popup(
    config: Optional[dict[str, Any]] = None,
    *,
    title: str = POPUP_TITLE,
    body: str = POPUP_BODY,
) -> bool:
    """Show the OS desktop notification. Returns True if a notifier started.

    Fire-and-forget on the same contract as ``notify_sound``: detached child,
    streams discarded, never waited on. ``False`` means nothing was shown
    (``display.notify_popup`` off, or no notifier available).
    """
    if not notify_popup_enabled(config):
        return False

    global _notifier
    if _notifier is None:
        _notifier = _probe_notifier()
        if not _notifier:
            logger.debug("notify_popup: no desktop notification command available")
    if not _notifier:
        return False

    return _spawn_detached(_notify_argv(_notifier, title, body), what="notify_popup")


def _spawn_detached(argv: list[str], *, what: str) -> bool:
    """Launch ``argv`` without waiting on it. False when the spawn failed.

    Shared by the sound and popup paths: both must survive a Ctrl+C aimed at
    the agent, must not print into the user's terminal, and must never be
    waited on — a hung audio device or notification daemon would otherwise
    stall the turn-completion path.
    """
    try:
        kwargs: dict[str, Any] = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if platform.system() == "Windows":
            # Detach from the console so the child doesn't flash a window or
            # inherit Ctrl+C aimed at the agent.
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
                subprocess, "DETACHED_PROCESS", 0
            )
        else:
            # New session: a Ctrl+C in the terminal must not kill the cue, and
            # the cue must not hold the terminal's process group open.
            kwargs["start_new_session"] = True
        subprocess.Popen(argv, **kwargs)  # noqa: S603 — argv list, no shell
    except (OSError, ValueError) as e:
        logger.debug("%s: spawn failed (%s): %s", what, argv[0], e)
        return False

    return True



def _is_wsl2() -> bool:
    try:
        with open("/proc/version", encoding="utf-8", errors="replace") as fh:
            return "microsoft" in fh.read().lower()
    except OSError:
        return False


def _probe_player() -> list[str]:
    """First available system audio player as an argv prefix, or ``[]``.

    Order is deliberate: on Linux the PulseAudio/PipeWire clients handle
    modern desktop audio routing (and mp3/ogg via their own decoders), ALSA's
    ``aplay`` is WAV-only so it sits below them, and ``ffplay`` is last
    because it is the heaviest process to spawn. macOS has exactly one right
    answer. WSL2 without a Linux audio bridge borrows the Windows host's
    player.
    """
    system = platform.system()

    if system == "Darwin":
        return ["afplay"] if shutil.which("afplay") else []

    if system == "Windows":
        return _powershell_player("powershell.exe") or _powershell_player("powershell")

    candidates = ("paplay", "pw-play", "aplay", "ffplay")
    for name in candidates:
        if not shutil.which(name):
            continue
        if name == "ffplay":
            return [name, "-nodisp", "-autoexit", "-loglevel", "quiet"]
        return [name]

    # WSL2 with no Linux-side audio: hand the file to the Windows host. The
    # path must be translated, so this is handled in _play_argv, not here.
    if system == "Linux" and _is_wsl2():
        return _powershell_player("powershell.exe")

    return []


def _powershell_player(binary: str) -> list[str]:
    return [binary, "-NoProfile", "-Command"] if shutil.which(binary) else []


def _play_argv(player: list[str], path: str) -> list[str]:
    """Full argv for ``player`` playing ``path``.

    PowerShell needs the file interpolated into a script rather than appended
    as an argument, and under WSL the Linux path has to be translated to its
    Windows form first. Everything else takes the path as a trailing argument.
    """
    if player and player[0].lower().startswith("powershell"):
        win_path = path
        if platform.system() == "Linux" and shutil.which("wslpath"):
            try:
                win_path = subprocess.run(
                    ["wslpath", "-w", path],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True,
                ).stdout.strip() or path
            except (OSError, subprocess.SubprocessError):
                pass
        # Single-quote escaping for PowerShell string literals is a doubled
        # quote — this keeps a path with an apostrophe from breaking the script.
        escaped = win_path.replace("'", "''")
        return [*player, f"(New-Object Media.SoundPlayer '{escaped}').PlaySync()"]

    return [*player, path]


def notify_sound(config: Optional[dict[str, Any]] = None) -> bool:
    """Play the configured completion sound. Returns True if a player started.

    Fire-and-forget: the child is spawned detached with its streams sent to
    devnull and is never waited on, so a slow or hung audio device cannot
    block the caller. ``False`` means nothing was played (no path configured,
    file missing, or no system player found) and the caller should fall back
    to the terminal bell.
    """
    path = resolve_notify_sound_path(config)
    if not path:
        return False

    global _player
    if _player is None:
        _player = _probe_player()
        if not _player:
            logger.debug("notify_sound: no system audio player available")
    if not _player:
        return False

    argv = _play_argv(_player, path)

    return _spawn_detached(argv, what="notify_sound")


def notify_turn_complete(
    config: Optional[dict[str, Any]] = None,
    *,
    bell: bool = False,
    stream: Any = None,
) -> bool:
    """Signal turn completion: sound (or bell) plus an optional OS popup.

    ``bell`` is the surface's ``display.bell_on_complete`` state. A configured
    sound replaces the bell rather than stacking with it — a user who set a
    sound asked for that sound, not for both. The popup is orthogonal: it is
    driven only by ``display.notify_popup``, so audio and visual cues can be
    enabled independently.

    Returns True if any cue was emitted.
    """
    # Popup first: it must fire even when there is no audible cue at all
    # (sound unset AND bell off), so it can't sit behind an early return.
    shown = notify_popup(config)

    if notify_sound(config):
        return True

    if not bell:
        return shown

    out = stream if stream is not None else sys.stdout
    try:
        out.write("\a")
        out.flush()
    except Exception:
        return shown

    return True


def _reset_probe_cache_for_tests() -> None:
    """Clear the memoized player and notifier probes. Tests only."""
    global _notifier, _player
    _player = None
    _notifier = None


# Kept under the old name so existing tests/callers keep working.
_reset_player_cache_for_tests = _reset_probe_cache_for_tests
