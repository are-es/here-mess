import pytest
from hermes_cli.alias_cmd import get_all_model_aliases, save_model_alias, delete_model_alias


def test_save_and_delete_model_alias(monkeypatch):
    mock_cfg = {"model_aliases": {}}

    from hermes_cli import alias_cmd
    monkeypatch.setattr(alias_cmd, "load_config", lambda: mock_cfg)
    monkeypatch.setattr(alias_cmd, "load_config_readonly", lambda: mock_cfg)
    monkeypatch.setattr("hermes_cli.config.save_config", lambda c: mock_cfg.update(c))

    # 1. Save alias
    save_model_alias("fast", model="google/gemini-2.5-flash", provider="custom", base_url="http://localhost:9090/v1")
    aliases = get_all_model_aliases()
    assert "fast" in aliases
    assert aliases["fast"]["model"] == "google/gemini-2.5-flash"
    assert aliases["fast"]["provider"] == "custom"

    # 2. Delete alias
    delete_model_alias("fast")
    aliases_after = get_all_model_aliases()
    assert "fast" not in aliases_after
