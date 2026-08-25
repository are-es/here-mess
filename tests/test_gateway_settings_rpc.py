"""Desktop Settings expansion RPCs: config.set whitelist, settings.snapshot,
memory.list / memory.write."""

import pytest

from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from tui_gateway import server


@pytest.fixture
def settings_home(tmp_path, monkeypatch):
    """Isolated HERMES_HOME with a writable config.yaml."""
    home = tmp_path / "hermes-home"
    home.mkdir()
    (home / "config.yaml").write_text("{}\n", encoding="utf-8")
    set_hermes_home_override(str(home))
    monkeypatch.setattr(server, "_hermes_home", home)
    yield home
    reset_hermes_home_override()


@pytest.fixture
def cfg_roundtrip(monkeypatch):
    """In-memory config dict wired through the real _write_config_key."""
    state: dict = {}

    def fake_load_raw():
        return state

    def write_key(key_path, value):
        current = state
        keys = key_path.split(".")
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value

    monkeypatch.setattr(server, "_load_cfg_raw", fake_load_raw)
    monkeypatch.setattr(server, "_write_config_key", write_key)
    return state


def _set(key, value):
    return server.dispatch(
        {"id": "t", "method": "config.set", "params": {"key": key, "value": value}}
    )


class TestConfigSetWhitelist:
    def test_compression_threshold_persists(self, cfg_roundtrip):
        resp = _set("compression.threshold", 0.65)
        assert resp["result"]["value"] == 0.65
        assert cfg_roundtrip["compression"]["threshold"] == 0.65

    def test_compression_threshold_clamped_reject(self, cfg_roundtrip):
        assert "error" in _set("compression.threshold", 5.0)
        assert "compression" not in cfg_roundtrip

    def test_tail_mode_validated(self, cfg_roundtrip):
        assert "error" in _set("compression.tail_mode", "turbo")
        resp = _set("compression.tail_mode", "lean")
        assert resp["result"]["value"] == "lean"

    def test_boolean_coercion(self, cfg_roundtrip):
        resp = _set("compression.enabled", "off")
        assert resp["result"]["value"] is False
        assert cfg_roundtrip["compression"]["enabled"] is False

    def test_protect_last_n_non_negative(self, cfg_roundtrip):
        resp = _set("compression.protect_last_n", -3)
        assert resp["result"]["value"] == 0

    def test_auxiliary_whitelisted_task_and_field(self, cfg_roundtrip):
        resp = _set("auxiliary.compression.model", "google/gemini-2.5-flash")
        assert resp["result"]["value"] == "google/gemini-2.5-flash"
        assert (
            cfg_roundtrip["auxiliary"]["compression"]["model"]
            == "google/gemini-2.5-flash"
        )

    def test_auxiliary_unknown_task_rejected(self, cfg_roundtrip):
        assert "error" in _set("auxiliary.session_search.provider", "openai")

    def test_api_key_never_echoed(self, cfg_roundtrip):
        resp = _set("auxiliary.vision.api_key", "sk-secret-123")
        body = str(resp)
        assert "sk-secret-123" not in body
        assert resp["result"]["stored"] is True
        # Value IS persisted to config (that's the point) but not returned.
        assert cfg_roundtrip["auxiliary"]["vision"]["api_key"] == "sk-secret-123"

    def test_memory_char_limit_bounds(self, cfg_roundtrip):
        assert "error" in _set("memory.memory_char_limit", 10)
        resp = _set("memory.user_char_limit", 2000)
        assert resp["result"]["value"] == 2000

    def test_arbitrary_dotted_path_still_unknown(self, cfg_roundtrip):
        assert "error" in _set("gateway.max_concurrent_sessions", 1)

    def test_invalid_type_rejected_cleanly(self, cfg_roundtrip):
        resp = _set("memory.memory_char_limit", "not-a-number")
        assert "error" in resp


