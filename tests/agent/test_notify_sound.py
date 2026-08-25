"""Turn-completion notification sound (`display.notify_sound`).

Behavior under test:

* Path resolution: unset/blank/missing-file all mean "no custom sound", so a
  stale config path degrades to the bell instead of erroring every turn.
* Playback is fire-and-forget — the helper must never wait on the player, or a
  hung audio device would wedge the surface that just finished a turn.
* The sound REPLACES the bell rather than stacking with it.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from agent import notify_sound as ns


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Drop env overrides and the memoized probes between cases."""
    monkeypatch.delenv("HERMES_NOTIFY_SOUND", raising=False)
    monkeypatch.delenv("HERMES_NOTIFY_POPUP", raising=False)
    ns._reset_probe_cache_for_tests()
    yield
    ns._reset_probe_cache_for_tests()


@pytest.fixture
def sound(tmp_path: Path) -> Path:
    path = tmp_path / "done.wav"
    path.write_bytes(b"RIFF____WAVEfmt ")

    return path


class TestResolvePath:
    def test_unset_config_resolves_to_none(self):
        assert ns.resolve_notify_sound_path({"display": {}}) is None

    def test_blank_and_whitespace_resolve_to_none(self):
        assert ns.resolve_notify_sound_path({"display": {"notify_sound": ""}}) is None
        assert ns.resolve_notify_sound_path({"display": {"notify_sound": "   "}}) is None

    def test_missing_file_resolves_to_none(self, tmp_path: Path):
        # A stale path must degrade to the bell, not raise on every turn.
        stale = str(tmp_path / "deleted.wav")

        assert ns.resolve_notify_sound_path({"display": {"notify_sound": stale}}) is None

    def test_existing_file_resolves_absolute(self, sound: Path):
        resolved = ns.resolve_notify_sound_path({"display": {"notify_sound": str(sound)}})

        assert resolved == str(sound)
        assert os.path.isabs(resolved)

    def test_tilde_expands(self, monkeypatch, tmp_path: Path):
        monkeypatch.setenv("HOME", str(tmp_path))
        target = tmp_path / "cue.wav"
        target.write_bytes(b"x")

        assert ns.resolve_notify_sound_path({"display": {"notify_sound": "~/cue.wav"}}) == str(target)

    def test_env_var_expands(self, monkeypatch, sound: Path):
        monkeypatch.setenv("CUE_DIR", str(sound.parent))

        resolved = ns.resolve_notify_sound_path({"display": {"notify_sound": "$CUE_DIR/done.wav"}})

        assert resolved == str(sound)

    def test_env_override_wins_over_config(self, monkeypatch, sound: Path, tmp_path: Path):
        other = tmp_path / "other.wav"
        other.write_bytes(b"y")
        monkeypatch.setenv("HERMES_NOTIFY_SOUND", str(other))

        resolved = ns.resolve_notify_sound_path({"display": {"notify_sound": str(sound)}})

        assert resolved == str(other)

    def test_non_string_config_value_is_ignored(self):
        # config.yaml is user-edited; a bare number must not crash resolution.
        assert ns.resolve_notify_sound_path({"display": {"notify_sound": 42}}) is None


