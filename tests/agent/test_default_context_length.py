import pytest
from agent.model_metadata import get_model_context_length
from hermes_cli.config import get_custom_provider_context_length


def test_custom_provider_level_default_context():
    custom_provs = [
        {
            "name": "my-proxy",
            "base_url": "http://localhost:9090/v1",
            "default_context_length": 1_000_000,
            "models": {
                "special-small": {"context_length": 32_000}
            }
        }
    ]
    # Specific model gets its own
    assert get_custom_provider_context_length("special-small", "http://localhost:9090/v1", custom_provs) == 32_000
    # Unlisted model inherits provider-level default
    assert get_custom_provider_context_length("any-other-model", "http://localhost:9090/v1", custom_provs) == 1_000_000


def test_global_agent_default_context_fallback(monkeypatch):
    from hermes_cli import config as config_mod
    monkeypatch.setattr(
        config_mod,
        "load_config_readonly",
        lambda: {"agent": {"default_context_length": 1_000_000}}
    )
    # Unknown model with no metadata gets the global default
    res = get_model_context_length("completely-unknown-custom-model-xyz", base_url="http://unknown:1234/v1")
    assert res == 1_000_000