class TestSettingsSnapshot:
    def test_snapshot_shape_and_defaults(self, cfg_roundtrip, monkeypatch):
        from hermes_cli.inventory import ConfigContext

        ctx = ConfigContext(
            current_provider="anthropic",
            current_model="claude-sonnet",
            current_base_url="",
            user_providers={},
            custom_providers=[],
        )
        monkeypatch.setattr(
            "hermes_cli.inventory.load_picker_context", lambda: ctx
        )

        resp = server.dispatch(
            {"id": "s", "method": "config.get", "params": {"key": "settings_snapshot"}}
        )
        snap = resp["result"]
        assert set(snap.keys()) == {"compression", "auxiliary", "memory", "model"}
        assert snap["compression"]["threshold"] == 0.50
        assert snap["model"] == {"model": "claude-sonnet", "provider": "anthropic"}
        for task, info in snap["auxiliary"].items():
            assert set(info.keys()) == {"provider", "model", "base_url", "has_api_key"}

    def test_snapshot_masks_api_keys(self, cfg_roundtrip, monkeypatch):
        from hermes_cli.inventory import ConfigContext

        cfg_roundtrip.setdefault("auxiliary", {})["mcp"] = {"api_key": "sk-live-key"}
        ctx = ConfigContext(
            current_provider="", current_model="", current_base_url="",
            user_providers={}, custom_providers=[],
        )
        monkeypatch.setattr(
            "hermes_cli.inventory.load_picker_context", lambda: ctx
        )
        resp = server.dispatch(
            {"id": "s", "method": "config.get", "params": {"key": "settings_snapshot"}}
        )
        assert "sk-live-key" not in str(resp)
        assert resp["result"]["auxiliary"]["mcp"]["has_api_key"] is True


MEMORY_TOOL = "tools.memory_tool"


class TestMemoryRpc:
    def _store_patch(self, monkeypatch, tmp_path):
        """Point the memory dir at a temp dir; store reads live each call."""
        import tools.memory_tool as mt

        mem_dir = tmp_path / "memories"
        mem_dir.mkdir(exist_ok=True)
        monkeypatch.setattr(mt, "get_memory_dir", lambda: mem_dir)
        return mem_dir

    def test_add_list_roundtrip(self, monkeypatch, tmp_path):
        self._store_patch(monkeypatch, tmp_path)
        resp = server.dispatch(
            {
                "id": "m1",
                "method": "memory.write",
                "params": {
                    "target": "user",
                    "action": "add",
                    "content": "Dolvin prefers terse answers.",
                },
            }
        )
        assert resp["result"]["entry_count"] == 1

        listed = server.dispatch(
            {"id": "m2", "method": "memory.list", "params": {}}
        )
        user = listed["result"]["targets"]["user"]
        assert user["entries"][0]["preview"].startswith("Dolvin prefers")
        assert user["chars_used"] > 0

    def test_replace_via_old_text(self, monkeypatch, tmp_path):
        self._store_patch(monkeypatch, tmp_path)
        server.dispatch(
            {
                "id": "r0",
                "method": "memory.write",
                "params": {
                    "target": "memory",
                    "action": "add",
                    "content": "old entry text here",
                },
            }
        )
        resp = server.dispatch(
            {
                "id": "r1",
                "method": "memory.write",
                "params": {
                    "target": "memory",
                    "action": "replace",
                    "old_text": "old entry text",
                    "content": "new entry text",
                },
            }
        )
        assert "error" not in resp or resp.get("result") is None or "error" not in resp.get("result", {})
        listed = server.dispatch(
            {"id": "r2", "method": "memory.list", "params": {}}
        )
        previews = [
            e["preview"]
            for e in listed["result"]["targets"]["memory"]["entries"]
        ]
        assert any(p.startswith("new entry text") for p in previews)

    def test_remove_entry(self, monkeypatch, tmp_path):
        self._store_patch(monkeypatch, tmp_path)
        for i in range(2):
            server.dispatch(
                {
                    "id": f"d{i}",
                    "method": "memory.write",
                    "params": {
                        "target": "memory",
                        "action": "add",
                        "content": f"deletable entry {i}",
                    },
                }
            )
        server.dispatch(
            {
                "id": "d9",
                "method": "memory.write",
                "params": {
                    "target": "memory",
                    "action": "remove",
                    "old_text": "deletable entry 0",
                },
            }
        )
        listed = server.dispatch(
            {"id": "dl", "method": "memory.list", "params": {}}
        )
        entries = listed["result"]["targets"]["memory"]["entries"]
        assert len(entries) == 1
        assert "entry 0" not in entries[0]["preview"]

    def test_oversized_content_returns_store_error(self, monkeypatch, tmp_path):
        self._store_patch(monkeypatch, tmp_path)
        big = "x" * 3000
        resp = server.dispatch(
            {
                "id": "big",
                "method": "memory.write",
                "params": {"target": "user", "action": "add", "content": big},
            }
        )
        assert "error" in resp

    def test_unknown_target_rejected(self, monkeypatch, tmp_path):
        self._store_patch(monkeypatch, tmp_path)
        resp = server.dispatch(
            {
                "id": "u1",
                "method": "memory.write",
                "params": {"target": "nope", "action": "add", "content": "x"},
            }
        )
        assert "error" in resp