class TestPlayback:
    def test_no_path_configured_does_not_spawn(self, monkeypatch):
        calls: list = []
        monkeypatch.setattr(ns.subprocess, "Popen", lambda *a, **k: calls.append(a))

        assert ns.notify_sound({"display": {}}) is False
        assert calls == []

    def test_missing_player_reports_false(self, monkeypatch, sound: Path):
        monkeypatch.setattr(ns, "_probe_player", lambda: [])

        assert ns.notify_sound({"display": {"notify_sound": str(sound)}}) is False

    def test_spawns_player_with_path_as_last_arg(self, monkeypatch, sound: Path):
        spawned: list[list[str]] = []
        monkeypatch.setattr(ns, "_probe_player", lambda: ["paplay"])
        monkeypatch.setattr(ns.subprocess, "Popen", lambda argv, **k: spawned.append(argv))

        assert ns.notify_sound({"display": {"notify_sound": str(sound)}}) is True
        assert spawned == [["paplay", str(sound)]]

    def test_playback_is_fire_and_forget(self, monkeypatch, sound: Path):
        """The helper must not wait/communicate — a hung device can't block a turn."""

        class FakeProc:
            def __init__(self):
                self.waited = False

            def wait(self, *a, **k):
                self.waited = True
                raise AssertionError("notify_sound must not wait on the player")

            def communicate(self, *a, **k):
                raise AssertionError("notify_sound must not communicate with the player")

        proc = FakeProc()
        monkeypatch.setattr(ns, "_probe_player", lambda: ["paplay"])
        monkeypatch.setattr(ns.subprocess, "Popen", lambda argv, **k: proc)

        assert ns.notify_sound({"display": {"notify_sound": str(sound)}}) is True
        assert proc.waited is False

    def test_streams_are_discarded_and_session_detached(self, monkeypatch, sound: Path):
        """Player output must not pollute the terminal, and Ctrl+C must not kill it."""
        seen: dict = {}
        monkeypatch.setattr(ns, "_probe_player", lambda: ["paplay"])
        monkeypatch.setattr(ns.subprocess, "Popen", lambda argv, **k: seen.update(k))

        ns.notify_sound({"display": {"notify_sound": str(sound)}})

        assert seen["stdout"] == subprocess.DEVNULL
        assert seen["stderr"] == subprocess.DEVNULL
        assert seen["stdin"] == subprocess.DEVNULL
        assert seen["start_new_session"] is True

    def test_spawn_failure_reports_false(self, monkeypatch, sound: Path):
        def boom(*a, **k):
            raise OSError("no audio device")

        monkeypatch.setattr(ns, "_probe_player", lambda: ["paplay"])
        monkeypatch.setattr(ns.subprocess, "Popen", boom)

        assert ns.notify_sound({"display": {"notify_sound": str(sound)}}) is False

    def test_player_probe_is_memoized(self, monkeypatch, sound: Path):
        probes = []
        monkeypatch.setattr(ns, "_probe_player", lambda: probes.append(1) or ["paplay"])
        monkeypatch.setattr(ns.subprocess, "Popen", lambda argv, **k: None)

        cfg = {"display": {"notify_sound": str(sound)}}
        ns.notify_sound(cfg)
        ns.notify_sound(cfg)
        ns.notify_sound(cfg)

        assert len(probes) == 1


class TestPlayerLadder:
    def test_prefers_pulse_over_alsa(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Linux")
        monkeypatch.setattr(ns.shutil, "which", lambda name: name in {"paplay", "aplay"})

        assert ns._probe_player() == ["paplay"]

    def test_falls_back_to_alsa(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Linux")
        monkeypatch.setattr(ns.shutil, "which", lambda name: name == "aplay")

        assert ns._probe_player() == ["aplay"]

    def test_ffplay_runs_headless_and_quiet(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Linux")
        monkeypatch.setattr(ns.shutil, "which", lambda name: name == "ffplay")

        argv = ns._probe_player()

        # No window, exits on its own, no log spam into the user's terminal.
        assert "-nodisp" in argv and "-autoexit" in argv and "-loglevel" in argv

    def test_macos_uses_afplay(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Darwin")
        monkeypatch.setattr(ns.shutil, "which", lambda name: name == "afplay")

        assert ns._probe_player() == ["afplay"]

    def test_nothing_available_returns_empty(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Linux")
        monkeypatch.setattr(ns.shutil, "which", lambda name: False)
        monkeypatch.setattr(ns, "_is_wsl2", lambda: False)

        assert ns._probe_player() == []

    def test_powershell_escapes_quotes_in_path(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Windows")

        argv = ns._play_argv(["powershell.exe", "-NoProfile", "-Command"], r"C:\it's\cue.wav")

        # PowerShell literal escape is a doubled quote — a path with an
        # apostrophe must not break out of the string.
        assert "it''s" in argv[-1]


class TestPopupEnabled:
    def test_off_by_default(self):
        # A popup on every turn is noise; it has to be asked for.
        assert ns.notify_popup_enabled({"display": {}}) is False

    def test_boolean_true_enables(self):
        assert ns.notify_popup_enabled({"display": {"notify_popup": True}}) is True

    def test_boolean_false_disables(self):
        assert ns.notify_popup_enabled({"display": {"notify_popup": False}}) is False

    def test_truthy_strings_enable(self):
        # config.yaml is hand-edited; `notify_popup: "yes"` must not read as off.
        for value in ("1", "true", "TRUE", "yes", "on"):
            assert ns.notify_popup_enabled({"display": {"notify_popup": value}}) is True

    def test_other_strings_disable(self):
        for value in ("0", "false", "no", "off", "maybe", ""):
            assert ns.notify_popup_enabled({"display": {"notify_popup": value}}) is False

    def test_env_override_enables(self, monkeypatch):
        monkeypatch.setenv("HERMES_NOTIFY_POPUP", "1")

        assert ns.notify_popup_enabled({"display": {"notify_popup": False}}) is True

    def test_env_override_disables(self, monkeypatch):
        monkeypatch.setenv("HERMES_NOTIFY_POPUP", "0")

        assert ns.notify_popup_enabled({"display": {"notify_popup": True}}) is False


class TestPopupDispatch:
    def test_disabled_does_not_spawn(self, monkeypatch):
        calls: list = []
        monkeypatch.setattr(ns.subprocess, "Popen", lambda *a, **k: calls.append(a))

        assert ns.notify_popup({"display": {}}) is False
        assert calls == []

    def test_missing_notifier_reports_false(self, monkeypatch):
        monkeypatch.setattr(ns, "_probe_notifier", lambda: [])

        assert ns.notify_popup({"display": {"notify_popup": True}}) is False

    def test_notify_send_gets_title_and_body(self, monkeypatch):
        spawned: list[list[str]] = []
        monkeypatch.setattr(ns, "_probe_notifier", lambda: ["notify-send"])
        monkeypatch.setattr(ns.subprocess, "Popen", lambda argv, **k: spawned.append(argv))

        assert ns.notify_popup({"display": {"notify_popup": True}}) is True
        argv = spawned[0]
        assert argv[0] == "notify-send"
        assert argv[-2:] == [ns.POPUP_TITLE, ns.POPUP_BODY]

    def test_popup_is_fire_and_forget(self, monkeypatch):
        """A hung notification daemon must not stall turn completion."""

        class FakeProc:
            def wait(self, *a, **k):
                raise AssertionError("notify_popup must not wait on the notifier")

        monkeypatch.setattr(ns, "_probe_notifier", lambda: ["notify-send"])
        monkeypatch.setattr(ns.subprocess, "Popen", lambda argv, **k: FakeProc())

        assert ns.notify_popup({"display": {"notify_popup": True}}) is True

    def test_notifier_probe_is_memoized(self, monkeypatch):
        probes: list[int] = []
        monkeypatch.setattr(ns, "_probe_notifier", lambda: probes.append(1) or ["notify-send"])
        monkeypatch.setattr(ns.subprocess, "Popen", lambda argv, **k: None)

        cfg = {"display": {"notify_popup": True}}
        ns.notify_popup(cfg)
        ns.notify_popup(cfg)

        assert len(probes) == 1

    def test_spawn_failure_reports_false(self, monkeypatch):
        def boom(*a, **k):
            raise OSError("no dbus")

        monkeypatch.setattr(ns, "_probe_notifier", lambda: ["notify-send"])
        monkeypatch.setattr(ns.subprocess, "Popen", boom)

        assert ns.notify_popup({"display": {"notify_popup": True}}) is False


class TestNotifierLadder:
    def test_linux_uses_notify_send(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Linux")
        monkeypatch.setattr(ns.shutil, "which", lambda name: name == "notify-send")

        assert ns._probe_notifier() == ["notify-send"]

    def test_macos_prefers_terminal_notifier(self, monkeypatch):
        # osascript popups are attributed to Script Editor, so prefer the real tool.
        monkeypatch.setattr(ns.platform, "system", lambda: "Darwin")
        monkeypatch.setattr(ns.shutil, "which", lambda name: name in {"terminal-notifier", "osascript"})

        assert ns._probe_notifier() == ["terminal-notifier"]

    def test_macos_falls_back_to_osascript(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Darwin")
        monkeypatch.setattr(ns.shutil, "which", lambda name: name == "osascript")

        assert ns._probe_notifier() == ["osascript", "-e"]

    def test_nothing_available_returns_empty(self, monkeypatch):
        monkeypatch.setattr(ns.platform, "system", lambda: "Linux")
        monkeypatch.setattr(ns.shutil, "which", lambda name: False)
        monkeypatch.setattr(ns, "_is_wsl2", lambda: False)

        assert ns._probe_notifier() == []

    def test_osascript_escapes_double_quotes(self):
        # AppleScript escapes with a backslash; the PowerShell rule would break it.
        argv = ns._notify_argv(["osascript", "-e"], 'He said "hi"', "body")

        assert '\\"hi\\"' in argv[-1]

    def test_terminal_notifier_uses_flag_form(self):
        argv = ns._notify_argv(["terminal-notifier"], "T", "B")

        assert argv == ["terminal-notifier", "-title", "T", "-message", "B"]


class TestTurnCompleteFallback:
    @pytest.fixture(autouse=True)
    def _no_popup(self, monkeypatch):
        """Isolate the audio ladder — popup coverage lives below."""
        monkeypatch.setattr(ns, "notify_popup", lambda cfg=None: False)

    def test_sound_replaces_bell(self, monkeypatch):
        written: list[str] = []
        monkeypatch.setattr(ns, "notify_sound", lambda cfg=None: True)

        class Out:
            def write(self, text):
                written.append(text)

            def flush(self):
                pass

        assert ns.notify_turn_complete(bell=True, stream=Out()) is True
        assert written == []

    def test_bell_when_no_sound_configured(self, monkeypatch):
        written: list[str] = []
        monkeypatch.setattr(ns, "notify_sound", lambda cfg=None: False)

        class Out:
            def write(self, text):
                written.append(text)

            def flush(self):
                pass

        assert ns.notify_turn_complete(bell=True, stream=Out()) is True
        assert written == ["\a"]

    def test_silent_when_bell_off_and_no_sound(self, monkeypatch):
        monkeypatch.setattr(ns, "notify_sound", lambda cfg=None: False)

        assert ns.notify_turn_complete(bell=False) is False

    def test_unwritable_stream_does_not_raise(self, monkeypatch):
        monkeypatch.setattr(ns, "notify_sound", lambda cfg=None: False)

        class Broken:
            def write(self, text):
                raise OSError("closed pipe")

            def flush(self):
                pass

        # A closed stdout at shutdown must not crash the turn-completion path.
        assert ns.notify_turn_complete(bell=True, stream=Broken()) is False


class TestTurnCompleteWithPopup:
    """The popup is orthogonal to the audio cue, not gated behind it."""

    def test_popup_fires_alongside_the_sound(self, monkeypatch):
        calls: list[str] = []
        monkeypatch.setattr(ns, "notify_popup", lambda cfg=None: calls.append("popup") or True)
        monkeypatch.setattr(ns, "notify_sound", lambda cfg=None: calls.append("sound") or True)

        assert ns.notify_turn_complete(bell=False) is True
        assert calls == ["popup", "sound"]

    def test_popup_fires_with_no_audible_cue_at_all(self, monkeypatch):
        """Sound unset AND bell off must still show the popup (#early-return trap)."""
        monkeypatch.setattr(ns, "notify_popup", lambda cfg=None: True)
        monkeypatch.setattr(ns, "notify_sound", lambda cfg=None: False)

        assert ns.notify_turn_complete(bell=False) is True

    def test_popup_fires_alongside_the_bell(self, monkeypatch):
        written: list[str] = []
        monkeypatch.setattr(ns, "notify_popup", lambda cfg=None: True)
        monkeypatch.setattr(ns, "notify_sound", lambda cfg=None: False)

        class Out:
            def write(self, text):
                written.append(text)

            def flush(self):
                pass

        assert ns.notify_turn_complete(bell=True, stream=Out()) is True
        assert written == ["\a"]

    def test_popup_survives_an_unwritable_bell_stream(self, monkeypatch):
        monkeypatch.setattr(ns, "notify_popup", lambda cfg=None: True)
        monkeypatch.setattr(ns, "notify_sound", lambda cfg=None: False)

        class Broken:
            def write(self, text):
                raise OSError("closed pipe")

            def flush(self):
                pass

        # The popup already happened, so the result must not read as "no cue".
        assert ns.notify_turn_complete(bell=True, stream=Broken()) is True


class TestConfigDefault:
    def test_sound_default_is_empty_so_bell_behavior_is_unchanged(self):
        from hermes_cli.config_defaults import DEFAULT_CONFIG

        assert DEFAULT_CONFIG["display"]["notify_sound"] == ""

    def test_popup_default_is_off(self):
        from hermes_cli.config_defaults import DEFAULT_CONFIG

        assert DEFAULT_CONFIG["display"]["notify_popup"] is False
